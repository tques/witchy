"""Build a character:  python -m spritestack.build characters/witch.py [--quick] [--views 0,35,90]

A character file defines NAME, SPRITE (native-size png from tools/prep_sprite.py) and
build(m, sprite). Outputs go to out/<NAME>/:
  atlas.png, meta.json   layers for a game engine (H slices of W x D, top to bottom)
  viewer.html            drag-to-rotate viewer (self-contained)
  turntable.gif          full spin
  sheet.png              front / side / back / side
  views.png              close-up angles from --views (quick checks while iterating)
  volume.npy             raw RGBA voxels [y][z][x]
--quick skips the GIF and viewer for fast iteration.
"""
import argparse, importlib.util, json, os, time
import numpy as np
from PIL import Image
from .model import Model
from . import render, gait, cast


def load_character(path):
    spec = importlib.util.spec_from_file_location('character', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def anim_settings(anim, overrides):
    if anim in cast.PRESETS:
        return dict(cast.PRESETS[anim], **(overrides or {}))
    return gait.settings(anim, overrides)


def _fit(vols, axis, c, margin):
    """Pad/crop one axis (1 = z, 2 = x) of every volume so position c is the exact middle."""
    occ = np.any([v[..., 3] > 0 for v in vols], axis=0)
    other = (0, 1) if axis == 2 else (0, 2)
    idx = np.where(occ.any(axis=other))[0]
    half = int(np.ceil(max(c - idx.min(), idx.max() + 1 - c))) + margin
    lo = int(round(c)) - half
    out = []
    for v in vols:
        shape = list(v.shape); n_ax = shape[axis]; shape[axis] = 2 * half
        n = np.zeros(shape, np.uint8)
        a, b = max(lo, 0), min(lo + 2 * half, n_ax)
        src = [slice(None)] * 4; dst = [slice(None)] * 4
        src[axis] = slice(a, b); dst[axis] = slice(a - lo, b - lo)
        n[tuple(dst)] = v[tuple(src)]
        out.append(n)
    return out


def recenter(vols, cx, cz=None, margin=2):
    """Put the body centre (x = cx, z = cz) in the middle of every layer, sized to fit all frames.
    Game engines (and the viewers) spin each slice around its centre, so the body must be there."""
    vols = _fit(vols, 2, cx, margin)
    return _fit(vols, 1, cz, margin) if cz is not None else vols


def build(path, quick=False, views=None, outroot=None):
    ch = load_character(path)
    root = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    sprite = None
    if getattr(ch, 'SPRITE', None):
        sprite = np.array(Image.open(os.path.join(root, ch.SPRITE)).convert('RGBA'))
    m = Model(*getattr(ch, 'GRID', ()))
    ch.build(m, sprite)                       # standing pose
    vol = m.shade()
    center = getattr(ch, 'CENTER_X', None)     # body centre line, if not already the middle of the box
    out = os.path.join(outroot or os.path.join(root, 'out'), ch.NAME)
    os.makedirs(out, exist_ok=True)
    anims = {}
    cfgs = {a: anim_settings(a, o) for a, o in getattr(ch, 'ANIMATIONS', {}).items()}
    for anim, cfg in cfgs.items():
        vols = []
        for i in range(cfg['frames']):
            fm = Model(*getattr(ch, 'GRID', ()))
            ch.build(fm, sprite, dict(cfg, anim=anim, t=i / cfg['frames'], frame=i))
            vols.append(fm.shade())
        anims[anim] = vols
    if center is not None:                     # one shared width for the pose and every frame
        allv = recenter([vol] + [v for vs in anims.values() for v in vs], center,
                        getattr(ch, 'CENTER_Z', None))
        vol, k = allv[0], 1
        for anim in anims:
            anims[anim] = allv[k:k + len(anims[anim])]; k += len(anims[anim])
    np.save(os.path.join(out, 'volume.npy'), vol)
    render.save_atlas(vol, out)
    render.sheet(vol, os.path.join(out, 'sheet.png'))
    if views:
        render.sheet(vol, os.path.join(out, 'views.png'), angles=views, scale=7)
    if not quick:
        render.turntable(vol, os.path.join(out, 'turntable.gif'))
        render.viewer(vol, os.path.join(out, 'viewer.html'), getattr(ch, 'TITLE', ch.NAME))
    for anim, cfg in cfgs.items():
        vols = anims[anim]
        ad = os.path.join(out, anim); os.makedirs(ad, exist_ok=True)
        Image.fromarray(render.anim_atlas(vols), 'RGBA').save(os.path.join(ad, 'atlas.png'))
        H, D, W, _ = vols[0].shape
        json.dump(dict(W=W, H=H, D=D, **{k: v for k, v in cfg.items() if not callable(v)},
                       layout='frames left to right; each frame column is H slices of W x D, top to bottom'),
                  open(os.path.join(ad, 'meta.json'), 'w'), indent=1)
        strip = [render.frame(v, 80) for v in vols]          # side view: best for checking steps
        sw, sh = strip[0].size
        img = Image.new('RGBA', (sw * len(strip), sh))
        for i, f in enumerate(strip):
            img.paste(f, (i * sw, 0))
        img.save(os.path.join(ad, 'frames.png'))
        if not quick:
            seq = [(v, cfg['fps'], cfg['speed']) for v in vols]
            lead = cfg.get('chain_from')
            if lead in anims:        # one-shots: show them from (and back into) the pose they chain from
                lc = cfgs[lead]
                hold = [(v, lc['fps'], lc['speed']) for v in anims[lead]]
                seq = hold + seq + hold
            else:
                seq = seq * 3
            render.anim_gif(seq, os.path.join(out, f'{anim}.gif'))
        print(f'  {anim}: {len(vols)} frames, {cfg["fps"]} fps, {cfg["speed"]:.2f} cubes/frame -> {ad}')
    if anims and not quick:
        render.play_viewer(vol, {a: (anims[a], cfgs[a]) for a in anims}, os.path.join(out, 'play.html'),
                           getattr(ch, 'TITLE', ch.NAME))
    print(f'{ch.NAME}: {int(m.occ.sum())} voxels -> {out}')
    return vol


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('character')
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--views', default='')
    a = ap.parse_args()
    t = time.time()
    build(a.character, a.quick, [float(v) for v in a.views.split(',') if v])
    print(f'done in {time.time() - t:.1f}s')
