"""Bake the prototype: every wall, prop and character animation becomes a sprite-stack atlas,
embedded with the room data into one self-contained page, prototype/witch_rpg.html.

  python prototype/build_game.py        (build the witch and fairy first: python -m spritestack.build ...)
"""
import base64, io, json, os, sys, time
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import props as P                     # noqa: E402
from rooms import ROOMS, WORLD_SCALE  # noqa: E402
P.SCALE = WORLD_SCALE                 # props/walls are enlarged to the witch's scale

SEG = 16          # wall segment length (depth-sorting granularity)
FENCE_SEG = 24


def trim(vols):
    """Crop a set of frames to their shared content, keeping the x/z centre in the middle and the
    bottom layer on the ground. Returns cropped frames."""
    occ = np.any([v[..., 3] > 0 for v in vols], axis=0)
    H, D, W = occ.shape
    top = np.where(occ.any(axis=(1, 2)))[0].min()
    def half(axis, n):
        idx = np.where(occ.any(axis=axis))[0]
        c = (n - 1) / 2
        return int(np.ceil(max(c - idx.min(), idx.max() - c))) + 1
    hz, hx = half((0, 2), D), half((0, 1), W)
    cz, cxx = (D - 1) / 2, (W - 1) / 2
    z0, x0 = int(round(cz - hz + 0.5)), int(round(cxx - hx + 0.5))
    out = []
    for v in vols:
        n = np.zeros((H - top, 2 * hz, 2 * hx, 4), np.uint8)
        zs, xs = max(z0, 0), max(x0, 0)
        ze, xe = min(z0 + 2 * hz, D), min(x0 + 2 * hx, W)
        n[:, zs - z0:ze - z0, xs - x0:xe - x0] = v[top:, zs:ze, xs:xe]
        out.append(n)
    return out


