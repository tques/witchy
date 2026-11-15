"""Voxel model builder: shapes, painting helpers and house-style shading.

Coordinates: x = left->right (sprite columns), y = top->bottom (sprite rows),
z = back->front (larger z is closer to the viewer). The volume is stored as
[y][z][x] so each horizontal layer (fixed y) is one sprite-stack slice.
"""
import numpy as np
from scipy import ndimage as ndi
from . import style


def hexc(h):
    """'d4585f' -> (212, 88, 95)"""
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Model:
    def __init__(self, W=style.GRID_W, H=style.GRID_H, D=style.GRID_D):
        self.W, self.H, self.D = W, H, D
        self.zc = D / 2
        self.Y, self.Z, self.X = np.mgrid[0:H, 0:D, 0:W].astype(float)
        self.occ = np.zeros((H, D, W), bool)
        self.col = np.zeros((H, D, W, 3))
        self.part = np.zeros((H, D, W), np.int16)
        self.flat = np.zeros((H, D, W), bool)      # unlit (exact-colour) voxels, e.g. eyes
        self.parts = {}                             # name -> id
        self.smooth = []                            # smooth-shaded surfaces (brims etc.)
        self.glow_parts = []
        self.lift = 0                               # raise the whole model this many layers (walk bob)
        self.lean, self.lean_pivot = 0.0, H - 1     # forward lean: rows shift +z by lean * height above pivot

    # ---------------------------------------------------------------- parts
    def pid(self, name):
        if name not in self.parts:
            self.parts[name] = len(self.parts) + 1
        return self.parts[name]

    def is_part(self, name):
        return self.part == self.pid(name)

    def put(self, mask, color, part):
        """Fill empty voxels in mask. Earlier puts win, so add front/detail pieces first.
        Returns the voxels actually placed."""
        m = mask & ~self.occ
        self.occ |= m
        self.col[m] = color
        self.part[m] = self.pid(part)
        return m

    def carve(self, mask):
        self.occ[mask] = False
        self.part[mask] = 0

    # --------------------------------------------------------------- shapes
    def ell(self, cx, cy, cz, rx, ry, rz):
        X, Y, Z = self.X, self.Y, self.Z
        return ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2 <= 1

    def ell_oriented(self, c, radii, R):
        """Ellipsoid whose local axes are the columns of rotation R (for re-aimed rings, discs, gems)."""
        P = np.stack([self.X - c[0], self.Y - c[1], self.Z - c[2]], -1) @ np.asarray(R, float)
        return ((P / np.asarray(radii, float)) ** 2).sum(-1) <= 1

    def ball(self, c, r):
        return self.ell(c[0], c[1], c[2], r, r, r)

    def capsule(self, p0, p1, r):
        """Cylinder with rounded ends (limbs, staffs)."""
        X, Y, Z = self.X, self.Y, self.Z
        p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = (d ** 2).sum()
        t = np.clip(((X - p0[0]) * d[0] + (Y - p0[1]) * d[1] + (Z - p0[2]) * d[2]) / L, 0, 1)
        return (X - p0[0] - t * d[0]) ** 2 + (Y - p0[1] - t * d[1]) ** 2 + (Z - p0[2] - t * d[2]) ** 2 <= r * r

    def cylinder(self, p0, p1, r):
        """Cylinder with flat ends (cuffs, bands, rims)."""
        X, Y, Z = self.X, self.Y, self.Z
        p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = (d ** 2).sum()
        t = ((X - p0[0]) * d[0] + (Y - p0[1]) * d[1] + (Z - p0[2]) * d[2]) / L
        return (t >= 0) & (t <= 1) & ((X - p0[0] - t * d[0]) ** 2 + (Y - p0[1] - t * d[1]) ** 2 + (Z - p0[2] - t * d[2]) ** 2 <= r * r)

    def strand(self, p0, p1, p2, r0, r1, n=22):
        """Tapered tube along a curve (start p0, bend toward p1, end p2). For bangs and curling locks."""
        p0, p1, p2 = [np.array(p, float) for p in (p0, p1, p2)]
        lo = np.floor(np.minimum(np.minimum(p0, p1), p2) - r0 - 1).astype(int)
        hi = np.ceil(np.maximum(np.maximum(p0, p1), p2) + r0 + 2).astype(int)
        lo = np.maximum(lo, 0); hi = np.minimum(hi, [self.W, self.H, self.D])
        sx, sy, sz = slice(lo[0], hi[0]), slice(lo[1], hi[1]), slice(lo[2], hi[2])
        x, y, z = self.X[sy, sz, sx], self.Y[sy, sz, sx], self.Z[sy, sz, sx]
        m = np.zeros(x.shape, bool)
        for i in range(n + 1):
            t = i / n
            p = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2
            r = r0 + (r1 - r0) * t
            m |= (x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 <= r * r
        full = np.zeros(self.occ.shape, bool); full[sy, sz, sx] = m
        return full

    def lathe(self, cx, cz, y0, y1, rx_of_y, rz_of_y):
        """Stack of horizontal ellipses from row y0 to y1-1: robes, skirts, bodies, pots.
        cz may be a function of the row (sway a hem). For left/right halves that move
        separately (walking), build two lathes and keep X < cx / X >= cx of each."""
        m = np.zeros(self.occ.shape, bool)
        X, Z = self.X[0], self.Z[0]
        for y in range(y0, y1):
            rx, rz = rx_of_y(y), rz_of_y(y)
            czy = cz(y) if callable(cz) else cz
            m[y] = ((X - cx) / rx) ** 2 + ((Z - czy) / rz) ** 2 <= 1
        return m

    def bent_cone(self, cx, cz, y_base, y_tip, r_base, r_tip, bend=(0, 0), power=(2.5, 1.0)):
        """Witch-hat style cone from y_base (exclusive) up to y_tip, tip pushed by `bend` (dx, dz)."""
        m = np.zeros(self.occ.shape, bool)
        X, Z = self.X[0], self.Z[0]
        for y in range(y_tip, y_base):
            t = (y_base - y) / float(y_base - y_tip)
            r = r_base + (r_tip - r_base) * t
            hx = cx + bend[0] * t ** power[0]
            hz = cz + bend[1] * t ** power[1]
            m[y] = (X - hx) ** 2 + (Z - hz) ** 2 <= r * r
        return m

    # ---------------------------------------------------- style components
    def brim(self, cx, cz, y_top, rx, rz, color, part, droop_at=0.82, droop=5.0,
             contact_r=0.76, contact_fade=0.18):
        """Level, 2-layer brim whose outer ring drops one layer. Never tilt thin flat parts:
        a slight tilt turns into plank-like bands in sprite stacking. Shading is smooth
        (analytic normal of a gently drooping surface) with a contact shadow near the centre."""
        X, Y, Z = self.X, self.Y, self.Z
        rr = np.sqrt(((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2)
        inner = (rr < droop_at) & ((Y == y_top) | (Y == y_top + 1))
        outer = (rr >= droop_at) & ((Y == y_top + 1) | (Y == y_top + 2))
        mask = (rr <= 1) & (inner | outer)
        self.put(mask, color, part)
        fx = 2 * droop * (X - cx) / rx ** 2
        fz = 2 * droop * (Z - cz) / rz ** 2
        normal = np.stack([fx, -np.ones_like(fx), fz], -1)
        self.smooth_surface(mask, part, normal,
                            contact=0.15 * np.clip((contact_r - rr) / contact_fade, 0, 1),
                            underside=(Y == y_top + 2))
        return mask

    def smooth_surface(self, mask, part, normal, contact=None, underside=None, two_sided=False):
        """Shade these voxels from a given smooth normal field (finer steps) instead of
        the stepped per-cube normal. Use for any large flat or gently curved part.
        two_sided: thin translucent sheets (wings) catch light from either side."""
        z = np.zeros(self.occ.shape)
        self.smooth.append(dict(mask=mask, part=part, normal=normal, two_sided=two_sided,
                                contact=z if contact is None else contact,
                                underside=np.zeros(self.occ.shape, bool) if underside is None else underside))

    def membrane(self, root, yaw_deg, ellipses, thickness=2.0):
        """Thin vertical sheet (wings, fins, capes, banners) hinged at `root`.
        The sheet runs outward along the direction yaw_deg (0 = +x, 90 = straight back);
        its outline is the union of ellipses (cu, cv, ru, rv, rot_deg) in sheet coordinates
        u (distance out from the root) and v (rows down from the root, negative = up).
        Placed nothing yet: returns dict(mask, u, v, rr) so the caller can colour veins/rims,
        then call put(). Shaded smoothly with a two-sided normal.
        Vertical sheets slice cleanly into layers; keep them vertical rather than near-flat."""
        X, Y, Z = self.X, self.Y, self.Z
        a = np.radians(yaw_deg)
        d = np.array([np.cos(a), 0, -np.sin(a)])            # outward along the sheet
        n = np.array([np.sin(a), 0, np.cos(a)])             # sheet normal (front side)
        rx, ry, rz = X - root[0], Y - root[1], Z - root[2]
        u = rx * d[0] + rz * d[2]
        v = ry
        s = rx * n[0] + rz * n[2]
        rr = np.full(self.occ.shape, np.inf)
        for cu, cv, ru, rv, rot in ellipses:
            t = np.radians(rot)
            du, dv = u - cu, v - cv
            pu = du * np.cos(t) + dv * np.sin(t)
            pv = -du * np.sin(t) + dv * np.cos(t)
            rr = np.minimum(rr, np.sqrt((pu / ru) ** 2 + (pv / rv) ** 2))
        mask = (rr <= 1) & (np.abs(s) <= thickness / 2) & (u >= 0)
        side = np.where(s >= 0, 1.0, -1.0)[..., None]
        normal = side * n[None, None, None, :] * np.ones(self.occ.shape + (3,))
        return dict(mask=mask, u=u, v=v, rr=rr, normal=normal)

    def cuffed_arm(self, shoulder, wrist, sleeve, cuff, skin, sleeve_in,
                   parts=('sleeve', 'gold', 'sleeve_in', 'skin'),
                   sleeve_r=3.2, cuff_r=3.6, open_r=2.4, hand_r=2.3, wrist_r=1.5):
        """Sleeve ending in a flat cuff with a dark opening; the hand comes out on a thin wrist."""
        S = np.array(shoulder, float); E = np.array(wrist, float)
        d = (E - S) / np.linalg.norm(E - S)
        p_sleeve, p_cuff, p_in, p_skin = parts
        cuff_m = self.cylinder(E - 0.4 * d, E + 1.4 * d, cuff_r)
        hollow = self.cylinder(E + 0.3 * d, E + 3.0 * d, open_r)
        self.put(cuff_m & ~hollow, cuff, p_cuff)
        self.put(self.cylinder(E - 0.2 * d, E + 0.4 * d, open_r), sleeve_in, p_in)
        self.put(self.capsule(S, E, sleeve_r), sleeve, p_sleeve)
        self.put(self.ball(E + 3.4 * d, hand_r), skin, p_skin)
        self.put(self.cylinder(E + 0.4 * d, E + 2.6 * d, wrist_r), skin, p_skin)
        return E + 3.4 * d          # hand centre, handy for placing props

    def cuffed_arm_to(self, shoulder, hand, *a, **kw):
        """cuffed_arm, but aimed so the hand lands on `hand` (for raised/casting poses)."""
        S = np.array(shoulder, float); Hd = np.array(hand, float)
        d = (Hd - S) / np.linalg.norm(Hd - S)
        return self.cuffed_arm(S, Hd - 3.4 * d, *a, **kw)

    def sparkle(self, points, color, part='magic', size=1.0):
        """Small unlit glints (magic motes, bursts, bolts). Exact colour, always bright."""
        for p in points:
            m = self.ell(p[0], p[1], p[2], size, size, size) | self.cylinder(
                (p[0] - size * 1.6, p[1], p[2]), (p[0] + size * 1.6, p[1], p[2]), 0.55) | self.cylinder(
                (p[0], p[1] - size * 1.6, p[2]), (p[0], p[1] + size * 1.6, p[2]), 0.55)   # little plus-shaped star
            placed = self.put(m, color, part)
            self.flat |= placed

    def recess_panel(self, panel, color, rows, skip_rows=(), edge_color=None):
        """Push a front panel one cube in so the trim beside it reads as a lip.
        `panel` marks the panel's voxels; optional darker edge where it meets the trim."""
        for y in rows:
            if y in skip_rows:
                continue
            for x in range(self.W):
                zs = np.where(panel[y, :, x])[0]
                if not len(zs):
                    continue
                zf = zs.max()
                self.occ[y, zf, x] = False; self.part[y, zf, x] = 0
                self.col[y, zf - 1, x] = color
            if edge_color is not None:
                xs = [x for x in range(self.W) if panel[y, :, x].any()]
                for x in ((min(xs), max(xs)) if xs else ()):
                    zs = np.where(self.occ[y, :, x])[0]
                    if len(zs):
                        self.col[y, zs.max(), x] = edge_color

    def glow(self, part, boost=None):
        """Self-lit part (orb, gem): stays bright and gets a specular highlight.
        boost (e.g. 1.0-1.35) brightens it further, for a pulsing spell focus."""
        self.glow_parts.append(part)
        if boost is not None:
            self.glow_boost = getattr(self, 'glow_boost', {}); self.glow_boost[part] = boost

    # --------------------------------------------------------- face paint
    def front_z(self, y, x):
        zs = np.where(self.occ[y, :, x])[0]
        return zs.max() if len(zs) else None

    def paint_eyes(self, grid, cx, top_y, part='skin', gap=style.EYE_GAP, depth=style.EYE_DEPTH):
        """Paint a pair of eyes onto the face. `grid` is one eye (rows of colours or None),
        listed from the inner column outward; it is mirrored for the other eye.
        Eyes are exact colours (unlit) and painted `depth` cubes deep."""
        for side in (1, -1):
            for r, row in enumerate(grid):
                for c, color in enumerate(row):
                    if color is None:
                        continue
                    if isinstance(color, str):
                        color = hexc(color)
                    x = int(cx) + side * (gap + c); y = top_y + r
                    z = self.front_z(y, x)
                    if z is None:
                        continue
                    for dz in range(depth):
                        if self.part[y, z - dz, x] == self.pid(part) and self.occ[y, z - dz, x]:
                            self.col[y, z - dz, x] = color
                            self.flat[y, z - dz, x] = True

    # ------------------------------------------------------------- shading
    def scaled(self, k):
        """A copy enlarged by factor k before lighting (e.g. props built small, scaled up to the
        characters' one-cube-per-pixel size). Shapes are resampled smoothly so curves stay round
        and the lighting is computed at full resolution; colours and parts are resampled nearest."""
        from scipy import ndimage as ndi
        if k == 1:
            return self
        H2, D2, W2 = (int(round(n * k)) for n in (self.H, self.D, self.W))
        f = (H2 / self.H, D2 / self.D, W2 / self.W)
        out = Model(W2, H2, D2)
        out.occ = ndi.zoom(self.occ.astype(float), f, order=1) > 0.5
        out.col = np.stack([ndi.zoom(self.col[..., i], f, order=0) for i in range(3)], -1)
        out.part = ndi.zoom(self.part, f, order=0)
        out.flat = ndi.zoom(self.flat.astype(np.uint8), f, order=0).astype(bool)
        out.parts, out.glow_parts = dict(self.parts), list(self.glow_parts)
        if hasattr(self, 'glow_boost'):
            out.glow_boost = dict(self.glow_boost)
        out.occ &= out.part > 0
        return out

    def _apply_lean(self):
        """Shear the model forward (running lean). Whole layers move, so they stay level."""
        if not self.lean:
            return
        def shift(a):
            out = np.zeros_like(a)
            for y in range(self.H):
                k = int(round(self.lean * (self.lean_pivot - y)))
                if k > 0:
                    out[y, k:] = a[y, :-k]
                elif k < 0:
                    out[y, :k] = a[y, -k:]
                else:
                    out[y] = a[y]
            return out
        self.occ, self.col, self.part, self.flat = (shift(a) for a in (self.occ, self.col, self.part, self.flat))
        for s in self.smooth:
            for key in ('mask', 'normal', 'contact', 'underside'):
                s[key] = shift(s[key])
        self.lean = 0.0

    def shade(self):
        """House-style lighting -> RGBA volume [y][z][x]."""
        self._apply_lean()
        occ = self.occ
        f = ndi.gaussian_filter(occ.astype(float), style.NORMAL_BLUR)
        gy, gz, gx = np.gradient(f)
        n = -np.stack([gx, gy, gz], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
        L = np.array(style.LIGHT, float); L /= np.linalg.norm(L)
        lam = np.clip((n * L).sum(-1), 0, 1)
        sh = style.AMBIENT + style.DIFFUSE * lam
        sh = np.round(sh / style.BAND) * style.BAND
        for s in self.smooth:
            bm = s['mask'] & occ & (self.part == self.pid(s['part']))
            nn = np.linalg.norm(s['normal'], axis=-1, keepdims=True)
            nb = np.divide(s['normal'], nn, out=np.zeros_like(s['normal']), where=nn > 0)
            dot = (nb * L).sum(-1)
            lb = np.clip(np.abs(dot) if s.get('two_sided') else dot, 0, 1)
            sh[bm] = (style.AMBIENT + style.DIFFUSE * lb)[bm]
            sh[bm] -= s['contact'][bm]
            sh[bm] = np.round(sh[bm] / style.SMOOTH_BAND) * style.SMOOTH_BAND
            sh[bm & s['underside']] -= style.BAND
        sh[self.flat] = np.maximum(sh[self.flat], 1.0)
        spec = np.zeros(occ.shape, bool)
        for p in self.glow_parts:
            o = self.part == self.pid(p)
            sh[o] = style.GLOW_MIN + style.GLOW_RANGE * lam[o]
            if p in getattr(self, 'glow_boost', {}):
                sh[o] *= self.glow_boost[p]
            spec |= o & (lam > style.GLOW_SPEC)
        out = np.clip(self.col * sh[..., None], 0, 255)
        out[spec] = style.SPEC_COLOR
        vol = np.zeros(occ.shape + (4,), np.uint8)
        vol[..., :3] = out.astype(np.uint8)
        vol[..., 3] = occ * 255
        if self.lift:
            vol = np.concatenate([vol[self.lift:], np.zeros_like(vol[:self.lift])], 0)
        return vol
