"""Prepare a sprite for modelling.

  python tools/prep_sprite.py path/to/upscaled_sprite.png NAME [--cell 15.9] [--bg-tol 14]
  python tools/prep_sprite.py sprites/NAME.png NAME --dump 20,27,26,33     # hex colours of a region

Writes, next to the repo's sprites/ folder:
  sprites/NAME.png          native-resolution sprite (one pixel per art pixel, transparent bg)
  sprites/NAME_grid.png     10x zoom with coordinates every 5/10 px: read positions off this
  sprites/NAME_palette.txt  main colours as RGB tuples, ready to paste into a character file
Detects the art-pixel size of upscaled images automatically (override with --cell).
The background is whatever touches the image border: transparent pixels, or a solid colour.
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detect_cell(rgb):
    """Estimate the upscale factor: the most common spacing between neighbouring colour
    edges along rows and columns is one art pixel (works even when the grid drifts)."""
    a = rgb.astype(int)
    gaps = []
    for img in (a, a.transpose(1, 0, 2)):
        edge = np.abs(np.diff(img, axis=1)).sum(2) > 40
        for row in edge[::2]:
            pos = np.where(row)[0]
            if len(pos) > 1:
                g = np.diff(pos)
                gaps.append(g[g >= 3])           # skip anti-aliasing slivers
    g = np.concatenate(gaps).astype(float)
    if not len(g):
        return 1.0
    hist = np.bincount(g.astype(int), minlength=200)[:200].astype(float)
    hist = np.convolve(hist, [1, 2, 3, 2, 1], 'same')
    mode = float(np.argmax(hist))
    near = g[np.abs(g - mode) <= 0.25 * mode]
    double = g[np.abs(g - 2 * mode) <= 0.25 * mode] / 2      # two-pixel runs refine the estimate
    est = float(np.median(np.concatenate([near, double])))
    # refine: the size whose grid lines up best with the edges (exact for clean upscales)
    ex = (np.abs(np.diff(a, axis=1)).sum(2) > 40).sum(0).astype(float)
    ey = (np.abs(np.diff(a, axis=0)).sum(2) > 40).sum(1).astype(float)
    def fit(s):
        tot = 0
        for e in (ex, ey):
            n = len(e); k = np.arange(1, n / s); best = 0
            for off in np.arange(0, s, 0.25):
                idx = np.floor(off + k * s).astype(int) - 1
                idx = idx[(idx >= 0) & (idx < n)]
                if len(idx):
                    best = max(best, e[idx].mean())
            tot += best / (e.mean() + 1e-9)
        return tot
    cands = np.arange(est * 0.92, est * 1.08, 0.02)
    scores = np.array([fit(s) for s in cands])
    return float(cands[np.argmax(scores)]) if scores.max() > 2.5 else est


def downsample(rgba, cell):
    H0, W0 = rgba.shape[:2]
    gw, gh = int(round(W0 / cell)), int(round(H0 / cell))
    xs = ((np.arange(gw) + 0.5) * W0 / gw).astype(int)
    ys = ((np.arange(gh) + 0.5) * H0 / gh).astype(int)
    return rgba[ys][:, xs]


def remove_background(a, tol):
    if (a[..., 3] < 128).any():
        mask = a[..., 3] >= 128
    else:
        bgc = np.median(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])[:, :3], axis=0)
        near = np.abs(a[..., :3].astype(int) - bgc).max(-1) <= tol
        lab, _ = ndi.label(near)
        border = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1]); border.discard(0)
        mask = ~np.isin(lab, list(border))
    a = a.copy(); a[..., 3] = mask * 255
    yy, xx = np.where(mask)
    return a[yy.min():yy.max() + 1, xx.min():xx.max() + 1]


def grid_image(a, path, S=10):
    H, W = a.shape[:2]
    im = Image.fromarray(a, 'RGBA').resize((W * S, H * S), Image.NEAREST)
    big = Image.new('RGB', im.size, (30, 30, 30)); big.paste(im, (0, 0), im)
    d = ImageDraw.Draw(big)
    for x in range(0, W, 5):
        d.line([(x * S, 0), (x * S, H * S)], fill=(0, 255, 0) if x % 10 == 0 else (0, 90, 0))
    for y in range(0, H, 5):
        d.line([(0, y * S), (W * S, y * S)], fill=(0, 255, 0) if y % 10 == 0 else (0, 90, 0))
    for x in range(0, W, 10):
        d.text((x * S + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(0, H, 10):
        d.text((2, y * S + 2), str(y), fill=(255, 255, 0))
    big.save(path)


def palette(a, n=16):
    px = a[a[..., 3] > 0][:, :3]
    q = Image.fromarray(px[None].astype(np.uint8), 'RGB').quantize(n, method=Image.MEDIANCUT)
    pal = np.array(q.getpalette()[:3 * n]).reshape(-1, 3)
    counts = np.bincount(np.array(q).ravel(), minlength=n)
    order = np.argsort(-counts)
    return [(tuple(int(v) for v in pal[i]), int(counts[i])) for i in order if counts[i]]


def dump(a, box):
    x0, y0, x1, y1 = box
    print('     ' + ' '.join(f'{x:>6}' for x in range(x0, x1 + 1)))
    for y in range(y0, y1 + 1):
        row = []
        for x in range(x0, x1 + 1):
            p = a[y, x]
            row.append('%02x%02x%02x' % tuple(p[:3]) if p[3] else '  ----')
        print(f'{y:>4} ' + ' '.join(row))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('name')
    ap.add_argument('--cell', type=float, help='art-pixel size in the image (auto if omitted; 1 for native sprites)')
    ap.add_argument('--bg-tol', type=int, default=14)
    ap.add_argument('--dump', help='x0,y0,x1,y1 of the native sprite: print hex colours (e.g. to copy eyes)')
    a = ap.parse_args()
    img = np.array(Image.open(a.image).convert('RGBA'))
    if a.dump:
        dump(img, [int(v) for v in a.dump.split(',')]); sys.exit()
    cell = a.cell or detect_cell(img[..., :3])
    print(f'art-pixel size: {cell:.2f}')
    native = downsample(img, cell) if cell > 1.01 else img
    if cell > 1.01 and not a.cell:
        # how well does the downsampled sprite reproduce the original? (clean upscales: ~0)
        H0, W0 = img.shape[:2]
        back = np.array(Image.fromarray(native).resize((W0, H0), Image.NEAREST)).astype(int)
        err = np.abs(back[..., :3] - img[..., :3].astype(int)).mean()
        if err > 4:
            print(f'warning: this image is not a clean pixel grid (error {err:.1f}); it may be AI-upscaled '
                  f'or filtered. Check sprites/NAME_grid.png and re-run with --cell if the pixels look off.')
    native = remove_background(native, a.bg_tol)
    H, W = native.shape[:2]
    out = os.path.join(ROOT, 'sprites'); os.makedirs(out, exist_ok=True)
    Image.fromarray(native, 'RGBA').save(os.path.join(out, f'{a.name}.png'))
    grid_image(native, os.path.join(out, f'{a.name}_grid.png'))
    with open(os.path.join(out, f'{a.name}_palette.txt'), 'w') as f:
        for c, k in palette(native):
            f.write(f'{c}  # {k} px\n')
    print(f'native sprite: {W}x{H}  ->  sprites/{a.name}.png, {a.name}_grid.png, {a.name}_palette.txt')
    if H > 88 or W > 72:
        print('note: larger than the default 72x90x48 box; set GRID = (W, H, D) in the character file '
              'or check the art-pixel size')
