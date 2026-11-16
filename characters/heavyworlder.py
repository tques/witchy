"""Heavyworlder (Uvo Tesh): grav-ball lineman from a high-gravity foundry world.
Designed directly in the house style (no source sprite). Short, wide and dense: a head sunk low
between oversized shoulder guards, a thick neck, huge bare forearms and fists, short heavy legs.
Slate skin, a wild ash-white mane, small deep-set eyes under a heavy brow, a teal team jersey
with steel harness straps, and a steel grav-brace belt with amber lights and struts down the legs.

Animations:
  idle      the planted stance, breathing (chest, shoulders and head rise a layer) with a blink
  run_ball  power run carrying the ball tucked under the right arm: short strides that land hard,
            low and leaning in, the free fist pumping
With pose=None the build is the standing stance exactly (idle frame 0)."""
import math
import numpy as np
from spritestack import hexc
from spritestack.gait import gait, PRESETS

NAME = 'heavyworlder'
TITLE = 'Heavyworlder Sprite Stack'
SPRITE = None
GRID = (72, 90, 56)          # deeper box: the run leans in and the ball reaches forward
ANIMATIONS = {
    'idle': dict(frames=8, fps=6, speed=0.0, loop=True),
    'run_ball': dict(PRESETS['run'], fps=14, stride=5.5, lift=3.0, kick=1.5, arm=3.0, prop_arm=1.0,
                     arm_raise=1.0, lean=0.11, trail=0.8),
}

SKIN, SKIN_FACE, SKIN_D = (104, 114, 132), (96, 106, 124), (78, 86, 104)     # slate
HAIR, HAIR_STRANDS = (196, 190, 176), [(214, 208, 192), (186, 178, 164), (226, 220, 206)]
TEAM, TEAM_D = (34, 116, 118), (24, 84, 88)              # foundry teal jersey
STEEL, STEEL_D = (150, 156, 170), (92, 96, 112)
STRAP = (52, 50, 60)
SHORTS, BOOT, SOLE = (40, 42, 54), (58, 56, 66), (30, 28, 36)
AMBER = (255, 176, 48)
BALL, BALL_SEAM = (120, 92, 70), (110, 232, 255)

# small deep-set eyes, pale ice iris with a dark pupil (inner column first, mirrored)
EYE = [["1c2030", "1c2030", "1c2030"],
       ["6fb6cc", "e8fbff", "1c2030"],
       ["6fb6cc", "1a2236", "6fb6cc"]]
EYE_SHUT = [["1c2030", "1c2030", "1c2030"],
            [None, None, None],
            [None, None, None]]

CX, FEET, HY = 36.0, 88, 38      # body centre line, sole row, head centre row


