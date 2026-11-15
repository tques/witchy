"""TEMPLATE: copy with  python tools/new_character.py NAME  (don't edit this file directly).

Work from sprites/NAME_grid.png: every number below is a sprite-pixel coordinate
(x right, y down) read off that grid. z is depth: m.zc is the centre, +z toward the viewer.
Rebuild and look:  python -m spritestack.build characters/NAME.py --quick --views 0,35,90,180

Build order matters: earlier put() calls win, so add props, face and hair before the body.
See STYLE_GUIDE.md for the rules every character follows.
"""
import math
import numpy as np
from spritestack import hexc
from spritestack.gait import gait

NAME = '__NAME__'
TITLE = '__NAME__'
SPRITE = 'sprites/__NAME__.png'
# GRID = (72, 90, 48)    # only if the sprite is bigger than ~70 x 88
# CENTER_X = 23.0        # body centre line, if the body isn't modelled at the middle of the box
# ANIMATIONS = {'walk': {}, 'run': {}}   # toolkit presets; see characters/witch.py and spritestack/gait.py

# ---- palette: pick from sprites/NAME_palette.txt ---------------------------------------------
SKIN, SKIN_FACE = (240, 208, 185), (221, 199, 182)
HAIR, HAIR_STRANDS = (200, 40, 55), [(214, 52, 62), (190, 38, 52), (226, 78, 80)]
TOP, TOP_IN, TRIM, PANT, SHOE = (98, 78, 175), (45, 32, 85), (215, 160, 60), (80, 55, 140), (105, 75, 180)

# ---- one eye from the sprite, inner column first --------------------------------------------
# get the colours with:  python tools/prep_sprite.py sprites/NAME.png x --dump x0,y0,x1,y1
# use None for skin pixels inside the box
EYE = [["251f48", "292048", "2b2046", "2b2046"],
       ["2f2259", "33235d", "929cc1", "8591b4"],
       ["32225a", "312257", "eaeaea", "dedce8"],
       ["634294", "614192", "e7e6e9", "e6dbda"]]

# ---- proportions (sprite coordinates) --------------------------------------------------------
CX = 23.0                 # body centre line
HEAD_Y, HEAD_R = 31, 8.5  # head centre row and radius
EYE_TOP = 29              # first row of the eyes
NECK_Y, WAIST_Y, HEM_Y = 41, 51, 76
FEET_Y = 87


def build(m, sprite, pose=None):        # pose: None = standing, else {'anim', 't' 0..1, 'frame'}
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    g = gait(pose)                    # every offset is 0 when standing
    g.apply(m, pivot_y=FEET_Y)        # bob + lean when walking/running
    face_z = int(zc + 1 + 5)          # flat face plate (style.FACE_PLATE in front of the head centre)

    # 1. props (weapons, staffs, orbs) -------------------------------------------------------
    # m.put(m.capsule((x0, y0, zc + 4), (x1, y1, zc + 4), 1.3), TRIM, 'trim')
    # m.put(m.ball((x, y, zc + 5), 4.5), (205, 185, 255), 'orb'); m.glow('orb')

    # 2. head with flat face plate -----------------------------------------------------------
    m.put(m.ell(CX, HEAD_Y, zc + 1, HEAD_R, HEAD_R, HEAD_R - 1) & (Z <= face_z), SKIN, 'skin')

    # 3. hair: solid base + a FEW strands (bangs, 1-2 curling locks) ---------------------------
    m.put(m.ell(CX, HEAD_Y - 1.5, zc - 0.5, HEAD_R + 2, HEAD_R + 2, HEAD_R + 1)
          & ~((Z > zc + 2) & (Y > HEAD_Y - 5) & (np.abs(X - CX) < HEAD_R - 1)), HAIR, 'hair')
    bangs = [(-6.5, -7.5, 0.5), (-3, -4, -1.5), (0.5, 0.5, 0.5), (3.5, 4.5, -1.5), (7, 8.5, 0.5)]
    for i, (dx0, dxt, dyt) in enumerate(bangs):
        p0 = (CX + dx0, HEAD_Y - 6.4, face_z - 0.5)
        p2 = (CX + dxt, EYE_TOP + dyt, face_z + 1.2)
        p1 = (p0[0] + (p2[0] - p0[0]) * 0.4, HEAD_Y - 5.8, face_z + 2.6)
        m.put(m.strand(p0, p1, p2, 3.0, 0.9), HAIR_STRANDS[i % 3], 'hair')

    # 4. arms with flat cuffs (sleeve end = cuff position) --------------------------------------
    parts = ('sleeve', 'trim', 'sleeve_in', 'skin')
    for side in (-1, 1):
        m.cuffed_arm((CX + 7 * side, NECK_Y + 1, zc), (CX + 10 * side, WAIST_Y + 4 + g.arm_lift(side), zc + 1 + g.arm(side)),
                     TOP, TRIM, SKIN, TOP_IN, parts)

    # 5. body: lathe = stacked ellipses, radius as a function of the row -----------------------
    m.put(m.ell(CX, NECK_Y - 0.5, zc, 6.5, 3, 5.5), TOP, 'body')
    m.put(m.lathe(CX, zc, NECK_Y, HEM_Y, lambda y: 7.5 + 0.12 * (y - NECK_Y), lambda y: 5.5 + 0.08 * (y - NECK_Y)),
          TOP, 'body')
    # trim: keep it flat (recolour), push panels between trims in with m.recess_panel(...)

    # 6. legs and shoes ----------------------------------------------------------------------
    for side in (-1, 1):
        lx = CX + 4 * side
        dz, dy = g.foot(side)
        m.put(m.capsule((lx, HEM_Y, zc), (lx, FEET_Y - 5 + dy, zc + dz), 2.6), PANT, 'legs')
        m.put(m.ell(lx, FEET_Y - 2.5 + dy, zc + 1.5 + dz, 3.4, 3.2, 4.6) & (Y <= FEET_Y + 1), SHOE, 'legs')

    # 7. face paint last: skin tone on the plate, then the sprite's eyes ----------------------
    for y in range(int(HEAD_Y - HEAD_R), int(HEAD_Y + HEAD_R) + 1):
        for x in range(int(CX - HEAD_R), int(CX + HEAD_R) + 1):
            z = m.front_z(y, x)
            if z is not None and m.part[y, z, x] == m.pid('skin'):
                m.col[y, z, x] = SKIN_FACE
    m.paint_eyes(EYE, CX, EYE_TOP)
