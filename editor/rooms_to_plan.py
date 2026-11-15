"""Convert the prototype's rooms (prototype/rooms.py) into Room Planner rooms.

  python editor/rooms_to_plan.py            -> editor/prototype_rooms.plan.json

Load the file with the planner's "Load file" button (or Claude seeds it into the planner's
shared storage). Mapping:
  props with an interaction -> Interactable (furniture-like ones stay Furniture, marked clickable)
  trees, bushes, flowers, rocks -> Decoration; other props -> Furniture
  exits -> Door / exit on the nearest edge, linked to the target room
  cameras -> Camera markers placed back along their view, with yaw/tilt as Camera facing/height
  camera zones, rugs, clearings -> Area; floor paths -> Path
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'prototype'))
from rooms import ROOMS  # noqa: E402

NAMES = {'bookshelf': 'Bookshelf', 'cauldron': 'Cauldron', 'table': 'Table with candle', 'bed': 'Bed', 'chest': 'Chest',
         'barrel': 'Barrel', 'tree': 'Oak tree', 'tree2': 'Oak tree', 'bush': 'Berry bush', 'bush2': 'Bush',
         'flowerbed': 'Flowerbed', 'flowerbed2': 'Flowerbed', 'mushroom': 'Red mushroom', 'mushroom_big': 'Big red mushroom',
         'well': 'Stone well', 'rocks': 'Rocks', 'signpost': 'Signpost', 'crystal_dim': 'Heart crystal', 'thorns': 'Thorn barrier'}
DECOR = {'tree', 'tree2', 'bush', 'bush2', 'flowerbed', 'flowerbed2', 'mushroom', 'mushroom_big', 'rocks', 'thorns', 'barrel'}
FURNITURE_LIKE = {'bookshelf', 'cauldron', 'table', 'bed', 'well'}
DETAILS = {   # what the prototype does with each interaction (game.js)
    'bookshelf': 'Clickable. First time: the witch learns the Spark spell from her grimoire.',
    'cauldron': 'Clickable. Flavour line: the brew smells of mint and thunder. Green brew glows.',
    'table': 'Clickable. Holds the fairy\'s note that starts the quest.',
    'bed': 'Clickable. Flavour line: no napping now.',
    'chest': 'Clickable. First time: gives a mana potion.',
    'well': 'Clickable. A voice hints at the fairy past the eastern gate.',
    'sign': 'Clickable. Reads "→ Whispering Forest".',
    'crystal': 'Cast Spark at it: it lights up and the thorn barrier disappears. Dark until then.',
    'fairy': 'Quest giver. Asks the witch to rekindle the heart crystal; thanks her afterwards. Floats and turns to face the player.',
}
ROOM_TEXT = {
    'cottage': dict(floor='Wooden planks', notes='Cosy one-room cottage. Near walls are cut away so the corner camera can see in.'),
    'garden': dict(floor='Grass with a stone path', notes='Fenced garden in front of the cottage. Two camera angles split at the middle.'),
    'forest': dict(floor='Dark grass with a dirt clearing', notes='Clearing ringed by trees. The fairy floats in a mushroom ring.'),
}


def size_of(block):
    r = max(block) if block else 4
    return 'S' if r < 5 else 'M' if r < 10 else 'L'


def mid(a, b):
    return round((a + b) / 2)


def convert(rid, r):
    W, D = r['size']
    n = 0
    def mid_id():
        nonlocal n; n += 1; return f'{rid}-{n}'
    out = dict(id=rid, name=r['name'], preset='custom', size=[W, D],
               setting='interior' if r['floor']['style'] == 'wood' else 'exterior',
               boundary='walls' if r.get('walls') and r['floor']['style'] == 'wood' else 'fence' if r.get('fences') else 'trees',
               floor=ROOM_TEXT.get(rid, {}).get('floor', ''), notes=ROOM_TEXT.get(rid, {}).get('notes', ''), markers=[], updated=0)
    M = out['markers']
    if 'start' in r:
        M.append(dict(id=mid_id(), kind='spawn', label='Player start', details='', x=r['start'][0], z=r['start'][1], size='M', face=r.get('start_face', 0) % 360))
    for p in r.get('props', []):
        a, it = p['asset'], p.get('interact')
        kind = 'decoration' if a in DECOR else 'item' if it and a not in FURNITURE_LIKE else 'furniture'
        M.append(dict(id=mid_id(), kind=kind, label=NAMES.get(a, a), details=DETAILS.get(it['id'], it['label']) if it else '',
                      x=p['pos'][0], z=p['pos'][1], size=size_of(p.get('block')), face=0 if kind != 'decoration' else None))
    for p in r.get('npcs', []):
        M.append(dict(id=mid_id(), kind='npc', label=p['asset'].title(), details=DETAILS.get(p['interact']['id'], ''),
                      x=p['pos'][0], z=p['pos'][1], size='M', face=p.get('face', 0) % 360))
    for e in r.get('exits', []):
        x0, z0, x1, z1 = e['rect']; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        d = {'N': cz, 'S': D - cz, 'W': cx, 'E': W - cx}; edge = min(d, key=d.get)
        pos = dict(N=(round(cx), 0), S=(round(cx), D), W=(0, round(cz)), E=(W, round(cz)))[edge]
        M.append(dict(id=mid_id(), kind='door', label=e['label'], details='', edge=edge, x=pos[0], z=pos[1],
                      width=round(x1 - x0) if edge in 'NS' else round(z1 - z0), to=e['to']))
    for run in r.get('walls', []):
        if run.get('window'):
            a, b = run['window']; sx, sz = run['start']
            x, z = (sx + (a + b) / 2, sz) if run['axis'] == 'x' else (sx, sz + (a + b) / 2)
            M.append(dict(id=mid_id(), kind='note', label='Window', details='Window in the wall here.', x=round(x), z=round(z), size='S', face=None))
    if rid == 'garden':
        M.append(dict(id=mid_id(), kind='area', label='Cottage outer wall (stone)', details='Stone wall with the cottage door and a window.', x=16, z=0, w=96, d=4))
    for i, c in enumerate(r['cameras']):
        y = c['yaw']; vx, vz = -math.sin(math.radians(y)), -math.cos(math.radians(y))   # view direction on the ground
        tx, tz = c['target']; px = min(max(tx - vx * 60, 0), W); pz = min(max(tz - vz * 60, 0), D)
        h = min(((26, 'low'), (32, 'medium'), (38, 'high')), key=lambda t: abs(t[0] - c['tilt']))[1]
        name = f'Camera {chr(65 + i)}' if len(r['cameras']) > 1 else 'Camera'
        M.append(dict(id=mid_id(), kind='camera', label=name, details=f'Fixed angle (rooms.py: yaw {y}, tilt {c["tilt"]}, zoom {c["zoom"]}).',
                      x=round(px), z=round(pz), face=round((180 - y) % 360), height=h))
        if c.get('zone'):
            x0, z0, x1, z1 = c['zone']
            M.append(dict(id=mid_id(), kind='area', label=f'{name} zone', details=f'{name} is used while the player is in here.', x=x0, z=z0, w=x1 - x0, d=z1 - z0))
    for dc in r['floor'].get('decals', []):
        if dc['kind'] == 'rug':
            x0, z0, x1, z1 = dc['rect']
            M.append(dict(id=mid_id(), kind='area', label='Purple rug', details='Purple with a gold border.', x=x0, z=z0, w=x1 - x0, d=z1 - z0))
        elif dc['kind'] == 'path':
            M.append(dict(id=mid_id(), kind='path', label='Stone path', details='', points=[list(p) for p in dc['points']], width=dc['width']))
        elif dc['kind'] == 'clearing':
            (cx, cz), rr = dc['center'], dc['radius']
            M.append(dict(id=mid_id(), kind='area', label='Dirt clearing (round)', details='Roughly circular patch of bare earth.', x=cx - rr, z=round(cz - rr / 1.15), w=2 * rr, d=round(2 * rr / 1.15)))
    for m in M:   # keep everything inside the room
        if 'x' in m and m['kind'] not in ('area',):
            m['x'] = min(max(m['x'], 0), W); m['z'] = min(max(m['z'], 0), D)
    return out


if __name__ == '__main__':
    plan = dict(format='room-planner/1', units='base units (rooms.py)', rooms=[convert(k, v) for k, v in ROOMS.items()])
    path = os.path.join(HERE, 'prototype_rooms.plan.json')
    json.dump(plan, open(path, 'w'), indent=1)
    for r in plan['rooms']:
        print(r['id'], r['size'], len(r['markers']), 'markers')
