"""Spellcasting actions shared by every mage (staff, wand, orb, sword-mage...).

    c = cast(pose)            # inert (all zeros) unless pose['anim'] is a cast preset
    c.active                  # True while casting
    c.hand(rest, cast)        # where the casting hand is (rest -> raised, plus wind-up/snap motion)
    c.aim(rest_dir, cast_dir) # unit direction the prop points (raised, plus wind-up/snap pitch)
    c.place(points, grip, rest_dir, hand, aim)  # move a rigid prop: rotate about its grip, then put grip in hand
    c.rotation(rest_dir, aim) # 3x3 rotation for oriented shapes (rings, discs): m.ell_oriented(..., R)
    c.free_hand(rest, cast)   # the other hand opens out to the side
    c.pulse                   # 0..1 glow strength of the focus (orb/gem): m.glow(part, boost=...)
    c.sparkles(center, aim)   # points for sparkles orbiting the focus (hold) / burst ring (flick)
    c.bolt(center, aim)       # released bolt: [(position, size), ...] head first, with a trail
    c.sparkle_size            # preset size for sparkles
    c.breeze                  # 0..1 magic wind: lift hair / hems a little (use like gait.trail)
    c.apply(m, pivot_y)       # small lean (back on wind-up, forward on the snap)

cast_hold loops; cast_flick plays once, starting and ending in the hold pose, so the two chain.
With pose=None every value is 0 / the rest pose, so the standing model never changes.
"""
import math
import numpy as np

PRESETS = {
    # held, ready to cast: arm up, focus pulsing, sparkles circling
    'cast_hold':  dict(frames=8, fps=8, speed=0.0, loop=True, sway=4.0, sparkle_count=6, sparkle_radius=7.5, sparkle_size=1.1,
                       breeze=0.35),
    # the release: wind back, snap forward past the aim, burst + bolt, settle back into the hold
    'cast_flick': dict(frames=10, fps=14, speed=0.0, loop=False, chain_from='cast_hold',
                       wind_pitch=-35.0, snap_pitch=22.0, wind_hand=(0, -2.0, -2.5), snap_hand=(0, 1.0, 3.0),
                       release=0.42, burst_len=0.4, bolt_len=0.35, bolt_reach=16.0, bolt_size=3.6, burst_radius=12.0,
                       sparkle_count=12, sparkle_size=1.4, breeze=0.6, lean_wind=-0.03, lean_snap=0.05),
}


def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def axis_angle(axis, deg):
    a = _norm(axis); t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def rotation_between(a, b):
    """Smallest rotation taking direction a onto direction b."""
    a, b = _norm(a), _norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else axis_angle(np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0]), 180)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


