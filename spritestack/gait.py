"""Locomotion cycles shared by every character.

A character's build(m, sprite, pose) calls g = gait(pose) and reads where things go:
    g.foot(side)      -> (dz, dy) offset of that boot from the standing pose (+dz forward, -dy up)
    g.leg_frac(side)  -> swing -1..1 (back..forward), for anything else that follows a leg
    g.arm(side)       -> dz of a free hand (swings opposite the leg on its side)
    g.prop_arm(side)  -> dz of a hand holding something (swings less)
    g.arm_lift(side)  -> dy of a hand (runners raise the forward hand)
    g.hem(side)       -> function y -> z-centre offset for that half of a skirt/robe
    g.trail           -> 0..1 how much hair, capes and hat tips stream backward
    m.lift / m.lean   -> set from g.bob / g.lean by apply(m)
side is -1 for the screen-left limb, +1 for the screen-right one. With pose=None
(standing) every offset is exactly 0, so the approved standing model never changes.
"""
import math

# Tuned on the witch (chibi, ~88 layers tall). Override any value per character via
# ANIMATIONS = {'run': dict(stride=8)} in the character file.
PRESETS = {
    'walk': dict(frames=8, fps=10, stride=5.5, lift=2.6, kick=0.0, arm=2.5, prop_arm=1.2, arm_raise=0.0,
                 hem=2.0, hem_from=58, hem_span=18, bob='walk', lean=0.0, trail=0.0),
    'run':  dict(frames=8, fps=14, stride=7.5, lift=4.5, kick=2.5, arm=4.0, prop_arm=2.0, arm_raise=1.5,
                 hem=3.0, hem_from=54, hem_span=22, bob='run', lean=0.09, trail=1.0),
}


def settings(anim, overrides=None):
    s = dict(PRESETS.get(anim, PRESETS['walk']))
    s.update(overrides or {})
    s.setdefault('speed', ground_speed(s))
    return s


def ground_speed(s):
    """Cubes travelled per frame so the planted foot doesn't slide: a full cycle is two steps,
    each covering the stride twice (front to back)."""
    return 2 * s['stride'] / (s['frames'] / 2)


class Gait:
    def __init__(self, pose=None):
        self.moving = bool(pose) and (pose.get('anim') in PRESETS or 'stride' in pose)
        self.s = settings(pose.get('anim'), pose) if self.moving else None
        self.phi = 2 * math.pi * pose['t'] if self.moving else 0.0
        s, phi = self.s, self.phi
        self._legs = {}
        for side, off in ((-1, 0.0), (1, math.pi)):
            if not self.moving:
                self._legs[side] = (0.0, 0.0, 0.0)
                continue
            p = phi + off
            swing, fwd = math.sin(p), math.cos(p)
            kick = max(0.0, -swing) ** 2 if fwd < 0 else 0.0     # heel kicks up behind at the end of a run stride
            self._legs[side] = (swing, max(0.0, fwd), kick)
        if not self.moving:
            self.bob, self.lean, self.trail = 0, 0.0, 0.0
        else:
            if s['bob'] == 'run':      # highest in flight (legs split), lowest at mid-stance
                self.bob = int(round(2 * math.sin(phi) ** 2))
            else:                      # walk: up one layer as the feet pass
                self.bob = 1 if abs(math.sin(phi)) < 0.5 else 0
            self.lean, self.trail = s['lean'], s['trail']

    # legs ---------------------------------------------------------------
    def leg_frac(self, side):
        return self._legs[side][0]

    def foot(self, side):
        if not self.moving:
            return 0.0, 0.0
        swing, up, kick = self._legs[side]
        return self.s['stride'] * swing, -(self.s['lift'] * up + self.s['kick'] * kick)

    # arms ---------------------------------------------------------------
    def arm(self, side):
        return -self._legs[side][0] * self.s['arm'] if self.moving else 0.0

    def prop_arm(self, side):
        return -self._legs[side][0] * self.s['prop_arm'] if self.moving else 0.0

    def arm_lift(self, side):
        return -max(0.0, -self._legs[side][0]) * self.s['arm_raise'] if self.moving else 0.0

    # cloth --------------------------------------------------------------
    def hem(self, side):
        """z offset of one half of a skirt, growing toward the hem; also trails back when running."""
        if not self.moving:
            return lambda y: 0.0
        s, sw = self.s, self._legs[side][0]
        return lambda y: (s['hem'] * sw - 1.5 * s['trail']) * max(0.0, (y - s['hem_from']) / s['hem_span'])

    def apply(self, m, pivot_y):
        """Body bob and forward lean (rows shift forward more the higher they are above pivot_y)."""
        m.lift = self.bob
        m.lean, m.lean_pivot = self.lean, pivot_y


def gait(pose):
    return Gait(pose)
