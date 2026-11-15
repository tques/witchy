"""Environment props for the prototype, built with the same toolkit and house lighting as the characters.

Every builder returns an RGBA volume [y][z][x] whose footprint is centred on the prop's position
and whose bottom layer sits on the ground. Coordinates inside a builder: x across, z depth
(+z faces the camera side), h = height above the ground (layer index = H - 1 - h).
Props that face a direction (walls, fences, shelves) are built in that world orientation so the
baked light stays consistent across the room.
"""
import math, random
import numpy as np
from spritestack import Model

WOOD, WOOD_D, WOOD_L = (140, 95, 60), (100, 66, 42), (170, 120, 78)
PLASTER, BEAM = (222, 206, 180), (96, 64, 44)
STONE = [(150, 146, 150), (132, 128, 138), (164, 158, 160), (120, 118, 128)]
GOLD, IRON = (215, 160, 60), (58, 52, 66)
LEAF = [(70, 140, 80), (88, 160, 86), (60, 122, 74), (104, 176, 96)]
SCALE = 1.0       # props are designed small and enlarged to character scale at bake time (build_game sets this)


class P:
    """Small wrapper: a Model sized W x H x D with ground-relative helpers."""
    def __init__(self, W, H, D):
        self.m = Model(W, H, D); self.W, self.H, self.D = W, H, D
        m = self.m
        self.X, self.Z = m.X, m.Z
        self.h = (H - 1) - m.Y                     # height above ground for every voxel
        self.cx, self.cz = (W - 1) / 2, (D - 1) / 2

    def y(self, h):                                # height -> model row
        return self.H - 1 - h

    def box(self, x0, x1, z0, z1, h0, h1):
        X, Z, h = self.X, self.Z, self.h
        return (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1) & (h >= h0) & (h < h1)

    def put(self, mask, color, part='p'):
        return self.m.put(mask, color, part)

    def done(self):
        return self.m.scaled(SCALE).shade()


def _rng(seed):
    return random.Random(seed)


