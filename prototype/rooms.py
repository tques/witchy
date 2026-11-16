"""Room layouts for the prototype, in BASE units. build_game.py multiplies every coordinate by
WORLD_SCALE (props are enlarged by the same factor) so the rooms fit the witch, who is built at one
cube per sprite pixel (~88 cubes tall).

x runs east, z runs south (toward the default camera), the ground is y = 0. Walls are listed as
straight runs and get split into 16-unit segments so the renderer can depth-sort them.

Each room:
  size        (width_x, depth_z)
  floor       floor style + decals drawn on the ground texture
  walls       runs: dict(start=(x, z), axis, length, height, kind, door/window=(from, to) along the run)
              doors and windows must sit inside one 16-unit segment (e.g. 50..62 or 66..78)
  fences      runs like walls
  props       dict(asset, pos, block=(half_x, half_z) footprint, interact=dict(id, label, at=(x, z)))
  npcs        dict(asset, pos, face, bob, interact={...})
  exits       dict(rect=(x0, z0, x1, z1), to=room, spawn=(x, z), face=degrees)
              face: 0 = facing south (+z, toward the camera side), 90 = west, 180 = north, 270 = east
  cameras     dict(zone=(x0, z0, x1, z1) or None, yaw, tilt, zoom, target=(x, z))
              zoom is screen pixels per BASE unit
"""
import math

WORLD_SCALE = 2.5

