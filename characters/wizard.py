"""Old wizard: confused, wandering the field looking for his Looking Glass.
Designed directly in the house style (no source sprite): tall floppy hat, big white beard,
starry robe with wide sleeves, curly shoes. Same scale and proportions as the witch."""
import math
import numpy as np
from spritestack import hexc
from spritestack.gait import gait

NAME = 'wizard'
TITLE = 'Wizard Sprite Stack'
SPRITE = None
GRID = (72, 96, 48)
ANIMATIONS = {'walk': dict(stride=4.5, lift=2.2, arm=1.8)}     # an old man's shorter, gentler steps

SKIN, SKIN_FACE, NOSE = (236, 202, 178), (226, 194, 172), (232, 170, 160)
WHITE, WHITE_D = (240, 238, 232), (214, 212, 210)
HAT, HAT_D, ROBE, ROBE_IN = (58, 72, 168), (44, 54, 132), (72, 96, 196), (34, 40, 90)
GOLD, SHOE = (226, 182, 72), (122, 84, 58)

# small, kindly eyes (inner column first), lids heavy: he squints a lot without his Looking Glass
EYE = [["3b2f4f", "3b2f4f", "3b2f4f"],
       ["4c3f86", "f4f2ff", "2f2640"],
       ["4c3f86", "4c3f86", None]]


def build(m, sprite, pose=None):
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    cx, FEET = 36.0, 91
    g = gait(pose)
    g.apply(m, pivot_y=FEET)
    face_z = int(zc + 6)

    # --- head with flat face plate, eyes later
    m.put(m.ell(cx, 32, zc + 1, 8.5, 8.5, 7.5) & (Z <= face_z), SKIN, 'skin')
    # bushy brows and moustache (in front of the face plate)
    for s in (-1, 1):
        m.put(m.strand((cx + s * 1.5, 28.6, face_z + 0.8), (cx + s * 4.5, 27.6, face_z + 1.6), (cx + s * 7.5, 29.6, face_z + 0.6), 1.5, 0.8), WHITE, 'beard')
        m.put(m.strand((cx, 36.6, face_z + 1.6), (cx + s * 4, 36.2, face_z + 2.4), (cx + s * 7.5, 38.5, face_z + 1.2), 1.9, 0.9), WHITE, 'beard')
    m.put(m.ball((cx, 34.6, face_z + 1.4), 1.9), NOSE, 'nose')
    # beard: a big soft wedge over the chest ending in a point
    beard = m.ell(cx, 44, zc + 5, 8.2, 10.5, 4.6) & (Y > 35)
    m.put(beard, WHITE, 'beard')
    m.put(m.strand((cx, 50, zc + 6), (cx + 1.5, 56, zc + 7), (cx + 3, 60, zc + 6.5), 4.5, 0.8), WHITE, 'beard')
    # side and back hair under the hat
    m.put(m.ell(cx, 30, zc - 2.5, 10.2, 8, 8.5) & ~((Z > zc + 2) & (np.abs(X - cx) < 8)) & (Y > 24), WHITE, 'hair')

    m.carve((m.is_part('hair') | m.is_part('beard')) & (Y < 25))      # nothing pokes through the brim
    # --- hat: smallish level brim, tall cone flopping over to one side, gold band and moon
    m.brim(cx, zc, 23, 15.5, 13.5, HAT_D, 'hat')
    cone = m.put(m.bent_cone(cx, zc, 23, 0, 10.4, 1.4, bend=(13, -7), power=(2.6, 1.6)), HAT, 'hat')
    m.col[cone & (Y >= 19)] = GOLD
    rng = np.random.default_rng(3)
    stars = cone & (Y < 18) & (rng.random(cone.shape) < 0.035)
    m.col[stars] = GOLD
    m.put(m.ell(cx, 14, zc + 8.2, 2.2, 2.6, 1.2) & ~m.ell(cx + 1.2, 13.4, zc + 9, 1.8, 2.2, 1.6), GOLD, 'gold')   # crescent moon

    # --- arms: wide sleeves with gold cuffs
    parts = ('sleeve', 'gold', 'sleeve_in', 'skin')
    for s in (-1, 1):
        m.cuffed_arm((cx + 7.5 * s, 43, zc), (cx + 11 * s, 55 + g.arm_lift(s), zc + 1 + g.arm(s)), ROBE, GOLD, SKIN, ROBE_IN, parts,
                     sleeve_r=3.6, cuff_r=4.2, open_r=2.8)

    # --- robe: flared lathe with a raised gold hem and scattered stars
    rx = lambda y: 7.8 + 6.2 * ((y - 40) / 40) ** 1.2
    rz = lambda y: 5.8 + 4.4 * ((y - 40) / 40) ** 1.2
    hem = lambda side: (lambda y: zc + g.hem(side)(y + 2))
    robe = (m.lathe(cx, hem(-1), 40, 81, rx, rz) & (X < cx)) | (m.lathe(cx, hem(1), 40, 81, rx, rz) & (X >= cx))
    placed = m.put(robe, ROBE, 'robe')
    m.col[placed & (rng.random(placed.shape) < 0.03) & (Y < 76)] = GOLD
    hz = np.where(X < cx, hem(-1)(78), hem(1)(78))
    m.put((((X - cx) / (rx(80) + 0.9)) ** 2 + ((Z - hz) / (rz(80) + 0.9)) ** 2 <= 1) & (Y >= 77) & (Y <= 79), GOLD, 'gold')

    # --- legs and curly shoes
    for s in (-1, 1):
        lx = cx + 3.8 * s
        dz, dy = g.foot(s)
        m.put(m.capsule((lx, 80, zc), (lx, 85 + dy, zc + dz), 2.4), ROBE_IN, 'legs')
        m.put(m.ell(lx, 88 + dy, zc + 1.5 + dz, 3.2, 3.0, 4.4) & (Y <= FEET + 1), SHOE, 'shoe')
        m.put(m.strand((lx, 88 + dy, zc + 5 + dz), (lx, 89 + dy, zc + 8.5 + dz), (lx, 85.5 + dy, zc + 9 + dz), 1.6, 0.6), SHOE, 'shoe')

    # --- face paint: skin tone on the plate, then the eyes
    for y in range(22, 42):
        for x in range(int(cx) - 9, int(cx) + 10):
            z = m.front_z(y, x)
            if z is not None and m.part[y, z, x] == m.pid('skin'):
                m.col[y, z, x] = SKIN_FACE
    m.paint_eyes(EYE, cx, 30, gap=2)
