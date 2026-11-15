"""Chain a built character's animations into one showcase GIF.

  python tools/sequence.py witch "stand:1s walk:2 run:3 walk:1 stand:0.5s cast_raise cast_hold:1 cast_flick cast_hold:1" --labels

Each step is NAME:COUNT (cycles, or plays for one-shots) or NAME:SECONDSs. "stand" is the
standing pose. Uses the frames already built in out/NAME/ (run the build first).
Options: --angle 35 (camera, degrees), --orbit 40 (swing the camera this many degrees over
the whole sequence, to show it's 3D), --labels (name each step in the corner), --scale 5, --out PATH.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from spritestack import render, style  # noqa: E402


def load(name):
    out = os.path.join(ROOT, 'out', name)
    m = json.load(open(os.path.join(out, 'meta.json')))
    a = np.array(Image.open(os.path.join(out, 'atlas.png')))
    anims = {'stand': dict(frames=[a.reshape(m['H'], m['D'], m['W'], 4)], fps=10, speed=0.0, loop=True)}
    for d in sorted(os.listdir(out)):
        meta = os.path.join(out, d, 'meta.json')
        if os.path.isfile(meta):
            am = json.load(open(meta))
            at = np.array(Image.open(os.path.join(out, d, 'atlas.png')))
            W, H, D = am['W'], am['H'], am['D']
            fr = [at[:, i * W:(i + 1) * W].reshape(H, D, W, 4) for i in range(at.shape[1] // W)]
            anims[d] = dict(frames=fr, fps=am['fps'], speed=am.get('speed', 0.0), loop=am.get('loop', True))
    return anims


def plan(anims, script):
    seq = []
    for step in script.split():
        name, _, amount = step.partition(':')
        if name not in anims:
            sys.exit(f'unknown animation "{name}"; built ones: {", ".join(anims)}')
        a = anims[name]
        if amount.endswith('s'):                       # seconds
            n = max(1, round(float(amount[:-1]) * a['fps']))
            fr = [a['frames'][i % len(a['frames'])] for i in range(n)]
        else:                                         # cycles / plays
            fr = a['frames'] * int(amount or 1)
        seq += [(f, a['fps'], a['speed'], name) for f in fr]
    return seq


def _font(width):
    from PIL import ImageFont
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVuSans.ttf', 'Arial.ttf'):
        try:
            return ImageFont.truetype(f, max(14, width // 26))
        except OSError:
            pass
    return ImageFont.load_default()


def crop_to(seq, pad=6):
    """Trim the empty box margins shared by every frame so the character fills the GIF."""
    occ = np.any([v[..., 3] > 0 for v, *_ in seq], axis=0)
    ys = np.where(occ.any(axis=(1, 2)))[0]
    lo = max(0, ys.min() - pad)
    return [(v[lo:], *rest) for v, *rest in seq]


def make_gif(seq, path, angle, orbit, labels, scale=style.PREVIEW_SCALE):
    seq = crop_to(seq)
    n = len(seq)
    angles = [angle - orbit / 2 + orbit * i / max(1, n - 1) for i in range(n)]
    frames, durations, travel = [], [], 0.0
    for i, (vol, fps, speed, name) in enumerate(seq):
        img = render.ground_frame(vol, angles[i], travel, scale=scale)
        if labels:
            d = ImageDraw.Draw(img)
            d.text((16, 12), name.replace('_', ' '), fill=(207, 200, 238, 255), font=_font(img.width))
        frames.append(img.convert('P', palette=Image.ADAPTIVE))
        durations.append(int(1000 / fps))
        travel += speed
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0)
    return n, sum(durations) / 1000


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('name'); ap.add_argument('script')
    ap.add_argument('--angle', type=float, default=35); ap.add_argument('--orbit', type=float, default=0)
    ap.add_argument('--labels', action='store_true'); ap.add_argument('--out')
    ap.add_argument('--scale', type=int, default=5, help='screen pixels per cube')
    a = ap.parse_args()
    path = a.out or os.path.join(ROOT, 'out', a.name, 'sequence.gif')
    n, secs = make_gif(plan(load(a.name), a.script), path, a.angle, a.orbit, a.labels, a.scale)
    print(f'{n} frames, {secs:.1f}s -> {path}')
