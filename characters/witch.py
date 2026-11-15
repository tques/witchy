"""Red-haired witch: the reference character the house style was built on."""
import math
import numpy as np
from spritestack import hexc
from spritestack.gait import gait

NAME = 'witch'
TITLE = 'Witch Sprite Stack'
SPRITE = 'sprites/witch.png'   # 67x88 native grid
CENTER_X = 23.0                # body centre line (she was modelled at x=23 to leave room for the staff)

# palette (sampled from the sprite)
SKIN = (240, 208, 185); SKIN_FACE = (221, 199, 182)
HAIR = (200, 40, 55); HAIR_STRANDS = [(214, 52, 62), (190, 38, 52), (226, 78, 80)]
BANG, BANG_DARK = (205, 45, 60), (150, 25, 45)
HAT, HAT_TIP, HAT_BAND, BRIM = (92, 72, 168), (62, 48, 125), (120, 130, 205), (150, 130, 215)
ROBE, DRESS, DRESS_EDGE = (98, 78, 175), (170, 185, 235), (120, 128, 190)
GOLD, BELT, STAFF, ORB = (215, 160, 60), (170, 115, 55), (200, 140, 60), (205, 185, 255)
STOCK, BOOT, SLEEVE_IN = (80, 55, 140), (105, 75, 180), (45, 32, 85)

# animations use the toolkit presets (spritestack/gait.py); override any value here, e.g. dict(stride=8)
ANIMATIONS = {'walk': {}, 'run': {}}

# one eye, copied from the sprite, inner column first; mirrored for the other eye
EYE = [["251f48", "292048", "2b2046", "2b2046", "6a4a59"],
       ["2f2259", "33235d", "929cc1", "8591b4", "211d47"],
       ["32225a", "312257", "eaeaea", "dedce8", "231b40"],
       ["634294", "614192", "e7e6e9", "e6dbda", None],
       ["614192", "613f91", "e5e5e5", "e8dbd6", None]]


