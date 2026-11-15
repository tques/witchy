"""Sprite-stack rendering: preview frames, turntable GIF, contact sheet, HTML viewer."""
import base64, json, math, os
import numpy as np
from PIL import Image
from . import style

VIEWER = os.path.join(os.path.dirname(__file__), 'viewer_template.html')


def frame(vol, angle_deg, scale=style.PREVIEW_SCALE, tilt=style.CAMERA_TILT, bg=style.BACKGROUND):
    """Draw every horizontal layer rotated by angle, bottom layer first, each shifted up."""
    H, D, W, _ = vol.shape
    S = scale; T = math.radians(tilt); th = math.radians(angle_deg)
    OW, OH = int(W * S * 1.5), int(H * S * math.cos(T) + W * S * 0.9)
    out = Image.new('RGBA', (OW, OH), (0, 0, 0, 0) if bg is None else bg + (255,))
    cx = OW / 2; base = OH - W * S * 0.35
    c, s = math.cos(th), math.sin(th); st = math.sin(T)
    a = c / S; b = s / (S * st); d = -s / S; e = c / (S * st)
    steps = math.ceil(S * math.cos(T))          # redraw each layer a few px up to fill gaps
    for y in range(H - 1, -1, -1):
        if not vol[y, ..., 3].any():
            continue
        layer = Image.fromarray(vol[y], 'RGBA')
        cy = base - (H - 1 - y) * S * math.cos(T)
        cu = W / 2 - a * cx - b * cy; cv = D / 2 - d * cx - e * cy
        lay = layer.transform((OW, OH), Image.AFFINE, (a, b, cu, d, e, cv), Image.NEAREST)
        for k in range(steps):
            out.alpha_composite(lay, (0, -k))
    return out


def turntable(vol, path, frames=style.TURNTABLE_FRAMES, **kw):
    fr = [frame(vol, 360.0 * i / frames, **kw) for i in range(frames)]
    pal = [f.convert('P', palette=Image.ADAPTIVE) for f in fr]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=70, loop=0)


def sheet(vol, path, angles=(0, 90, 180, 270), **kw):
    fr = [frame(vol, a, **kw) for a in angles]
    w, h = fr[0].size
    out = Image.new('RGBA', (w * len(fr), h))
    for i, f in enumerate(fr):
        out.paste(f, (i * w, 0))
    out.save(path)


def save_atlas(vol, outdir):
    H, D, W, _ = vol.shape
    Image.fromarray(vol.reshape(H * D, W, 4), 'RGBA').save(os.path.join(outdir, 'atlas.png'))
    json.dump(dict(W=W, H=H, D=D, layer_order='top to bottom', slice='W x D, front row last'),
              open(os.path.join(outdir, 'meta.json'), 'w'), indent=1)


def viewer(vol, path, title):
    H, D, W, _ = vol.shape
    import io
    buf = io.BytesIO()
    Image.fromarray(vol.reshape(H * D, W, 4), 'RGBA').save(buf, 'PNG')
    html = open(VIEWER).read()
    for k, v in dict(TITLE=title, W=W, H=H, D=D, TILT=style.CAMERA_TILT,
                     ATLAS=base64.b64encode(buf.getvalue()).decode()).items():
        html = html.replace('{{%s}}' % k, str(v))
    open(path, 'w').write(html)


def anim_gif(seq, path, angle=35, scale=style.PREVIEW_SCALE, tilt=style.CAMERA_TILT, spacing=12, bg=style.BACKGROUND):
    """seq: list of (volume, fps, speed). Plays the frames over ground dots that scroll back at
    `speed` cubes per frame (she faces +z; the camera follows her)."""
    from PIL import ImageDraw
    H, D, W, _ = seq[0][0].shape
    S = scale; T = math.radians(tilt); th = math.radians(angle)
    c, s_, st = math.cos(th), math.sin(th), math.sin(T)
    out, durations, travel = [], [], 0.0
    for vol, fps, speed in seq:
        ch = frame(vol, angle, scale, tilt, bg=None)
        OW, OH = ch.size
        cx = OW / 2; base = OH - W * S * 0.35
        img = Image.new('RGBA', (OW, OH), bg + (255,))
        d = ImageDraw.Draw(img)
        for gx in np.arange(-72, 73, spacing):
            for gz in np.arange(-72, 73, spacing):
                z = gz - travel % spacing
                X = cx + S * (gx * c - z * s_)
                Y = base + S * (gx * s_ + z * c) * st
                d.rectangle([X - S * 0.6, Y - S * 0.4, X + S * 0.6, Y + S * 0.4], fill=(52, 44, 82, 255))
        d.ellipse([cx - S * 9, base - S * 9 * st, cx + S * 9, base + S * 9 * st], fill=(16, 13, 28, 255))
        img.alpha_composite(ch)
        out.append(img.convert('P', palette=Image.ADAPTIVE))
        durations.append(int(1000 / fps))
        travel += speed
    out[0].save(path, save_all=True, append_images=out[1:], duration=durations, loop=0)


def walk_gif(vols, path, speed, fps, cycles=3, **kw):
    anim_gif([(v, fps, speed) for v in vols] * cycles, path, **kw)


def anim_atlas(vols):
    """Frames side by side; each frame column is H slices of W x D, top to bottom."""
    H, D, W, _ = vols[0].shape
    return np.concatenate([v.reshape(H * D, W, 4) for v in vols], axis=1)


def play_viewer(stand, anims, path, title):
    """One page: stand / walk / run (any animations), steer with drag or arrow keys, hold Shift to run."""
    import io
    H, D, W, _ = stand.shape
    data = {}
    for name, (vols, cfg) in [('stand', ([stand], dict(fps=1, speed=0)))] + list(anims.items()):
        buf = io.BytesIO()
        Image.fromarray(anim_atlas(vols), 'RGBA').save(buf, 'PNG')
        data[name] = dict(n=len(vols), fps=cfg['fps'], speed=cfg['speed'], loop=cfg.get('loop', True),
                          after=cfg.get('chain_from'),
                          src='data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode())
    html = open(os.path.join(os.path.dirname(__file__), 'play_viewer_template.html')).read()
    for k, v in dict(TITLE=title, W=W, H=H, D=D, TILT=style.CAMERA_TILT, ANIMS=json.dumps(data)).items():
        html = html.replace('{{%s}}' % k, str(v))
    open(path, 'w').write(html)
