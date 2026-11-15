"""Winged forest fairy: green fluffy hair, glowing antennae, flower, leaf dress, two pairs of wings."""
import math
import numpy as np
from spritestack import hexc

NAME = 'fairy'
TITLE = 'Fairy Sprite Stack'
SPRITE = 'sprites/fairy.png'      # 55x69 native grid
GRID = (72, 74, 48)               # same scale as the witch; she is just smaller

# sprite (x, y) -> model: centre her in the box, small top margin for the antenna bulbs
OX, OY = 17, 3

# palette (sampled from the sprite)
SKIN, SKIN_FACE = (238, 212, 200), (232, 207, 195)
HAIR = (150, 200, 140); HAIR_STRANDS = [(150, 200, 135), (118, 172, 125), (175, 214, 148)]
HAIR_DARK = (96, 140, 118)
DRESS, DRESS_LIGHT, DRESS_DARK = (126, 181, 131), (187, 220, 152), (96, 146, 112)
WHITE, PANEL_EDGE = (242, 237, 223), (200, 196, 190)
UNDERSKIRT = (200, 190, 228)
GOLD, BULB, BULB_RIM, STEM = (232, 180, 60), (250, 238, 170), (190, 135, 80), (110, 165, 115)
PETAL, PETAL_EDGE, FLOWER_MID = (232, 220, 240), (190, 170, 220), (240, 190, 60)
WING, WING_LIGHT, WING_BLUE, WING_RIM, WING_RIM_DARK = (185, 186, 219), (220, 222, 245), (158, 175, 210), (159, 136, 184), (120, 95, 150)

# one eye from the sprite (x18..22, y23..26), inner column first
EYE = [["2f2c58", "2f265d", "2c205a", "33205b", "8c5c6a"],
       ["342469", "36296d", "b6c4dd", "bac6dd", "2c1f5c"],
       ["5a3d90", "5e3e94", "eaeceb", "eceae8", None],
       ["63449e", "67449d", "eaeaea", "ebe6e6", None]]


