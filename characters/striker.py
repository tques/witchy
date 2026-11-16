"""Striker: an alien warrior who plays grav-ball, a futuristic armoured football.
Designed directly in the house style (no source sprite): green-skinned alien with big amber
eyes and small tusks, a horned helmet with a tall crest, heavy shoulder pads, a chest plate
with a glowing chevron, armoured greaves and cleated boots, carrying a glowing plasma ball.
Same scale and proportions as the witch."""
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
TUSK = (238, 230, 206)
ARMOR, ARMOR_D = (178, 44, 52), (132, 30, 42)            # team crimson
METAL, METAL_D = (186, 192, 208), (120, 126, 146)        # silver plating
SUIT, SUIT_IN = (44, 40, 66), (22, 18, 36)               # dark under-suit
CREST, CREST_D = (236, 178, 58), (196, 128, 36)          # gold crest
PLASMA, CHEVRON = (120, 236, 255), (110, 226, 250)

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
    tr = g.trail
    face_z = int(zc + 6)
    ball_dz, ball_dy = g.prop_arm(1), g.arm_lift(1)

    # --- 1. prop: the plasma ball, tucked in his screen-right hand, with silver end caps
    bx, by, bz = cx + 15.5, 56 + ball_dy, zc + 4 + ball_dz
    for s in (-1, 1):
        m.put(m.ell(bx + s * 4.2, by, bz, 1.6, 2.2, 2.2), METAL, 'metal')
    m.put(m.ell(bx, by, bz, 5.6, 3.6, 3.6), PLASMA, 'plasma'); m.glow('plasma')
    m.col[m.is_part('plasma') & (np.abs(X - bx) < 0.6)] = (230, 255, 255)   # seam band

    # --- 2. head with flat face plate
    m.put(m.ell(cx, 32, zc + 1, 8.5, 8.5, 7.5) & (Z <= face_z), SKIN, 'skin')
    # small tusks at the jaw corners
    for s in (-1, 1):
        m.put(m.strand((cx + s * 4.5, 37.5, face_z - 0.5), (cx + s * 5.5, 40, face_z + 1.0), (cx + s * 4.8, 38.6, face_z + 2.2), 1.2, 0.5),
              TUSK, 'tusk')

    # --- 3. helmet: shell open at the face, cheek guards, horns and a tall crest
    shell = m.ell(cx, 30, zc - 0.5, 10.4, 10.2, 9.4) & ~((Z > zc + 1) & (Y > 26.5) & (np.abs(X - cx) < 7.2))
    shell &= Y < 39
    helm = m.put(shell, ARMOR, 'helm')
    m.col[helm & (Y >= 24) & (Y <= 25)] = METAL                           # flat silver band
    m.col[helm & (Y < 24) & (np.abs(X - cx) < 1.6) & (Z > zc)] = METAL     # brow ridge stripe
    for s in (-1, 1):                                                     # cheek guards
        m.put(m.ell(cx + s * 8.6, 33, zc + 2.5, 2.4, 5.5, 4.2), METAL, 'metal')
        m.put(m.strand((cx + s * 9.5, 23, zc + 1), (cx + s * 15, 22, zc + 1), (cx + s * 16, 15, zc + 0.5), 2.2, 0.7),
              METAL, 'metal')                                             # curved horns
    crest = m.membrane((cx, 22, zc + 7), 90,
                       [(8, -4, 9.5, 6.5, -8), (15 + 2 * tr, -2 + tr, 6, 4.5, -20)], thickness=2.4)
    cm = crest['mask'] & (Y < 24)
    m.put(cm, CREST, 'crest')
    m.col[cm & (crest['rr'] > 0.80)] = CREST_D
    m.smooth_surface(cm, 'crest', crest['normal'], two_sided=True)

    # --- 4. shoulder pads (gridiron pads, warrior pauldrons) with silver rims
    for s in (-1, 1):
        px = cx + s * 9.5
        pad = m.ell(px, 42, zc, 6.0, 4.2, 6.2) & (Y <= 44)
        m.put(m.ell(px, 42.5, zc, 6.8, 4.2, 6.9) & (Y >= 44) & (Y <= 45), METAL, 'metal')
        p = m.put(pad, ARMOR, 'pads')
        m.col[p & (np.abs(X - (px + s * 1.5)) < 0.7)] = METAL_D           # flat ridge stripe

    # --- 5. arms: dark suit sleeves, silver gauntlet cuffs, green hands
    parts = ('sleeve', 'metal', 'sleeve_in', 'skin')
    m.cuffed_arm((cx - 9, 44, zc), (cx - 13, 54 + g.arm_lift(-1), zc + 1 + g.arm(-1)), SUIT, METAL, SKIN, SUIT_IN, parts,
                 sleeve_r=3.0, cuff_r=3.9, open_r=2.5, hand_r=2.5)
    m.cuffed_arm((cx + 9, 44, zc), (cx + 12, 51 + ball_dy, zc + 2.5 + ball_dz), SUIT, METAL, SKIN, SUIT_IN, parts,
                 sleeve_r=3.0, cuff_r=3.9, open_r=2.5, hand_r=2.5)

    # --- 6. back: a power pack with two glowing vents between the shoulder pads
    pack = m.put(m.ell(cx, 46, zc - 6.5, 5.0, 3.6, 2.6), METAL_D, 'pack')
    for s in (-1, 1):
        m.put(m.cylinder((cx + 2.4 * s, 44, zc - 8.7), (cx + 2.4 * s, 48, zc - 8.7), 1.0), PLASMA, 'vent')
    m.glow('vent')

    # --- torso: chest plate over the suit, belt, shorts
    m.put(m.ell(cx, 41, zc, 5.5, 2.5, 5), SUIT, 'suit')                   # neck seal
    rx = lambda y: 9.2 - 0.12 * max(0, y - 46)
    rz = lambda y: 6.4 - 0.06 * max(0, y - 46)
    chest = m.put(m.lathe(cx, zc, 42, 61, rx, rz), ARMOR, 'chest')
    front = chest & (Z > zc + 2)
    # glowing chevron on the chest
    v = front & (np.abs((Y - 46) - 0.8 * np.abs(X - cx)) < 1.1) & (np.abs(X - cx) < 6)
    m.col[v] = CHEVRON; m.part[v] = m.pid('chevron'); m.glow('chevron')
    # abdomen panel recessed between flat silver trim
    panel = front & (np.abs(X - cx) <= 3.2) & (Y >= 53) & (Y <= 58)
    m.col[front & (np.abs(np.abs(X - cx) - 4.2) < 0.7) & (Y >= 52) & (Y <= 59)] = METAL
    m.col[panel] = ARMOR_D
    m.recess_panel(panel, ARMOR_D, range(53, 59), edge_color=SUIT_IN)
    # team number 7 on the back, flat silver
    back = chest & (Z < zc - 2)
    seven = ((Y >= 52) & (Y <= 53) & (np.abs(X - cx) <= 3)) | \
            ((Y > 53) & (Y <= 59) & (np.abs(X - (cx + 2.5 - 0.6 * (Y - 53))) < 1.0))
    m.col[back & seven] = METAL
    m.put(m.lathe(cx, zc, 61, 64, lambda y: 8.4, lambda y: 6.0), METAL_D, 'belt')
    m.put(m.ell(cx, 62.5, zc + 6, 2.0, 1.6, 1), PLASMA, 'buckle'); m.glow('buckle')
    m.put((m.lathe(cx, zc, 64, 71, lambda y: 8.0 - 0.1 * (y - 64), lambda y: 5.8) & (Y < 71)), SUIT, 'shorts')

    # --- 7. legs: armoured thigh plates, knee guards, silver greaves, cleated boots
    for s in (-1, 1):
        lx = cx + 4.2 * s
        dz, dy = g.foot(s)
        at = lambda f: (lx, 66 + 18 * f + dy * f, zc + dz * f)
        m.put(m.ball(at(0.62), 2.9), METAL, 'metal')                      # knee guard
        m.put(m.cylinder(at(0.68), at(0.92), 3.1), METAL, 'metal')         # greave
        m.put(m.capsule(at(0.05), at(0.5), 3.4), ARMOR, 'legs')            # thigh plate
        m.put(m.capsule(at(0.0), at(1.0), 2.6), SUIT, 'legs')
        boot = m.ell(lx, 85 + dy, zc + 1.5 + dz, 3.6, 3.2, 4.8) & (Y <= FEET - 1 + dy)
        m.put(boot, SUIT_IN, 'boots')
        m.col[m.is_part('boots') & (Y < 84 + dy)] = ARMOR_D
        sole = m.ell(lx, FEET - 1 + dy, zc + 1.5 + dz, 3.6, 1.2, 4.8) & (Y >= FEET - 1 + dy) & (Y <= FEET + dy)
        m.put(sole, METAL_D, 'cleats')

    # --- 8. face paint: one skin tone on the plate, then the eyes
    for y in range(24, 42):
        for x in range(int(cx) - 9, int(cx) + 10):
            z = m.front_z(y, x)
            if z is not None and m.part[y, z, x] == m.pid('skin'):
                m.col[y, z, x] = SKIN_FACE
    m.paint_eyes(EYE, cx, 29, gap=1)