ROOMS = {
    'cottage': dict(
        name="Witch's Cottage", size=(140, 105), start=(92, 82), start_face=160,
        floor=dict(style='wood', decals=[dict(kind='rug', rect=(45, 38, 102, 80))]),
        walls=[dict(start=(0, 0), axis='x', length=140, height=44, kind='cottage', door=(66, 78)),
               dict(start=(0, 4), axis='z', length=97, height=44, kind='cottage', window=(50, 62)),
               dict(start=(0, 101), axis='x', length=140, height=8, kind='cottage'),          # cut-away near walls
               dict(start=(136, 4), axis='z', length=97, height=8, kind='cottage')],
        props=[dict(asset='bookshelf', pos=(28, 10), block=(14, 5), interact=dict(id='bookshelf', label='Examine bookshelf', at=(28, 30))),
               dict(asset='cauldron', pos=(72, 58), block=(12, 12), interact=dict(id='cauldron', label='Look in the cauldron', at=(72, 80))),
               dict(asset='table', pos=(112, 28), block=(14, 9), interact=dict(id='table', label='Read the note', at=(112, 48))),
               dict(asset='bed', pos=(19, 70), block=(12, 19), interact=dict(id='bed', label='Bed', at=(40, 70))),
               dict(asset='chest', pos=(118, 85), block=(9, 7), interact=dict(id='chest', label='Open chest', at=(118, 68))),
               dict(asset='barrel', pos=(128, 14), block=(7, 7))],
        exits=[dict(rect=(66, 0, 78, 10), to='garden', spawn=(70, 22), face=0, label='Go outside')],
        cameras=[dict(zone=None, yaw=32, tilt=36, zoom=4.4, target=(70, 55))],
    ),
    'garden': dict(
        name='Garden', size=(220, 150),
        floor=dict(style='grass', decals=[dict(kind='path', points=[(70, 8), (72, 45), (105, 72), (162, 78), (220, 78)], width=14)]),
        walls=[dict(start=(16, 0), axis='x', length=120, height=44, kind='stone', door=(48, 60), window=(82, 94))],
        fences=[dict(start=(0, 10), axis='z', length=135),
                dict(start=(0, 145), axis='x', length=72), dict(start=(102, 145), axis='x', length=118),   # gap = south gate
                dict(start=(216, 10), axis='z', length=50), dict(start=(216, 95), axis='z', length=50),
                dict(start=(136, 4), axis='x', length=84)],
        props=[dict(asset='well', pos=(160, 38), block=(13, 13), interact=dict(id='well', label='Peer into the well', at=(160, 62))),
               dict(asset='flowerbed', pos=(38, 20), block=(13, 6)), dict(asset='flowerbed2', pos=(110, 20), block=(13, 6)),
               dict(asset='barrel', pos=(132, 18), block=(7, 7)),
               dict(asset='tree', pos=(25, 120), block=(6, 6)), dict(asset='tree2', pos=(192, 122), block=(6, 6)),
               dict(asset='bush', pos=(115, 130), block=(9, 9)), dict(asset='bush2', pos=(62, 132), block=(9, 9)),
               dict(asset='mushroom', pos=(45, 102)), dict(asset='mushroom', pos=(52, 110)), dict(asset='rocks', pos=(148, 120), block=(7, 5)),
               dict(asset='signpost', pos=(200, 58), block=(3, 2), interact=dict(id='sign', label='Read sign', at=(192, 70)))],
        exits=[dict(rect=(64, 0, 76, 10), to='cottage', spawn=(70, 22), face=0, label='Go inside'),
               dict(rect=(210, 60, 220, 95), to='forest', spawn=(18, 75), face=270, label='To the forest'),
               dict(rect=(72, 140, 102, 150), to='field', spawn=(68, 22), face=0, label='To the field')],
        cameras=[dict(zone=(0, 0, 110, 150), yaw=-28, tilt=34, zoom=4.0, target=(68, 70)),
                 dict(zone=(110, 0, 220, 150), yaw=38, tilt=30, zoom=4.0, target=(158, 75))],
    ),
    'forest': dict(
        name='Forest Clearing', size=(188, 150),
        floor=dict(style='forest', decals=[dict(kind='clearing', center=(102, 75), radius=52),
                                           dict(kind='path', points=[(0, 75), (45, 75), (72, 72)], width=14)]),
        props=[dict(asset='tree', pos=(22, 22), block=(6, 6)), dict(asset='tree2', pos=(68, 10), block=(6, 6)),
               dict(asset='tree', pos=(120, 8), block=(6, 6)), dict(asset='tree2', pos=(175, 38), block=(6, 6)),
               dict(asset='tree', pos=(178, 102), block=(6, 6)), dict(asset='tree2', pos=(22, 125), block=(6, 6)),
               dict(asset='tree', pos=(160, 140), block=(6, 6)), dict(asset='tree', pos=(118, 112), block=(6, 6)),
               dict(asset='bush2', pos=(115, 142), block=(9, 9)),
               dict(asset='bush', pos=(12, 48), block=(9, 9)), dict(asset='rocks', pos=(45, 115), block=(7, 5)),
               dict(asset='thorns', pos=(155, 12), block=(17, 6)),
               dict(asset='crystal_dim', pos=(145, 50), block=(8, 8), swap='crystal_lit',
                    interact=dict(id='crystal', label='The dark crystal', at=(115, 92))),        # cast from a few steps away
               *[dict(asset='mushroom', pos=p) for p in ((138, 72), (130, 95), (88, 82), (95, 48), (120, 55))]],   # small ring round the fairy
        npcs=[dict(asset='fairy', pos=(102, 70), face=200, bob=3, interact=dict(id='fairy', label='Talk to the fairy', at=(102, 100)))],
        exits=[dict(rect=(0, 58, 10, 92), to='garden', spawn=(200, 78), face=90, label='Back to the garden')],
        cameras=[dict(zone=None, yaw=-22, tilt=29, zoom=4.0, target=(98, 72))],
    ),
    'field': dict(
        name='Field', size=(350, 240),
        floor=dict(style='meadow', decals=[]),
        props=[# from the planner, scaled to the larger field
               dict(asset='stump', pos=(91, 92), block=(8, 8),
                    interact=dict(id='stump', label='Examine the tree stump', at=(91, 115))),
               dict(asset='boulder', pos=(175, 112), block=(12, 10)),
               dict(asset='wildflowers', pos=(36, 52)), dict(asset='wildflowers2', pos=(40, 180)),
               dict(asset='wildflowers2', pos=(259, 36)), dict(asset='wildflowers', pos=(262, 180)),
               dict(asset='wildflowers2', pos=(314, 72)),
               # added so the bigger field doesn't feel empty
               dict(asset='pond', pos=(130, 182), block=(19, 13),
                    interact=dict(id='pond', label='Look into the pond', at=(130, 210))),
               dict(asset='log', pos=(245, 140), block=(15, 5)),
               dict(asset='wildflowers', pos=(148, 50)), dict(asset='wildflowers2', pos=(200, 210)),
               dict(asset='wildflowers', pos=(320, 138)), dict(asset='wildflowers2', pos=(75, 148)),
               dict(asset='rocks', pos=(45, 125), block=(7, 5)), dict(asset='rocks', pos=(308, 208), block=(7, 5)),
               dict(asset='rocks', pos=(208, 82), block=(7, 5)),
               dict(asset='mushroom', pos=(220, 50)), dict(asset='mushroom_big', pos=(226, 56)), dict(asset='mushroom', pos=(215, 59)),
               dict(asset='mushroom', pos=(72, 220)), dict(asset='mushroom', pos=(79, 226)),
               dict(asset='tree2', pos=(120, 82), block=(6, 6)), dict(asset='tree', pos=(295, 102), block=(6, 6)),
               # north edge: the garden's fence borders part of it (the garden is only 220 wide); trees continue the edge east of it
               dict(asset='tree', pos=(228, 10), block=(6, 6)), dict(asset='tree2', pos=(282, 5), block=(6, 6)),
               dict(asset='tree', pos=(335, 12), block=(6, 6)),
               dict(asset='bush', pos=(10, 88), block=(9, 9)), dict(asset='bush2', pos=(10, 160), block=(9, 9)),
               dict(asset='bush', pos=(340, 70), block=(9, 9)), dict(asset='bush2', pos=(340, 170), block=(9, 9)),
               dict(asset='bush', pos=(58, 232), block=(9, 9)), dict(asset='bush2', pos=(165, 235), block=(9, 9)),
               dict(asset='bush', pos=(278, 232), block=(9, 9))],
        npcs=[dict(asset='wizard', pos=(262, 120), face=0, wander=dict(radius=60, pause=(1.5, 4.0)),
                   interact=dict(id='wizard', label='Talk to the wizard', at=(262, 140)))],
        exits=[dict(rect=(52, 0, 82, 12), to='garden', spawn=(88, 130), face=180, label='Back to the garden')],
        # two halves, each seen from its southern corner (from the planner)
        cameras=[dict(zone=(0, 0, 174, 240), yaw=-45, tilt=32, zoom=3.6, target=(87, 120)),     # A: south-west corner, looking north-east
                 dict(zone=(174, 0, 350, 240), yaw=45, tilt=32, zoom=3.6, target=(262, 120))],  # B: south-east corner, looking north-west
    ),
}