def build(m, sprite):
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    cx = 19 + OX                       # face centre line
    y = lambda sy: sy + OY             # sprite row -> model row

    # ---- antennae with glowing bulbs (thin tubes are fine; they are not flat) -----------------
    for root, ctrl, tip in [((cx - 3, y(13), zc + 1), (cx - 6, y(2), zc + 2), (cx - 12, y(4), zc + 2)),
                            ((cx + 3, y(13), zc + 1), (cx + 5, y(5), zc + 2), (cx + 9, y(8), zc + 2))]:
        m.put(m.ball(tip, 2.3), BULB, 'bulb')
        m.put(m.ball((tip[0] - 0.8, tip[1] + 0.8, tip[2] - 0.8), 2.3), BULB_RIM, 'bulb_rim')
        m.put(m.strand(root, ctrl, tip, 0.9, 0.7), STEM, 'stem')
    m.glow('bulb')

    # ---- flower tucked in her hair (front right) ----------------------------------------------
    fc = np.array([cx + 9.5, y(17), zc + 7.5])
    m.put(m.ball(fc + (0, 0, 0.8), 1.3), FLOWER_MID, 'flower_mid')
    for i in range(5):
        a = math.radians(90 + 72 * i)
        pc = fc + (2.4 * math.cos(a), -2.4 * math.sin(a), 0)
        m.put(m.ell(*pc, 2.1, 2.1, 1.0), PETAL, 'petal')

    # ---- head with flat face plate ------------------------------------------------------------
    hy = y(25)
    face_z = int(zc + 6)
    m.put(m.ell(cx, hy, zc + 1, 8.0, 8.0, 7.2) & (Z <= face_z), SKIN, 'skin')

    # ---- hair: big fluffy solid base + a few chunky strands ------------------------------------
    strands = [  # bangs over the forehead, ending above the eyes (one between them)
        *[((cx + dx0, y(15.5), face_z - 0.5), (cx + dx0 + (dxt - dx0) * 0.4, y(16.5), face_z + 2.6),
           (cx + dxt, y(yt), face_z + 1.2), r0, r1)
          for dx0, dxt, yt, r0, r1 in [(-6.5, -7.5, 25, 3.0, 1.0), (-3, -3.8, 22.2, 3.0, 0.9), (0.4, 0.6, 24.5, 2.1, 0.6),
                                       (3.6, 4.4, 22.2, 3.0, 0.9), (7, 8.2, 25, 3.0, 1.0)]],
        # spiky tufts flicking out at the sides and top, like the sprite's fluffy outline
        ((cx - 9, y(22), zc + 1), (cx - 13, y(20), zc + 1), (cx - 14.5, y(16), zc), 2.4, 0.7),
        ((cx + 9, y(27), zc + 1), (cx + 13, y(30), zc + 1), (cx + 15, y(27), zc), 2.4, 0.7),
        ((cx - 4, y(14), zc - 1), (cx - 7, y(9), zc - 1), (cx - 9, y(10), zc - 2), 2.2, 0.6),
        ((cx - 9, y(31), zc - 2), (cx - 12, y(35), zc - 2), (cx - 13, y(33), zc - 3), 2.2, 0.6),
        # tufts at the back of the hair curling outward, so the back view has shape
        ((cx - 3, y(32), zc - 7), (cx - 8, y(37), zc - 8), (cx - 10, y(33.5), zc - 7.5), 2.6, 0.7),
        ((cx + 3, y(32), zc - 7), (cx + 8, y(37), zc - 8), (cx + 10, y(33.5), zc - 7.5), 2.6, 0.7),
        ((cx, y(16), zc - 8), (cx + 1, y(12), zc - 10), (cx + 4, y(13), zc - 11), 2.4, 0.7)]
    for i, (p0, p1, p2, r0, r1) in enumerate(strands):
        m.put(m.strand(p0, p1, p2, r0, r1), HAIR_STRANDS[i % 3], 'hair')
    m.put(m.ell(cx, hy - 3, zc - 0.5, 11, 11, 10) & ~((Z > zc + 2) & (Y > hy - 6) & (np.abs(X - cx) < 7)), HAIR, 'hair')
    m.put(m.ell(cx, y(29), zc - 3, 9.8, 7.5, 6.5), HAIR, 'hair')       # short back mass
    for sx in (cx - 8.5, cx + 8.5):                                                         # side locks
        m.put(m.capsule((sx, y(24), zc + 1.5), (sx + (1.2 if sx > cx else -1.2), y(33), zc + 0.5), 2.6), HAIR, 'hair')

    # ---- arms: puff sleeves, bare arms reaching out, light wrist bands, hands -------------------
    for side in (-1, 1):
        sh = (cx + side * 6, y(36), zc)
        wr = (cx + side * 10.5, y(43), zc + 2)
        m.put(m.ball(sh, 2.8), DRESS, 'dress')
        m.put(m.cylinder((wr[0] - side * 0.5, wr[1] - 0.6, wr[2]), (wr[0] + side * 0.3, wr[1] + 0.3, wr[2]), 1.9), WHITE, 'cuff')
        m.put(m.ball((cx + side * 11.6, y(44.5), zc + 2.3), 2.0), SKIN, 'skin')
        m.put(m.capsule(sh, wr, 1.6), SKIN, 'skin')

    # ---- collar, pendant ----------------------------------------------------------------------
    m.put(m.ell(cx, y(35), zc + 4.6, 1.6, 1.6, 1.2), GOLD, 'gold')
    m.put(m.ell(cx, y(33.5), zc, 5.5, 1.6, 4.6), WHITE, 'collar')

    # ---- bodice and leaf skirt with pointed hem ----------------------------------------------
    m.put(m.lathe(cx, zc, y(34), y(45), lambda yy: 5.0 + 0.05 * (yy - y(34)), lambda yy: 4.0), DRESS, 'dress')
    ang = np.arctan2(X - cx, Z - zc)                          # 0 = front
    tri = 1 - np.abs(((ang / (2 * np.pi) * 5 + 0.5) % 1) * 2 - 1)   # 5 leaf points, one at the front
    t = lambda yy: (yy - y(44)) / 9.0
    skirt = m.lathe(cx, zc, y(44), y(55), lambda yy: 5.2 + 6.0 * t(yy) ** 0.9, lambda yy: 4.2 + 4.6 * t(yy) ** 0.9)
    leaf = skirt & (Y <= y(49.5) + 4.5 * tri)
    placed = m.put(leaf, DRESS, 'dress')
    m.col[placed & (Y >= y(49.5) + 4.5 * tri - 2)] = DRESS_LIGHT          # lighter leaf tips
    under = m.lathe(cx, zc, y(46), y(52), lambda yy: 5.0 + 4.6 * ((yy - y(46)) / 6.0), lambda yy: 4.1 + 3.6 * ((yy - y(46)) / 6.0))
    m.put(under, UNDERSKIRT, 'dress')                         # shows between the leaf points

    # white front panel, pushed in one cube (style: panels recessed, trim flat)
    dress = m.is_part('dress')
    panel = m.occ & dress & (Z > zc + 2) & (np.abs(X - cx) <= 1.3) & (Y >= y(37)) & (Y <= y(44))
    m.col[panel] = WHITE
    m.recess_panel(panel, WHITE, range(y(37), y(45)), edge_color=PANEL_EDGE)

    # ---- legs and leaf boots with white cuffs, toes pointing down (floating) -------------------
    for side in (-1, 1):
        lx = cx + side * 2.3
        m.put(m.cylinder((lx, y(60.3), zc + 0.3), (lx, y(61.6), zc + 0.3), 2.5), WHITE, 'cuff')
        m.put(m.ell(lx, y(63.5), zc + 0.8, 2.4, 3.2, 2.8), DRESS, 'boot')
        m.put(m.strand((lx, y(64.5), zc + 1.5), (lx, y(67.5), zc + 3), (lx, y(67), zc + 5.5), 1.8, 0.5), DRESS_DARK, 'boot')
        m.put(m.capsule((lx, y(51), zc), (lx, y(61), zc + 0.3), 2.0), SKIN, 'skin')

    # ---- wings: two pairs of vertical membranes angled back from the shoulder blades -----------
    for side in (-1, 1):
        root = (cx + side * 1.5, y(37), zc - 3.5)
        yaw = 30 if side > 0 else 150                         # out to each side, swept 30 deg back
        for ellipses in ([(15, -13, 16, 11, -38)],               # big upper wing
                         [(9.5, 7, 10, 6.2, 32)]):               # small lower wing
            w = m.membrane(root, yaw, ellipses, thickness=2.0)
            placed = m.put(w['mask'], WING, 'wing')
            band = ((w['u'] * 0.55 - w['v'] * 0.45) % 5.5) < 1.6                # light diagonal bands
            m.col[placed & band] = WING_LIGHT
            m.col[placed & (w['u'] < 5)] = WING_BLUE                            # bluer near the body
            m.col[placed & (w['rr'] > 0.80)] = WING_RIM
            m.col[placed & (w['rr'] > 0.92)] = WING_RIM_DARK
            m.smooth_surface(placed, 'wing', w['normal'], two_sided=True)

    # ---- face paint last: skin tone on the plate, then the sprite's eyes -----------------------
    for yy in range(int(hy - 8), int(hy + 9)):
        for xx in range(int(cx - 8), int(cx + 9)):
            zf = m.front_z(yy, xx)
            if zf is not None and m.part[yy, zf, xx] == m.pid('skin'):
                m.col[yy, zf, xx] = SKIN_FACE
    m.paint_eyes(EYE, cx, y(23))
