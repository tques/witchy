"""Striker: an alien warrior who plays grav-ball, a futuristic full-contact football.
Designed directly in the house style (no source sprite): green-skinned alien with big amber
eyes in a sports helmet (glossy shell, ear pods, face cage), angular team-kit armour in matte
black and hazard orange, and glowing neon seams and number. Same scale as the witch."""
import math
import numpy as np
from spritestack import hexc
from spritestack.gait import gait

NAME = 'striker'
TITLE = 'Striker Sprite Stack'
SPRITE = None
GRID = (72, 90, 48)
ANIMATIONS = {'walk': dict(stride=5.0, arm=2.0), 'run': {}}   # a heavier, planted walk

SKIN, SKIN_FACE = (122, 186, 140), (112, 174, 132)
SHELL = (44, 46, 62)                                     # glossy black helmet / armour
PLATE, PLATE_D = (62, 66, 86), (36, 38, 52)              # gunmetal plates and seams
TEAM, TEAM_D = (240, 116, 36), (190, 78, 28)             # hazard orange
CAGE = (168, 174, 190)                                   # face cage bars
SUIT, SUIT_IN = (30, 30, 44), (14, 12, 22)               # under-suit
GLOVE = (74, 78, 98)
NEON = (96, 236, 255)                                    # glowing seams

# big amber alien eyes with a dark slit (inner column first, mirrored for the other eye)
EYE = [["2a1a12", "2a1a12", "2a1a12", "2a1a12"],
       ["d07a1e", "ffc040", "fff0b0", "2a1a12"],
       ["d07a1e", "1a0c08", "ffc040", "2a1a12"],
       ["d07a1e", "1a0c08", "ffc040", "2a1a12"],
       [None, "d07a1e", "d07a1e", None]]

CX, FEET = 36.0, 88