# ----------------------------------------------------------------- walls
def wall(length, axis='x', height=44, thick=4, kind='cottage', window=None, door=None, seed=0):
    """A straight wall segment. axis: runs along x or z. kind: 'cottage' (plaster, timber, wood
    wainscot), 'stone'. window / door: (start, end) along the segment."""
    W, D = (length, thick) if axis == 'x' else (thick, length)
    p = P(W, height, D)
    X, Z, h = p.X, p.Z, p.h
    u = X if axis == 'x' else Z                     # along the wall
    r = _rng(seed)
    body = p.box(0, W, 0, D, 0, height)
    if door:
        a, b = door
        hole = (u >= a) & (u < b) & (h < 34)
        frame = (u >= a - 2) & (u < b + 2) & (h < 36) & ~hole
        body &= ~hole
        panel = (u >= a) & (u < b) & (h < 34) & ((Z if axis == 'x' else X) >= thick - 2)
        placed = p.put(panel, WOOD, 'door')
        p.m.col[placed & (((u - a) % 4) < 0.6)] = WOOD_D            # plank lines
        knob = (np.abs(u - (b - 3)) < 1) & (np.abs(h - 16) < 1) & panel
        p.m.col[knob & placed] = GOLD
        p.put(frame & body, BEAM, 'frame')
    if window:
        a, b = window
        glass = (u >= a) & (u < b) & (h >= 18) & (h < 32)
        across = Z if axis == 'x' else X
        body &= ~glass
        pane = glass & (across >= thick // 2 - 1) & (across < thick // 2 + 1)
        cross = pane & ((np.abs(u - (a + b) / 2) < 0.8) | (np.abs(h - 25) < 0.8))
        p.put(cross, BEAM, 'frame')
        placed = p.put(pane, (190, 215, 240), 'glass')
        p.put(((u >= a - 1) & (u < b + 1) & (h >= 17) & (h < 33)) & ~glass & body, BEAM, 'frame')
    if kind == 'cottage':
        placed = p.put(body, PLASTER, 'wall')
        col = p.m.col
        col[placed & (h < 10)] = WOOD                                          # wainscot
        col[placed & (h < 10) & (np.round(u) % 6 == 0)] = WOOD_D
        col[placed & ((h == 10) | (h >= height - 3))] = BEAM                   # beams
        col[placed & (np.round(u) % 16 == 0)] = BEAM                           # posts
    else:   # stone
        placed = p.put(body, STONE[0], 'wall')
        bw, bh = 8, 5
        row = (h // bh).astype(int)
        uu = u + (row % 2) * (bw // 2)
        block = (uu // bw).astype(int) * 31 + row * 7
        for k in np.unique(block[placed]):
            p.m.col[placed & (block == k)] = STONE[(k * 2654435761 + seed) % 4]
        mortar = placed & (((h % bh) == 0) | ((np.round(uu) % bw) == 0))
        p.m.col[mortar] = (98, 96, 106)
    return p.done()


def fence(length, axis='x', seed=0):
    W, D = (length, 4) if axis == 'x' else (4, length)
    p = P(W, 12, D)
    u = p.X if axis == 'x' else p.Z
    across = p.Z if axis == 'x' else p.X
    mid = np.abs(across - 1.5) <= 1.0
    post = mid & (((np.round(u) % 12) <= 1)) & (p.h < 11)
    p.put(post, WOOD_D, 'post')
    rail = (np.abs(across - 1.5) <= 0.6) & (((p.h >= 3) & (p.h < 5)) | ((p.h >= 7) & (p.h < 9)))
    p.put(rail, WOOD, 'rail')
    return p.done()


# ----------------------------------------------------------- furniture
def bookshelf(seed=1):
    p = P(26, 34, 8)
    X, Z, h = p.X, p.Z, p.h
    r = _rng(seed)
    for sh in (1, 11, 21):
        x = 2
        while x < 23:
            w = r.choice([2, 2, 3]); bh = r.randint(6, 8)
            col = r.choice([(150, 50, 60), (60, 90, 150), (70, 130, 80), (180, 140, 60), (110, 70, 140), (200, 190, 170)])
            p.put(p.box(x, x + w, 1, 7, sh + 1, sh + 1 + bh), col, 'book')
            x += w
    frame = p.box(0, 26, 0, 8, 0, 34) & ~p.box(2, 24, 2, 8, 2, 32)
    p.put(frame, WOOD, 'frame')
    for sh in (1, 11, 21):
        p.put(p.box(0, 26, 0, 8, sh, sh + 1), WOOD_D, 'shelf')
    return p.done()


def cauldron():
    p = P(26, 20, 26)
    m = p.m; cx, cz = p.cx, p.cz
    # embers and logs underneath
    for a in (0, 60, 120):
        t = math.radians(a)
        m.put(m.capsule((cx - 8 * math.cos(t), p.y(1), cz - 8 * math.sin(t)), (cx + 8 * math.cos(t), p.y(1), cz + 8 * math.sin(t)), 1.4), WOOD_D, 'log')
    m.put(m.ell(cx, p.y(2), cz, 5, 1.5, 5), (255, 150, 60), 'ember'); m.glow('ember')
    # brew surface and bubbles (glowing)
    m.put(m.ell(cx, p.y(16), cz, 8.4, 0.8, 8.4), (120, 230, 120), 'brew')
    for bx, bz in ((-3, 2), (2, -2), (4, 3)):
        m.put(m.ball((cx + bx, p.y(17), cz + bz), 1.3), (170, 250, 160), 'brew')
    m.glow('brew', boost=1.1)
    # iron pot: lathe that bulges, hollow top, thick rim
    pot = m.lathe(cx, cz, p.y(17), p.y(3) + 1, lambda yy: 10.5 * math.sin(math.pi * (0.15 + 0.75 * ((p.y(3) - yy) / 14))) + 1,
                  lambda yy: 10.5 * math.sin(math.pi * (0.15 + 0.75 * ((p.y(3) - yy) / 14))) + 1)
    m.put(pot, IRON, 'pot')
    rim = m.lathe(cx, cz, p.y(17), p.y(15) + 1, lambda yy: 10.5, lambda yy: 10.5) & ~m.ell(cx, p.y(16), cz, 8.6, 3, 8.6)
    m.put(rim, (80, 74, 90), 'pot')
    for a in (30, 150, 270):
        t = math.radians(a)
        m.put(m.capsule((cx + 7 * math.cos(t), p.y(5), cz + 7 * math.sin(t)), (cx + 9 * math.cos(t), p.y(0), cz + 9 * math.sin(t)), 1.3), IRON, 'pot')
    return p.done()


def table():
    p = P(26, 22, 16)
    m = p.m
    m.put(m.ell(5, p.y(18), 7, 0.9, 2.2, 0.9), (255, 200, 90), 'flame'); m.glow('flame', boost=1.2)
    m.put(p.box(4, 7, 6, 9, 14, 17), (240, 232, 210), 'candle')
    p.put(p.box(14, 22, 5, 11, 14, 16), (110, 60, 120), 'book')
    p.put(p.box(14, 22, 5, 11, 16, 17), (230, 220, 200), 'book')
    p.put(p.box(0, 26, 0, 16, 12, 14), WOOD_L, 'top')
    for x0, z0 in ((1, 1), (23, 1), (1, 13), (23, 13)):
        p.put(p.box(x0, x0 + 2, z0, z0 + 2, 0, 12), WOOD_D, 'leg')
    return p.done()


def bed():
    p = P(22, 14, 36)
    p.put(p.box(3, 19, 1, 8, 7, 10), (240, 236, 228), 'pillow')
    blanket = p.box(1, 21, 8, 35, 6, 10)
    placed = p.put(blanket, (120, 70, 150), 'blanket')
    p.m.col[placed & ((np.round(p.Z) % 6) < 2)] = (150, 95, 175)
    p.put(p.box(0, 22, 0, 36, 3, 6), WOOD, 'frame')
    p.put(p.box(0, 22, 0, 2, 0, 14), WOOD_D, 'head')
    for x0, z0 in ((0, 33), (19, 33)):
        p.put(p.box(x0, x0 + 3, z0, z0 + 3, 0, 4), WOOD_D, 'leg')
    return p.done()


def chest():
    p = P(16, 13, 12)
    m = p.m
    lid = m.cylinder((0, p.y(8), p.cz), (15.9, p.y(8), p.cz), 5.6) & (p.h >= 8)
    placed = m.put(lid, WOOD, 'lid')
    p.put(p.box(0, 16, 1, 11, 0, 8), WOOD, 'box')
    for x0 in (2, 12):
        m.col[(np.abs(p.X - x0 - 0.5) < 1) & m.occ] = GOLD
    m.col[(np.abs(p.X - 7.5) < 1.2) & (np.abs(p.h - 8) < 1.5) & (p.Z > 8) & m.occ] = GOLD
    return p.done()


def barrel():
    p = P(13, 15, 13)
    m = p.m
    body = m.lathe(p.cx, p.cz, p.y(14), p.y(0) + 1, lambda yy: 5 + 1.2 * math.sin(math.pi * (p.y(0) - yy) / 14),
                   lambda yy: 5 + 1.2 * math.sin(math.pi * (p.y(0) - yy) / 14))
    placed = m.put(body, WOOD, 'barrel')
    m.col[placed & ((p.h == 2) | (p.h == 11))] = IRON
    m.col[placed & (p.h == 14)] = WOOD_D
    return p.done()


# ------------------------------------------------------------- outdoors
def tree(seed=3, height=78):
    p = P(46, height, 46)
    m = p.m; r = _rng(seed); cx, cz = p.cx, p.cz
    for i in range(7):
        a = r.uniform(0, 2 * math.pi); rad = r.uniform(5, 11)
        hc = r.uniform(height * 0.52, height * 0.82)
        rr = r.uniform(10, 14)
        m.put(m.ell(cx + rad * math.cos(a), p.y(hc), cz + rad * math.sin(a), rr, rr * 0.8, rr), LEAF[i % 4], 'leaf')
    m.put(m.ell(cx, p.y(height * 0.86), cz, 11, 9, 11), LEAF[3], 'leaf')
    m.put(m.capsule((cx, p.y(0), cz), (cx + 1, p.y(height * 0.55), cz - 1), 4.2), (110, 78, 56), 'trunk')
    for a in (0, 120, 240):                                            # roots
        t = math.radians(a + 20)
        m.put(m.capsule((cx, p.y(3), cz), (cx + 7 * math.cos(t), p.y(0), cz + 7 * math.sin(t)), 2.0), (100, 70, 50), 'trunk')
    return p.done()


def bush(seed=4):
    p = P(20, 13, 20)
    m = p.m; r = _rng(seed)
    for i in range(5):
        a = r.uniform(0, 2 * math.pi); rad = r.uniform(2, 5)
        m.put(m.ell(p.cx + rad * math.cos(a), p.y(r.uniform(4, 7)), p.cz + rad * math.sin(a), 6, 5.5, 6), LEAF[i % 4], 'leaf')
    for i in range(4):                                                 # a few berries
        a = r.uniform(0, 2 * math.pi)
        m.col[m.ball((p.cx + 7 * math.cos(a), p.y(6), p.cz + 7 * math.sin(a)), 1.2) & m.occ] = (200, 60, 80)
    return p.done()


def flowerbed(seed=5, colors=((230, 120, 170), (250, 220, 90), (180, 140, 230), (245, 245, 240))):
    p = P(26, 9, 12)
    m = p.m; r = _rng(seed)
    for i in range(10):
        x, z = r.uniform(3, 23), r.uniform(3, 9)
        hh = r.uniform(4, 6.5)
        m.put(m.ball((x, p.y(hh + 1), z), 1.4), colors[i % len(colors)], 'petal')
        m.put(m.capsule((x, p.y(2), z), (x, p.y(hh), z), 0.6), (80, 150, 80), 'stem')
    p.put(p.box(0, 26, 0, 12, 0, 2), (110, 80, 60), 'soil')
    edge = p.box(0, 26, 0, 12, 0, 3) & ~p.box(1, 25, 1, 11, 0, 3)
    p.put(edge, (150, 146, 150), 'edge')
    return p.done()


def mushroom(seed=6, big=False):
    s = 1.6 if big else 1.0
    p = P(int(10 * s) + 2, int(10 * s) + 1, int(10 * s) + 2)
    m = p.m
    cap = m.ell(p.cx, p.y(6 * s), p.cz, 4 * s, 2.6 * s, 4 * s) & (p.h >= 5 * s)
    placed = m.put(cap, (200, 60, 70), 'cap')
    r = _rng(seed)
    for i in range(5):
        a = r.uniform(0, 2 * math.pi)
        m.col[m.ball((p.cx + 2.8 * s * math.cos(a), p.y(7 * s), p.cz + 2.8 * s * math.sin(a)), 0.9 * s) & placed] = (250, 245, 235)
    m.put(m.capsule((p.cx, p.y(0), p.cz), (p.cx, p.y(5 * s), p.cz), 1.4 * s), (240, 232, 215), 'stem')
    return p.done()


def well():
    p = P(28, 36, 28)
    m = p.m; cx, cz = p.cx, p.cz
    m.put(m.ell(cx, p.y(9), cz, 7, 0.6, 7), (60, 90, 140), 'water')
    ring = m.lathe(cx, cz, p.y(10), p.y(0) + 1, lambda yy: 10, lambda yy: 10) & ~m.lathe(cx, cz, p.y(10), p.y(0) + 1, lambda yy: 7, lambda yy: 7)
    placed = m.put(ring, STONE[0], 'stone')
    blk = ((np.arctan2(p.X - cx, p.Z - cz) * 4).astype(int) * 7 + (p.h // 3).astype(int) * 3)
    for k in np.unique(blk[placed]):
        m.col[placed & (blk == k)] = STONE[k % 4]
    for sx in (-9, 9):
        m.put(p.box(cx + sx - 1, cx + sx + 1, cz - 1, cz + 1, 10, 26), WOOD_D, 'post')
    m.put(m.capsule((cx - 9, p.y(22), cz), (cx + 9, p.y(22), cz), 0.8), WOOD, 'post')
    # steep gable roof: 1 layer per cube (45 degrees) so it slices cleanly
    roof = (np.abs(p.Z - cz) <= 12) & (np.abs(p.X - cx) <= 12) & (p.h >= 25) & (np.abs(np.abs(p.Z - cz) - (34 - p.h)) <= 1.2)
    placed = m.put(roof, (150, 70, 60), 'roof')
    m.col[placed & ((np.round(p.X) % 4) == 0)] = (120, 54, 48)
    return p.done()


def rocks(seed=7):
    p = P(16, 8, 12)
    m = p.m; r = _rng(seed)
    for i in range(3):
        m.put(m.ell(r.uniform(5, 11), p.y(r.uniform(1.5, 3)), r.uniform(4, 8), r.uniform(3, 5), r.uniform(2.5, 4), r.uniform(3, 4)), STONE[i], 'rock')
    return p.done()


def signpost():
    p = P(16, 22, 6)
    p.put(p.box(1, 15, 2, 4, 13, 19), WOOD_L, 'sign')
    p.put(p.box(7, 9, 2, 4, 0, 21), WOOD_D, 'post')
    return p.done()


def crystal(lit=False):
    p = P(22, 34, 22)
    m = p.m; cx, cz = p.cx, p.cz
    core = (130, 230, 255) if lit else (90, 100, 130)
    # diamond silhouette: radius grows then shrinks; 6-sided facets
    ang = np.arctan2(p.X - cx, p.Z - cz)
    rad = np.hypot(p.X - cx, p.Z - cz) * (1 + 0.12 * np.cos(6 * ang))
    prof = np.where(p.h < 12, 2 + (p.h - 3) * 0.65, 8 - (p.h - 12) * 0.42)
    body = (rad <= prof) & (p.h >= 3) & (p.h <= 30)
    placed = m.put(body, core, 'crystal')
    m.col[placed & (np.cos(6 * ang) > 0.6)] = tuple(min(255, int(c * 1.18)) for c in core)
    if lit:
        m.glow('crystal', boost=1.15)
    for a in (0, 110, 220):
        t = math.radians(a)
        m.put(m.ell(cx + 8 * math.cos(t), p.y(1.5), cz + 8 * math.sin(t), 4, 2.5, 3.5), STONE[1], 'rock')
    return p.done()


def thorns(seed=8):
    p = P(34, 18, 12)
    m = p.m; r = _rng(seed)
    for i in range(9):
        x0 = r.uniform(2, 32); x1 = x0 + r.uniform(-8, 8)
        m.put(m.strand((x0, p.y(0), r.uniform(3, 9)), ((x0 + x1) / 2, p.y(r.uniform(10, 17)), r.uniform(2, 10)),
                       (x1, p.y(r.uniform(2, 8)), r.uniform(3, 9)), 1.6, 0.6), (90, 50, 100) if i % 2 else (70, 40, 85), 'vine')
    return p.done()


def stump(seed=13):
    """Hollow tree stump: rings on top, dark hollow, roots, a couple of tiny mushrooms."""
    p = P(22, 12, 22)
    m = p.m; cx, cz = p.cx, p.cz; r = _rng(seed)
    bark, wood, hollow = (112, 80, 56), (196, 156, 104), (52, 38, 32)
    m.put(m.ell(cx, p.y(9.6), cz, 3.2, 1.2, 3.2), hollow, 'hollow')
    body = m.lathe(cx, cz, p.y(10), p.y(0) + 1, lambda yy: 6.5 + 1.4 * ((yy - p.y(10)) / 10) ** 2, lambda yy: 6.5 + 1.4 * ((yy - p.y(10)) / 10) ** 2)
    placed = m.put(body, bark, 'stump')
    top = placed & (p.h >= 10)
    ring = np.hypot(p.X - cx, p.Z - cz)
    m.col[top] = wood
    m.col[top & (np.round(ring) % 2 == 0)] = (176, 136, 88)
    m.col[top & (ring > 5.6)] = bark
    m.col[placed & ~top & ((np.round(np.arctan2(p.X - cx, p.Z - cz) * 5) % 2) == 0)] = (98, 70, 50)   # bark ridges
    for a in (20, 140, 260):
        t = math.radians(a)
        m.put(m.capsule((cx + 5 * math.cos(t), p.y(3), cz + 5 * math.sin(t)), (cx + 10 * math.cos(t), p.y(0), cz + 10 * math.sin(t)), 1.6), bark, 'root')
    for dx, dz, hh in ((6.5, 3, 3), (7.2, 0.5, 5)):
        m.put(m.ell(cx + dx, p.y(hh + 1.2), cz + dz, 1.6, 0.9, 1.6), (220, 120, 70), 'cap')
        m.put(m.capsule((cx + dx, p.y(hh - 1), cz + dz), (cx + dx, p.y(hh + 1), cz + dz), 0.6), (240, 230, 210), 'stem')
    return p.done()


def boulder(seed=15):
    """Big mossy boulder: one large rounded rock with a couple of smaller ones, moss on the top."""
    p = P(34, 22, 28)
    m = p.m; cx, cz = p.cx, p.cz
    rock = [(150, 146, 150), (136, 132, 140), (162, 156, 158)]
    main = m.ell(cx - 1, p.y(8), cz, 13, 12, 10.5) & (p.h >= 0) | m.ell(cx + 4, p.y(12), cz - 1, 9, 9, 8)
    placed = m.put(main, rock[0], 'rock')
    m.col[placed & (((p.X * 3 + p.Z * 5 + p.h * 7).astype(int) % 11) < 3)] = rock[1]          # mottling
    m.col[placed & (p.h >= 15)] = (98, 150, 84)                                                   # moss on top
    m.col[placed & (p.h >= 13) & (p.h < 15) & ((np.round(p.X + p.Z) % 3) == 0)] = (110, 160, 90)
    m.put(m.ell(cx + 12, p.y(3), cz + 7, 5, 3.5, 4), rock[2], 'rock')
    m.put(m.ell(cx - 13, p.y(2.5), cz + 6, 4, 3, 3.5), rock[1], 'rock')
    return p.done()


def wildflowers(seed=14):
    """A loose patch of mixed wild flowers on the grass (no bed): daisies, bluebells, poppies, buttercups."""
    p = P(28, 9, 22)
    m = p.m; r = _rng(seed)
    kinds = [((250, 250, 245), (250, 210, 80)), ((140, 150, 235), None), ((230, 80, 80), (40, 30, 30)),
             ((250, 220, 70), None), ((235, 150, 205), None), ((190, 130, 230), None)]
    for i in range(22):
        x, z = r.uniform(3, 25), r.uniform(3, 19)
        if ((x - 14) / 12) ** 2 + ((z - 11) / 9) ** 2 > 1:
            continue
        hh = r.uniform(3, 6.5)
        petal, centre = kinds[i % len(kinds)]
        m.put(m.ball((x, p.y(hh + 1), z), 0.7), centre or petal, 'centre')
        m.put(m.ell(x, p.y(hh + 1), z, 1.6, 0.8, 1.6), petal, 'petal')
        m.put(m.capsule((x, p.y(0), z), (x, p.y(hh), z), 0.5), (84, 150, 78), 'stem')
        if r.random() < 0.6:
            m.put(m.ell(x + 1, p.y(1.5), z, 1.4, 0.6, 0.8), (96, 168, 84), 'leaf')
    return p.done()


PROPS = {
    'bookshelf': bookshelf, 'cauldron': cauldron, 'table': table, 'bed': bed, 'chest': chest, 'barrel': barrel,
    'tree': tree, 'tree2': lambda: tree(seed=11, height=70), 'bush': bush, 'bush2': lambda: bush(seed=12),
    'flowerbed': flowerbed, 'flowerbed2': lambda: flowerbed(seed=9, colors=((250, 150, 90), (240, 240, 245), (230, 120, 170))),
    'mushroom': mushroom, 'mushroom_big': lambda: mushroom(seed=10, big=True), 'well': well, 'rocks': rocks,
    'signpost': signpost, 'crystal_dim': crystal, 'crystal_lit': lambda: crystal(lit=True), 'thorns': thorns,
    'fence_x': lambda: fence(24, 'x'), 'fence_z': lambda: fence(24, 'z'),
    'stump': stump, 'wildflowers': wildflowers, 'wildflowers2': lambda: wildflowers(seed=21), 'boulder': boulder,
}