def build(m, sprite, pose=None):
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    cx = 23.0
    g = gait(pose)                    # all offsets are 0 when standing
    g.apply(m, pivot_y=88)            # body bob + running lean, pivoting at her feet
    tr = g.trail                      # 0 standing/walking, 1 running: hair and hat tip stream back
    staff_dz, staff_dy = g.prop_arm(1), g.arm_lift(1)   # she holds the staff in the screen-right hand

    # staff and orb, held out in her right hand
    oz, oy = zc + staff_dz, staff_dy
    m.put(m.ball((58, 44 + oy, oz + 5), 4.6), ORB, 'orb'); m.glow('orb')
    m.put(m.ell(58, 44 + oy, oz + 5, 6.3, 6.3, 3.2) & ~m.ell(58, 44 + oy, oz + 5, 4.8, 4.8, 6), GOLD, 'gold')
    m.put(m.capsule((32, 60 + oy, oz + 4), (53, 46 + oy, oz + 5), 1.3), STAFF, 'gold')

    # head with a flat face plate
    face_z = int(zc + 6)
    m.put(m.ell(cx, 31, zc + 1, 8.5, 8.5, 7.5) & (Z <= face_z), SKIN, 'skin')

    # hair: solid base, then a few strands curving off it
    m.put(m.ell(cx, 29.5, zc - 0.5, 10.5, 10.5, 9.5) & ~((Z > zc + 2) & (Y > 26) & (np.abs(X - cx) < 7.5)), HAIR, 'hair')
    m.put(m.ell(cx + 1, 42 - 2 * tr, zc - 4 - 2.5 * tr, 11, 13, 5.5) & (Y > 30), HAIR, 'hair')
    for sx in (cx - 9, cx + 9.5):
        m.put(m.capsule((sx, 30, zc + 1), (sx + (1.5 if sx > cx else -1.5), 47, zc - 1), 2.6), HAIR, 'hair')
    strands = [  # bangs (start under the brim, end above the eyes, one between them)
        *[((x0, 24.6, face_z - 0.5), (x0 + (xt - x0) * 0.4, 25.2, face_z + 2.6), (xt, yt, face_z + 1.2), r0, r1)
          for x0, xt, yt, r0, r1 in [(16, 14.8, 30.5, 3.0, 1.0), (19.5, 18.6, 28.0, 3.0, 0.9), (22.6, 23, 30.5, 2.2, 0.6),
                                     (26.5, 27.4, 28.1, 3.0, 0.9), (30, 31.5, 30.5, 3.0, 1.0)]],
        ((13, 32, zc + 1), (8, 37, zc + 2), (6.5, 32, zc + 1), 2.4, 0.8),     # side flicks
        ((33, 38, zc), (40, 44, zc), (43, 40, zc - 1), 2.4, 0.8),
        ((30, 48 - 2 * tr, zc - 5 - 2.5 * tr), (35, 53 - 4 * tr, zc - 5 - 5 * tr), (38, 50 - 5 * tr, zc - 4 - 7 * tr), 2.2, 0.7),
        ((16, 48 - 2 * tr, zc - 5 - 2.5 * tr), (12, 53 - 4 * tr, zc - 5 - 5 * tr), (9.5, 50 - 5 * tr, zc - 4 - 7 * tr), 2.2, 0.7)]
    for i, (p0, p1, p2, r0, r1) in enumerate(strands):
        m.put(m.strand(p0, p1, p2, r0, r1), HAIR_STRANDS[i % 3], 'hair')
    m.carve(m.is_part('hair') & (Y < 23))          # nothing pokes through the brim

    # hat: level brim, bent cone with a band, buckle
    m.brim(cx, zc, 21, 21, 19, BRIM, 'hat')
    cone = m.put(m.bent_cone(cx, zc, 21, 1, 12.2, 1.2, bend=(16, -4 - 5 * tr)), HAT, 'hat')
    m.col[cone & (Y <= 4)] = HAT_TIP
    m.col[cone & (Y >= 17)] = HAT_BAND
    m.put(m.ell(cx, 18.5, zc + 11, 2.2, 2.2, 1.5), GOLD, 'gold')

    # arms with flat cuffs
    parts = ('sleeve', 'gold', 'sleeve_in', 'skin')
    m.cuffed_arm((cx - 7, 42, zc), (cx - 11, 55 + g.arm_lift(-1), zc + 1 + g.arm(-1)), ROBE, GOLD, SKIN, SLEEVE_IN, parts)
    m.cuffed_arm((cx + 7, 42, zc), (cx + 12, 52 + staff_dy, zc + 3 + staff_dz), ROBE, GOLD, SKIN, SLEEVE_IN, parts)

    # collar, brooch, flared robe
    m.put(m.ell(cx, 40.5, zc, 6.5, 3, 5.5), ROBE, 'robe')
    m.put(m.ell(cx, 40, zc + 4, 2, 2, 1.5), GOLD, 'gold')
    rx = lambda y: 7.5 + 0.3 * (y - 41) if y <= 48 else 7.5 + 6.5 * ((y - 41) / 35.0) ** 1.3
    rz = lambda y: 5.5 if y <= 48 else 5.5 + 4.5 * ((y - 41) / 35.0) ** 1.3
    # each half of the skirt follows the leg under it, more toward the hem
    hem = lambda side: (lambda y: zc + g.hem(side)(y))
    m.put((m.lathe(cx, hem(-1), 41, 77, rx, rz) & (X < cx)) | (m.lathe(cx, hem(1), 41, 77, rx, rz) & (X >= cx)),
          ROBE, 'robe')

    # front opening: dress panel between flat gold stripes, belt, hem
    robe = m.is_part('robe')
    front = m.occ & robe & (Z > zc + 2)
    half = 1.2 + 0.09 * np.maximum(Y - 46, 0)
    panel = front & (np.abs(X - cx) <= half) & (Y > 44)
    m.col[panel] = DRESS
    m.col[front & (np.abs(np.abs(X - cx) - half - 1) < 0.9) & (Y > 44)] = GOLD
    m.col[robe & (Y >= 50) & (Y <= 52)] = BELT
    m.col[robe & (Y >= 74)] = GOLD
    m.recess_panel(panel, DRESS, range(45, 74), skip_rows=(50, 51, 52), edge_color=DRESS_EDGE)
    hrx, hrz = 7.5 + 6.5 + 0.9, 5.5 + 4.5 + 0.9      # raised hem band
    hem_z = np.where(X < cx, hem(-1)(74), hem(1)(74))
    m.put((((X - cx) / hrx) ** 2 + ((Z - hem_z) / hrz) ** 2 <= 1) & (Y >= 73) & (Y <= 75), GOLD, 'gold')

    # legs and boots
    for side in (-1, 1):
        lx = cx + 4 * side
        dz, dy = g.foot(side)                     # foot offset from the standing pose
        at = lambda f: (lx, 76 + 5 * f + dy * f, zc + dz * f)   # point f of the way down the leg
        m.put(m.capsule(at(0), at(1), 2.6), STOCK, 'legs')
        m.put(m.capsule(at(0.7), at(0.9), 3.1), GOLD, 'gold')
        m.put(m.ell(lx, 84.5 + dy, zc + 1.5 + dz, 3.4, 3.2, 4.6) & (Y <= 88), BOOT, 'legs')

    # face: skin tone and painted hairline on the face plate, then the sprite's eyes
    for y in range(22, 41):
        for x in range(int(cx) - 10, int(cx) + 11):
            z = m.front_z(y, x)
            if z is None or m.part[y, z, x] != m.pid('skin'):
                continue
            m.col[y, z, x] = SKIN_FACE
            dx = x - cx
            if y < 27.2 + 1.3 * abs(math.sin(dx * 0.9)) + (2.5 if abs(dx) > 6 else 0):
                m.col[y, z, x] = BANG if x % 3 else BANG_DARK
                m.col[y, z - 1, x] = m.col[y, z, x]
    m.paint_eyes(EYE, cx, 29)