class Cast:
    def __init__(self, pose=None):
        self.active = bool(pose) and pose.get('anim') in PRESETS
        self.s = dict(PRESETS[pose['anim']], **{k: v for k, v in pose.items() if k not in ('anim', 't', 'frame')}) if self.active else {}
        self.kind = pose['anim'] if self.active else None
        t = pose['t'] if self.active else 0.0
        self.t = t
        s = self.s
        self.raise_ = 1.0 if self.active else 0.0
        self.pitch, self.hand_off, self.lean, self.burst, self.bolt_t = 0.0, np.zeros(3), 0.0, None, None
        if not self.active:
            self.pulse, self.breeze = 0.0, 0.0
        elif self.kind == 'cast_hold':
            self.pitch = s['sway'] * math.sin(2 * math.pi * t)
            self.pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t)
            self.breeze = s['breeze']
        else:   # cast_flick
            r = s['release']
            wind = np.array(s['wind_hand'], float); snap = np.array(s['snap_hand'], float)
            if t < r * 0.8:                                   # wind up
                k = _ease(t / (r * 0.8))
                self.pitch, self.hand_off = s['wind_pitch'] * k, wind * k
                self.lean = s['lean_wind'] * k
            elif t < r + 0.08:                                # snap through the release
                k = _ease((t - r * 0.8) / (r * 0.2 + 0.08))
                self.pitch = s['wind_pitch'] + (s['snap_pitch'] - s['wind_pitch']) * k
                self.hand_off = wind + (snap - wind) * k
                self.lean = s['lean_wind'] + (s['lean_snap'] - s['lean_wind']) * k
            else:                                             # recover into the hold
                k = _ease((t - r - 0.08) / (1 - r - 0.08))
                self.pitch, self.hand_off = s['snap_pitch'] * (1 - k), snap * (1 - k)
                self.lean = s['lean_snap'] * (1 - k)
            self.pulse = min(1.0, 0.5 + t / r * 0.5) if t < r else max(0.0, 1 - (t - r) / 0.25) * 0.5 + 0.5 * _ease((t - r) / (1 - r))
            self.breeze = s['breeze'] if r - 0.1 < t < r + 0.35 else PRESETS['cast_hold']['breeze']
            if r <= t < r + s['burst_len']:
                self.burst = (t - r) / s['burst_len']
            if r <= t < r + s['bolt_len']:
                self.bolt_t = (t - r) / s['bolt_len']

    # --- casting arm and prop ------------------------------------------------
    def hand(self, rest, cast):
        rest, cast = np.asarray(rest, float), np.asarray(cast, float)
        return rest + (cast - rest) * self.raise_ + self.hand_off

    def aim(self, rest_dir, cast_dir):
        rest_dir, cast_dir = _norm(rest_dir), _norm(cast_dir)
        d = _norm(rest_dir + (cast_dir - rest_dir) * self.raise_)
        if self.pitch:
            side = np.cross(d, [0, -1, 0])                  # tilt the tip back (-) or forward (+)
            if np.linalg.norm(side) > 1e-6:
                d = axis_angle(side, -self.pitch) @ d
        return _norm(d)

    def rotation(self, rest_dir, aim):
        return rotation_between(rest_dir, aim)

    def place(self, points, grip, rest_dir, hand, aim):
        """Rigid prop: rotate its standing-pose points about the grip so rest_dir -> aim, move grip to hand."""
        R = rotation_between(rest_dir, aim)
        grip = np.asarray(grip, float)
        return [tuple(R @ (np.asarray(p, float) - grip) + hand) for p in points]

    def free_hand(self, rest, cast):
        rest, cast = np.asarray(rest, float), np.asarray(cast, float)
        return rest + (cast - rest) * self.raise_

    # --- effects -------------------------------------------------------------
    def _frame(self, aim):
        a = _norm(aim)
        u = _norm(np.cross(a, [0, 1, 0]) if abs(a[1]) < 0.95 else np.cross(a, [1, 0, 0]))
        return u, np.cross(a, u)

    def sparkles(self, center, aim):
        """Hold: motes orbiting the focus. Flick: an expanding ring after the release."""
        if not self.active:
            return []
        c = np.asarray(center, float); u, v = self._frame(aim); s = self.s
        pts = []
        if self.kind == 'cast_hold':
            n, R = s['sparkle_count'], s['sparkle_radius']
            for i in range(n):
                a = 2 * math.pi * (self.t + i / n)
                r = R * (1 + 0.12 * math.sin(4 * math.pi * self.t + i))
                pts.append(c + r * (math.cos(a) * u + math.sin(a) * v) + np.array([0, -1.5 * math.sin(a * 2), 0]))
        elif self.burst is not None:
            n = s['sparkle_count']; R = 3 + s['burst_radius'] * _ease(self.burst)
            for i in range(n):
                if self.burst > 0.6 and i % 2:
                    continue                                  # thin out as it fades
                a = 2 * math.pi * i / n
                pts.append(c + R * (math.cos(a) * u + math.sin(a) * v))
        return [tuple(p) for p in pts]

    @property
    def sparkle_size(self):
        return self.s.get('sparkle_size', 1.0)

    def bolt(self, center, aim):
        """The released bolt: list of (position, size), head first, with a short fading trail."""
        if self.bolt_t is None:
            return []
        k = self.bolt_t; a = _norm(aim); c = np.asarray(center, float)
        head = 5 + self.s['bolt_reach'] * _ease(k)
        size = self.s['bolt_size'] * (1 - 0.45 * k)
        return [(tuple(c + a * (head - 3.2 * i)), size * (0.75 ** i)) for i in range(4) if head - 3.2 * i > 4]

    def apply(self, m, pivot_y):
        if self.lean:
            m.lean, m.lean_pivot = self.lean, pivot_y


def cast(pose):
    return Cast(pose)