def build(m, sprite, pose=None):
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    cx = CX
    g = gait(pose)
    g.apply(m, pivot_y=FEET)
    face_z = int(zc + 6)

    def slab(y0, y1, a, b, cz=zc, x0=cx, n=4.0):
        """Rounded-square layers (superellipse): machined, not organic. a, b may vary by row."""
        out = np.zeros(m.occ.shape, bool)
        for y in range(max(y0, 0), min(y1, m.H)):
            ay, by_ = (a(y) if callable(a) else a), (b(y) if callable(b) else b)
            czy = cz(y) if callable(cz) else cz
            out[y] = (np.abs(X[y] - x0) / ay) ** n + (np.abs(Z[y] - czy) / by_) ** n <= 1
        return out

    def neon(mask):
        m.col[mask] = NEON
        m.part[mask] = m.pid('neon')

    # --- 1. face cage (in front of the face, below the eyes)
    fz = face_z + 2.2
    for y in (37.5, 40.5):
        m.put(m.cylinder((cx - 6.5, y, fz), (cx + 6.5, y, fz), 0.8), CAGE, 'cage')
    m.put(m.cylinder((cx, 36.5, fz), (cx, 41.5, fz), 0.8), CAGE, 'cage')
    for s in (-1, 1):
        m.put(m.capsule((cx + 6.5 * s, 37.5, fz), (cx + 9.5 * s, 34, zc + 3), 0.8), CAGE, 'cage')
        m.put(m.capsule((cx + 6.5 * s, 40.5, fz), (cx + 9.5 * s, 36, zc + 3), 0.8), CAGE, 'cage')

    # --- 2. head with flat face plate
    m.put(m.ell(cx, 32, zc + 1, 8.5, 8.5, 7.5) & (Z <= face_z), SKIN, 'skin')

    # --- 3. helmet: glossy shell open at the face, ear pods with glowing rings, team stripe
    for s in (-1, 1):
        ex = cx + 10.2 * s
        m.put(m.cylinder((ex - 1.0 * s, 32.5, zc + 1), (ex + 1.2 * s, 32.5, zc + 1), 3.4), PLATE, 'pod')
    pods = m.is_part('pod')
    r = np.sqrt((Y - 32.5) ** 2 + (Z - zc - 1) ** 2)
    neon(pods & (np.abs(X - cx) > 10.5) & (r > 2.0) & (r < 2.9))
    shell = m.ell(cx, 30, zc - 0.5, 10.2, 10.4, 9.6) & ~((Z > zc + 1) & (Y > 25.5) & (np.abs(X - cx) < 7.2))
    shell &= Y < 39
    helm = m.put(shell, SHELL, 'helm')
    stripe = (Y < 25) | (Z < zc - 1)                                      # over the top and down the back
    m.col[helm & (np.abs(X - cx) < 2.2) & stripe] = TEAM               # centre stripe
    m.col[helm & (np.abs(np.abs(X - cx) - 3.2) < 0.5) & stripe] = TEAM_D
    neon(helm & (Y >= 24.5) & (Y <= 25.4) & (Z > zc + 1))                # brow light strip

    # --- 4. shoulder pads: angular, level-topped slabs in team orange with neon edges
    for s in (-1, 1):
        px = cx + 9.8 * s
        top = slab(40, 45, lambda y: 6.4 - 0.6 * max(0, 41 - y), lambda y: 6.6 - 0.6 * max(0, 41 - y), x0=px)
        pad = m.put(top, TEAM, 'pads')
        m.col[pad & (Y == 44)] = TEAM_D
        neon(pad & (np.abs(X - cx) > 15.2) & (Y >= 42) & (Y <= 43))
        m.put(slab(45, 47, 5.2, 5.6, x0=px), PLATE_D, 'underpad')

    # --- 5. arms: black suit, orange gauntlets, armoured gloves
    parts = ('sleeve', 'gaunt', 'sleeve_in', 'glove')
    for s in (-1, 1):
        m.cuffed_arm((cx + 9.5 * s, 44, zc), (cx + 12.5 * s, 54 + g.arm_lift(s), zc + 1 + g.arm(s)),
                     SUIT, TEAM, GLOVE, SUIT_IN, parts, sleeve_r=3.0, cuff_r=3.9, open_r=2.5, hand_r=2.6)

    # --- 6. back: power pack with two glowing vents
    for s in (-1, 1):
        m.put(m.cylinder((cx + 2.3 * s, 44.5, zc - 9.0), (cx + 2.3 * s, 49.5, zc - 9.0), 0.9), NEON, 'neon')
    m.put(slab(43, 51, 4.6, 2.2, cz=zc - 6.8), PLATE_D, 'pack')

    # --- 7. torso: machined chest plate, segmented abdomen, belt, hips
    m.put(m.ell(cx, 41, zc, 5.5, 2.5, 5), SUIT, 'suit')                   # neck seal
    chest = m.put(slab(42, 53, lambda y: 9.3 - 0.1 * max(0, y - 46), 6.5), PLATE, 'chest')
    abs_ = m.put(slab(53, 61, lambda y: 7.8 - 0.05 * (y - 53), 5.8), SHELL, 'abs')
    front = chest & (Z > zc + 2)
    m.col[front & (np.abs(X - cx) > 5.5) & (Y >= 44)] = TEAM               # orange side panels
    neon(front & (np.abs(np.abs(X - cx) - 5.0) < 0.5) & (Y >= 44))        # neon seam between them
    seven = ((Y >= 45) & (Y <= 46) & (np.abs(X - cx) <= 2.5)) | \
            ((Y > 46) & (Y <= 51) & (np.abs(X - (cx + 1.8 - 0.6 * (Y - 46))) < 0.9))
    neon(front & seven)                                                   # glowing number 7
    m.col[abs_ & ((Y == 55) | (Y == 58))] = PLATE_D                       # plate seams
    m.col[abs_ & (np.abs(X - cx) < 0.6) & (Z > zc)] = PLATE_D
    m.col[chest & (Z < zc - 2) & (np.abs(X - cx) > 5.5) & (Y >= 44)] = TEAM   # orange back panels
    seven_b = ((Y >= 53) & (Y <= 54) & (np.abs(X - cx) <= 2.5)) | \
              ((Y > 54) & (Y <= 59) & (np.abs(X - (cx - 1.8 + 0.6 * (Y - 54))) < 0.9))   # mirrored: seen from behind
    neon(abs_ & (Z < zc - 2) & seven_b)
    m.put(slab(61, 63, 8.2, 6.0), PLATE_D, 'belt')
    neon(m.is_part('belt') & (Y == 62) & (Z > zc + 3) & (np.abs(X - cx) < 2.5))
    hips = m.put(slab(63, 70, lambda y: 8.0 - 0.12 * (y - 63), 5.8), SUIT, 'hips')
    m.col[hips & (np.abs(np.abs(X - cx) - 7.0) < 0.9)] = TEAM             # side stripes

    # --- 8. legs: thigh plates, angular knee pads, shin guards with neon strips, chunky boots
    for s in (-1, 1):
        lx = cx + 4.2 * s
        dz, dy = g.foot(s)
        at = lambda f: (lx, 66 + 18 * f + dy * f, zc + dz * f)
        kx, ky, kz = at(0.6)
        m.put(slab(int(round(ky - 2)), int(round(ky + 2)), 3.0, 2.6, cz=kz + 1.0, x0=kx), TEAM, 'knee')
        shin = m.put(m.cylinder(at(0.68), at(0.95), 3.0), SHELL, 'shin')
        neon(shin & (np.abs(X - lx) < 0.6) & (Z > zc + dz * 0.8 + 2))
        m.put(m.cylinder(at(0.08), at(0.5), 3.3), PLATE, 'thigh')
        m.put(m.capsule(at(0.0), at(1.0), 2.6), SUIT, 'legs')
        b = m.put(slab(int(round(83 + dy)), int(round(FEET + dy)) + 1, 3.5, 4.6, cz=zc + 1.4 + dz, x0=lx), SHELL, 'boots')
        m.col[b & (Y >= FEET - 1 + dy)] = TEAM_D
        neon(b & (Y == int(round(FEET - 2 + dy))) & (Z > zc + dz + 4))

    m.glow('neon')

    # --- 9. face paint: one skin tone on the plate, then the eyes
    for y in range(24, 42):
        for x in range(int(cx) - 9, int(cx) + 10):
            z = m.front_z(y, x)
            if z is not None and m.part[y, z, x] == m.pid('skin'):
                m.col[y, z, x] = SKIN_FACE
    m.paint_eyes(EYE, cx, 29, gap=1)