def atlas_entry(vols, **extra):
    H, D, W, _ = vols[0].shape
    img = np.concatenate([v.reshape(H * D, W, 4) for v in vols], axis=1)
    buf = io.BytesIO(); Image.fromarray(img, 'RGBA').save(buf, 'PNG', optimize=True)
    return dict(W=W, H=H, D=D, n=len(vols), src='data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), **extra)


def load_anim(char, anim):
    out = os.path.join(ROOT, 'out', char)
    if anim == 'stand':
        m = json.load(open(os.path.join(out, 'meta.json')))
        a = np.array(Image.open(os.path.join(out, 'atlas.png')))
        return [a.reshape(m['H'], m['D'], m['W'], 4)], dict(fps=1, speed=0)
    m = json.load(open(os.path.join(out, anim, 'meta.json')))
    a = np.array(Image.open(os.path.join(out, anim, 'atlas.png')))
    W, H, D = m['W'], m['H'], m['D']
    return [a[:, i * W:(i + 1) * W].reshape(H, D, W, 4) for i in range(m['frames'])], m


def scale_room(r, k):
    """Multiply every coordinate in a room (built in base units) by k."""
    sc = lambda v: [x * k for x in v]
    r['size'] = sc(r['size'])
    if 'start' in r: r['start'] = sc(r['start'])
    for o in r['objects'] + r.get('npcs', []):
        o['pos'] = sc(o['pos'])
        if 'block' in o: o['block'] = sc(o['block'])
        if 'interact' in o: o['interact'] = dict(o['interact'], at=sc(o['interact']['at']))
        if 'wander' in o: o['wander'] = dict(o['wander'], radius=o['wander']['radius'] * k)
    for e in r['exits']:
        e['rect'], e['spawn'] = sc(e['rect']), sc(e['spawn'])
    for c in r['cameras']:
        c['target'] = sc(c['target']); c['zoom'] = c['zoom'] / k
        if c.get('zone'): c['zone'] = sc(c['zone'])
        if isinstance(c.get('follow'), dict) and c['follow'].get('bounds'): c['follow'] = dict(c['follow'], bounds=sc(c['follow']['bounds']))
    for d in r['floor'].get('decals', []):
        for key in ('rect', 'center'):
            if key in d: d[key] = sc(d[key])
        for key in ('width', 'radius'):
            if key in d: d[key] = d[key] * k
        if 'points' in d: d['points'] = [sc(p) for p in d['points']]
    r['floor']['scale'] = k
    return r


def outskirts(rid, r, nbs):
    """Scenery planted just outside a room's walkable area (rooms.py: outskirts='trees'), so a following camera
    that reaches an edge sees a border instead of empty ground. Trees along the north, east and west edges;
    low bushes and rocks along the south (camera) side so nothing tall stands between the camera and the player.
    Skips anything that would land inside a neighbouring room or in front of an exit. Look-only: outside the
    walkable area, so it blocks nothing. Positions are deterministic per room."""
    import random
    if r.get('outskirts') != 'trees':
        return []
    rng = random.Random(rid)
    W, D = r['size']; k = WORLD_SCALE
    nb_rects = [(n['off'][0] / k, n['off'][1] / k, n['off'][0] / k + ROOMS[n['id']]['size'][0], n['off'][1] / k + ROOMS[n['id']]['size'][1]) for n in nbs]
    exits = [((e['rect'][0] + e['rect'][2]) / 2, (e['rect'][1] + e['rect'][3]) / 2) for e in r['exits']]
    out = []
    def plant(x, z, south):
        if any(x0 - 10 <= x <= x1 + 10 and z0 - 10 <= z <= z1 + 10 for x0, z0, x1, z1 in nb_rects):
            return
        if any(abs(x - ex) < 34 and abs(z - ez) < 34 for ex, ez in exits):
            return
        asset = rng.choice(['bush', 'bush2', 'bush', 'rocks']) if south else rng.choice(['tree', 'tree2', 'tree', 'bush2'])
        out.append(dict(asset=asset, pos=[x * k, z * k], scenery=True))
    for edge in 'NSEW':
        length = W if edge in 'NS' else D
        t = rng.uniform(4, 16)
        while t < length + 30:
            depth = rng.uniform(10, 34) if edge != 'S' else rng.uniform(8, 18)
            if edge == 'N': plant(t - 15, -depth, False)
            if edge == 'S': plant(t - 15, D + depth, True)
            if edge == 'W': plant(-depth, t - 15, False)
            if edge == 'E': plant(W + depth, t - 15, False)
            t += rng.uniform(22, 32) if edge != 'S' else rng.uniform(26, 40)
    return out


def main():
    t0 = time.time()
    assets, rooms = {}, {}

    # characters: one shared crop per character so every animation lines up
    for char, anims in (('witch', ['stand', 'walk', 'run', 'cast_raise', 'cast_flick', 'cast_lower']), ('fairy', ['stand']), ('wizard', ['stand', 'walk'])):
        loaded = {a: load_anim(char, a) for a in anims}
        allv = trim([v for a in anims for v in loaded[a][0]])
        k = 0
        for a in anims:
            n = len(loaded[a][0]); meta = loaded[a][1]
            assets[f'{char}_{a}'] = atlas_entry(allv[k:k + n], fps=meta.get('fps', 1), speed=meta.get('speed', 0))
            k += n

    # props
    used = {p['asset'] for r in ROOMS.values() for p in r.get('props', [])} | \
           {p['swap'] for r in ROOMS.values() for p in r.get('props', []) if 'swap' in p}
    for name in sorted(used):
        assets[name] = atlas_entry(trim([P.PROPS[name]()]))

    # walls and fences: split runs into segments, reuse identical segments
    def segments(run, seg):
        out, off = [], 0
        while off < run['length']:
            ln = min(seg, run['length'] - off)
            feat = {}
            for f in ('door', 'window'):
                if run.get(f) and off <= run[f][0] < off + ln:
                    feat[f] = (run[f][0] - off, run[f][1] - off)
            out.append((off, ln, feat)); off += ln
        return out

    for rid, r in ROOMS.items():
        objs = []
        for i, run in enumerate(r.get('walls', [])):
            for off, ln, feat in segments(run, SEG):
                key = f"wall_{run['kind']}_{run['axis']}_{ln}_{run['height']}_" + '_'.join(f'{k}{a}-{b}' for k, (a, b) in feat.items())
                if key not in assets:
                    assets[key] = atlas_entry([P.wall(ln, run['axis'], run['height'], 4, run['kind'], seed=len(assets), **feat)])
                sx, sz = run['start']
                if run['axis'] == 'x':
                    pos = (sx + off + ln / 2, sz + 2); block = (ln / 2, 2)
                else:
                    pos = (sx + 2, sz + off + ln / 2); block = (2, ln / 2)
                objs.append(dict(asset=key, pos=pos, block=block, wall=True))
        for run in r.get('fences', []):
            for off, ln, feat in segments(run, FENCE_SEG):
                key = f"fence_{run['axis']}_{ln}"
                if key not in assets:
                    assets[key] = atlas_entry([P.fence(ln, run['axis'])])
                sx, sz = run['start']
                pos = (sx + off + ln / 2, sz + 2) if run['axis'] == 'x' else (sx + 2, sz + off + ln / 2)
                block = (ln / 2, 2) if run['axis'] == 'x' else (2, ln / 2)
                objs.append(dict(asset=key, pos=pos, block=block, wall=True))
        for p in r.get('props', []):
            objs.append(dict(p))
        import copy
        rooms[rid] = scale_room(copy.deepcopy(dict({k: v for k, v in r.items() if k not in ('walls', 'fences', 'props')}, objects=objs)), WORLD_SCALE)

    # outdoor rooms see their outdoor neighbours: line up each pair of linked exits, gate to gate
    def edge_of(r, rect):
        W, D = r['size']; cx, cz = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
        d = {'N': cz, 'S': D - cz, 'W': cx, 'E': W - cx}
        return min(d, key=d.get), cx, cz
    for rid, r in ROOMS.items():
        nbs = []
        if r['floor']['style'] != 'wood':
            for e in r['exits']:
                other = ROOMS[e['to']]
                back = next((f for f in other['exits'] if f['to'] == rid), None)
                if other['floor']['style'] == 'wood' or not back:
                    continue
                ea, ex, ez = edge_of(r, e['rect']); eb, fx, fz = edge_of(other, back['rect'])
                if {ea, eb} not in ({'N', 'S'}, {'E', 'W'}):
                    continue
                W, D = r['size']; W2, D2 = other['size']
                off = {'S': (ex - fx, D), 'N': (ex - fx, -D2), 'E': (W, ez - fz), 'W': (-W2, ez - fz)}[ea]
                nbs.append(dict(id=e['to'], off=[off[0] * WORLD_SCALE, off[1] * WORLD_SCALE]))
        rooms[rid]['neighbors'] = nbs
        rooms[rid]['objects'] += outskirts(rid, r, nbs)
        rooms[rid]['id'] = rid
        if nbs:
            print(f'  {rid} sees ' + ', '.join(f"{n['id']} at ({n['off'][0] / WORLD_SCALE:g}, {n['off'][1] / WORLD_SCALE:g})" for n in nbs))

    data = dict(assets=assets, rooms=rooms, start='cottage')
    html = open(os.path.join(HERE, 'game_template.html')).read()
    html = html.replace('/*GAME_JS*/', open(os.path.join(HERE, 'game.js')).read())
    html = html.replace('/*GAME_DATA*/null', json.dumps(data, separators=(',', ':')))
    out = os.path.join(HERE, 'witch_rpg.html')
    open(out, 'w').write(html)
    print(f'{len(assets)} assets, {len(html) / 1e6:.1f} MB -> {out} ({time.time() - t0:.1f}s)')


if __name__ == '__main__':
    main()