def build(m, sprite, pose=None):
    X, Y, Z, zc = m.X, m.Y, m.Z, m.zc
    cx = CX
    anim = (pose or {}).get('anim')
    g = gait(pose if anim not in (None, 'idle') else None)
    g.apply(m, pivot_y=FEET)
    running = anim == 'run_ball'
    tr = g.trail

    # idle: breathe in over half the loop (upper body up one layer), blink once
    t = (pose or {}).get('t', 0.0)
    up = 1 if anim == 'idle' and math.sin(2 * math.pi * t) > 0.3 else 0
    blink = anim == 'idle' and (pose or {}).get('frame') == 6
    hy = HY - up
    face_z = int(zc + 1 + 5)

    def slab(y0, y1, a, b, cz=zc, x0=cx, n=4.0):
        """Rounded-square layers (superellipse) for machined parts; a, b may vary by row."""
        out = np.zeros(m.occ.shape, bool)
        for y in range(max(int(round(y0)), 0), min(int(round(y1)), m.H)):
            ay, by_ = (a(y) if callable(a) else a), (b(y) if callable(b) else b)
            out[y] = (np.abs(X[y] - x0) / ay) ** n + (np.abs(Z[y] - cz) / by_) ** n <= 1
        return out

    def amber(mask):
        m.col[mask] = AMBER
        m.part[mask] = m.pid('amber')

    # --- 1. prop: the ball, tucked under the right arm (run only)
    if running:
        bdz, bdy = g.prop_arm(1), g.arm_lift(1)
        bx, by, bz = cx + 9.5, 56.5 + bdy, zc + 13 + bdz
        ball = m.put(m.ell(bx, by, bz, 4.4, 4.4, 6.6), BALL, 'ball')
        seam = ball & ((np.abs(X - bx) < 0.6) | (np.abs(np.abs(Z - bz) - 2.8) < 0.5) | (np.abs(Z - bz) > 5.6))
        m.col[seam] = BALL_SEAM; m.part[seam] = m.pid('seam'); m.glow('seam')

    # --- 2. head: heavy scowling brow, wide jaw, flat face plate
    for s in (-1, 1):
        m.put(m.strand((cx + s * 7.5, hy - 3.6, face_z - 0.5), (cx + s * 4.5, hy - 3.4, face_z + 1.4),
                       (cx + s * 1.2, hy - 2.2, face_z + 0.8), 1.7, 1.2), SKIN_D, 'brow')
    m.put(m.ell(cx, hy, zc + 1, 8.6, 8.4, 7.5) & (Z <= face_z), SKIN, 'skin')
    m.put(m.ell(cx, hy + 3.5, zc + 1, 9.2, 5.0, 7.2) & (Z <= face_z), SKIN, 'skin')

    # --- 3. hair: solid mane plus a few chunky wild spikes, swept back when running
    m.put(m.ell(cx, hy - 2.5, zc - 1, 9.9, 8.6, 9.0) & ~((Z > zc + 2) & (Y > hy - 5.5) & (np.abs(X - cx) < 8)),
          HAIR, 'hair')
    m.put(m.ell(cx, hy + 1, zc - 5, 9.0, 7.5, 5.0) & (Y > hy - 4), HAIR, 'hair')       # back of the mane
    b = 4 * tr                                                                          # streaming back
    spikes = [((cx, hy - 8.5, zc + 3), (cx + 1, hy - 14.5, zc + 1 - b / 2), (cx + 2.5, hy - 16.5, zc - 3 - b), 3.6, 1.1),
              ((cx - 5, hy - 7.5, zc + 1), (cx - 9, hy - 13, zc - b / 2), (cx - 12, hy - 13.5, zc - 2 - b), 3.2, 1.0),
              ((cx + 5, hy - 7.5, zc + 1), (cx + 9, hy - 13, zc - b / 2), (cx + 12.5, hy - 12.5, zc - 2 - b), 3.2, 1.0),
              ((cx - 3, hy - 6, zc - 6), (cx - 5, hy - 10, zc - 10 - b / 2), (cx - 6.5, hy - 8.5, zc - 13 - b), 3.0, 1.0),
              ((cx + 3.5, hy - 6, zc - 6), (cx + 6, hy - 9.5, zc - 10 - b / 2), (cx + 7.5, hy - 7, zc - 13 - b), 3.0, 1.0),
              ((cx - 2, hy - 8.5, face_z - 1), (cx - 4, hy - 6.5, face_z + 1.8), (cx - 5.5, hy - 4.6, face_z + 0.8), 2.6, 0.8)]
    for i, (p0, p1, p2, r0, r1) in enumerate(spikes):
        m.put(m.strand(p0, p1, p2, r0, r1), HAIR_STRANDS[i % 3], 'hair')

    # --- 4. oversized shoulder guards: level-topped steel slabs over a teal tier, amber lights
    for s in (-1, 1):
        px = cx + 15.5 * s
        guard = m.put(slab(39 - up, 47 - up, lambda y: 8.6 - 0.9 * max(0, 41 - up - y), lambda y: 9.0 - 0.9 * max(0, 41 - up - y),
                           x0=px), STEEL, 'guard')
        m.col[guard & (Y == 46 - up)] = STEEL_D
        rivet = guard & (Y == 43 - up) & (np.abs(Z - zc) > 6.5) & ((np.abs(X - px) % 4) < 1)
        m.col[rivet] = STEEL_D
        amber(guard & (np.abs(X - cx) > 23.2) & (Y >= 42 - up) & (Y <= 43 - up) & (np.abs(Z - zc) < 4))
        m.put(slab(47 - up, 50 - up, 7.6, 8.0, x0=px), TEAM_D, 'guard_tier')

    # --- 5. arms: bare slate muscle, steel wrist braces, huge fists
    def arm(s, shoulder, elbow, wrist, fist):
        d = np.array(fist, float) - np.array(wrist, float); d /= np.linalg.norm(d)
        band = m.put(m.cylinder(np.array(wrist) - 1.2 * d, np.array(wrist) + 1.0 * d, 5.4), STEEL, 'brace')
        amber(band & (np.abs(X - wrist[0]) > 4.6) & (np.abs(Y - wrist[1]) < 0.8))
        f = m.put(m.ell(*fist, 5.0, 4.6, 5.0), SKIN, 'fist')
        m.col[f & (Z > fist[2] + 2.6) & (Y < fist[1] + 2)] = STEEL_D    # knuckle plate on the front
        m.put(m.capsule(elbow, wrist, 5.0), SKIN, 'arm')
        m.put(m.capsule(shoulder, elbow, 4.7), SKIN, 'arm')
        return f

    for s in (-1, 1):
        sh = (cx + 15.5 * s, 47 - up, zc)
        if not running:                                   # hanging heavy, fists by the knees
            arm(s, sh, (cx + 19 * s, 57 - up, zc + 0.5), (cx + 19.5 * s, 64.5 - up, zc + 1), (cx + 19.5 * s, 69.5 - up, zc + 1.5))
        elif s == -1:                                     # free arm: bent, fist pumping
            a = g.arm(-1)
            arm(s, sh, (cx - 19, 57, zc - 1 + 0.4 * a), (cx - 18.5, 60 + g.arm_lift(-1), zc + 4.5 + a),
                (cx - 18, 61 + g.arm_lift(-1), zc + 9 + 1.2 * a))
        else:                                             # ball arm: forearm cradles the ball, fist over its nose
            arm(s, sh, (cx + 19.5, 58 + bdy, zc + 1 + bdz), (cx + 17, 61 + bdy, zc + 8.5 + bdz), (cx + 15, 59.5 + bdy, zc + 13.5 + bdz))

    # --- 6. neck and barrel torso: teal jersey with steel harness straps
    m.put(m.cylinder((cx, hy + 3, zc), (cx, 48 - up, zc), 6.8), SKIN, 'neck')
    torso = m.put(slab(44 - up, 62, lambda y: 12.8 - 0.12 * max(0, y - 50), lambda y: 9.2 - 0.06 * max(0, y - 50), n=3.0),
                  TEAM, 'torso')
    k = lambda y: 8.5 - 0.32 * (y - 44)                  # straps run in from the shoulders to the belt
    m.col[torso & (np.abs(np.abs(X - cx) - k(Y)) < 1.3) & (np.abs(Z - zc) > 4)] = STRAP
    m.col[torso & (Y >= 50 - up) & (Y <= 51 - up) & (np.abs(Z - zc) > 4)] = STRAP     # chest cross-strap
    m.col[torso & (Y >= 55) & (np.abs(Z - zc) > 4) & (np.abs(X - cx) < 1.5)] = TEAM_D
    # number 4 on the back, flat bone white
    back = torso & (Z < zc - 4)
    four = ((np.abs(X - (cx - 2.0)) < 0.9) & (Y >= 52) & (Y <= 57)) | \
           ((np.abs(X - (cx + 2.0)) < 0.9) & (Y >= 52) & (Y <= 61)) | ((Y >= 57) & (Y <= 58) & (np.abs(X - cx) <= 3.0))
    m.col[back & four & (np.abs(np.abs(X - cx) - k(Y)) >= 1.3)] = HAIR

    # --- 7. grav-brace belt: steel band, amber lights all round, central regulator
    m.put(slab(60, 64, 2.8, 1.6, cz=zc + 10.2), STEEL_D, 'regulator')
    amber(m.is_part('regulator') & (Z >= zc + 11) & (np.abs(X - cx) < 1.6) & (Y >= 61) & (Y <= 62))
    belt = m.put(slab(60, 66, 13.2, 9.8, n=3.0), STEEL, 'belt')
    m.col[belt & ((Y == 60) | (Y == 65))] = STEEL_D
    amber(belt & (Y >= 62) & (Y <= 63) & ((np.round(np.arctan2(X - cx, Z - zc) * 4) % 2) == 0)
          & (np.abs(X - cx) > 3.5))
    m.put(slab(66, 73, lambda y: 11.6 - 0.15 * (y - 66), 8.2, n=3.0), SHORTS, 'shorts')

    # --- 8. short heavy legs with knee guards, brace struts and big boots
    for s in (-1, 1):
        lx = cx + 6.6 * s
        dz, dy = g.foot(s)
        at = lambda f: (lx, 71 + 13 * f + dy * f, zc + dz * f)
        kx, ky, kz = at(0.6)
        m.put(m.ball((kx, ky, kz + 1.6), 4.0), STEEL, 'knee')
        m.put(m.capsule((lx + 5.0 * s, 65, zc), (kx + 4.0 * s, ky, kz), 1.2), STEEL_D, 'strut')
        m.put(m.capsule(at(0.0), at(0.55), 5.2), SHORTS, 'thigh')
        m.put(m.capsule(at(0.55), at(1.0), 4.4), SKIN, 'shin')
        boot = m.put(slab(81 + dy, FEET + 1 + dy, 5.6, 7.2, cz=zc + 2 + dz, x0=lx, n=3.0), BOOT, 'boot')
        m.col[boot & (Y >= FEET - 1 + dy)] = SOLE
        m.col[boot & (Y <= 82 + dy)] = STEEL_D
        amber(boot & (Y == int(round(FEET - 3 + dy))) & (Z < zc + dz - 4))            # heel lights

    m.glow('amber')

    # --- 9. face paint: one skin tone on the plate, then the eyes
    for y in range(int(hy - 9), int(hy + 9)):
        for x in range(int(cx) - 10, int(cx) + 11):
            z = m.front_z(y, x)
            if z is not None and m.part[y, z, x] == m.pid('skin'):
                m.col[y, z, x] = SKIN_FACE
    m.paint_eyes(EYE_SHUT if blink else EYE, cx, int(hy - 1), gap=2)
