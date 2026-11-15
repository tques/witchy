"""Room layouts for the prototype, in BASE units. build_game.py multiplies every coordinate by
WORLD_SCALE (props are enlarged by the same factor) so the rooms fit the witch, who is built at one
cube per sprite pixel (~88 cubes tall).

x runs east, z runs south (toward the default camera), the ground is y = 0. Walls are listed as
straight runs and get split into 16-unit segments so the renderer can depth-sort them.

Each room:
  size        (width_x, depth_z)
  floor       floor style + decals drawn on the ground texture
  walls       runs: dict(start=(x, z), axis, length, height, kind, door/window=(from, to) along the run)
              doors and windows must sit inside one 16-unit segment (e.g. 50..62 or 34..46)
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
        name="Witch's Cottage", size=(112, 84), start=(74, 66), start_face=160,
        floor=dict(style='wood', decals=[dict(kind='rug', rect=(36, 30, 82, 64))]),
        walls=[dict(start=(0, 0), axis='x', length=112, height=44, kind='cottage', door=(50, 62)),
               dict(start=(0, 4), axis='z', length=76, height=44, kind='cottage', window=(34, 46)),
               dict(start=(0, 80), axis='x', length=112, height=8, kind='cottage'),          # cut-away near walls
               dict(start=(108, 4), axis='z', length=76, height=8, kind='cottage')],
        props=[dict(asset='bookshelf', pos=(22, 8), block=(14, 5), interact=dict(id='bookshelf', label='Examine bookshelf', at=(22, 24))),
               dict(asset='cauldron', pos=(58, 46), block=(12, 12), interact=dict(id='cauldron', label='Look in the cauldron', at=(58, 64))),
               dict(asset='table', pos=(90, 22), block=(14, 9), interact=dict(id='table', label='Read the note', at=(90, 38))),
               dict(asset='bed', pos=(15, 56), block=(12, 19), interact=dict(id='bed', label='Bed', at=(32, 56))),
               dict(asset='chest', pos=(94, 68), block=(9, 7), interact=dict(id='chest', label='Open chest', at=(94, 54))),
               dict(asset='barrel', pos=(102, 11), block=(7, 7))],
        exits=[dict(rect=(50, 0, 62, 10), to='garden', spawn=(56, 18), face=0, label='Go outside')],
        cameras=[dict(zone=None, yaw=32, tilt=36, zoom=4.4, target=(56, 44))],
    ),
    'garden': dict(
        name='Garden', size=(176, 120),
        floor=dict(style='grass', decals=[dict(kind='path', points=[(56, 6), (58, 36), (84, 58), (130, 62), (176, 62)], width=14)]),
        walls=[dict(start=(16, 0), axis='x', length=96, height=44, kind='stone', door=(34, 46), window=(66, 78))],
        fences=[dict(start=(0, 8), axis='z', length=108),
                dict(start=(0, 116), axis='x', length=58), dict(start=(82, 116), axis='x', length=94),   # gap = south gate
                dict(start=(172, 8), axis='z', length=40), dict(start=(172, 76), axis='z', length=40),
                dict(start=(112, 4), axis='x', length=60)],
        props=[dict(asset='well', pos=(128, 30), block=(13, 13), interact=dict(id='well', label='Peer into the well', at=(128, 50))),
               dict(asset='flowerbed', pos=(30, 16), block=(13, 6)), dict(asset='flowerbed2', pos=(88, 16), block=(13, 6)),
               dict(asset='barrel', pos=(106, 14), block=(7, 7)),
               dict(asset='tree', pos=(20, 96), block=(6, 6)), dict(asset='tree2', pos=(154, 98), block=(6, 6)),
               dict(asset='bush', pos=(92, 104), block=(9, 9)), dict(asset='bush2', pos=(50, 106), block=(9, 9)),
               dict(asset='mushroom', pos=(36, 82)), dict(asset='mushroom', pos=(42, 88)), dict(asset='rocks', pos=(118, 96), block=(7, 5)),
               dict(asset='signpost', pos=(160, 46), block=(3, 2), interact=dict(id='sign', label='Read sign', at=(154, 56)))],
        exits=[dict(rect=(50, 0, 62, 10), to='cottage', spawn=(56, 18), face=0, label='Go inside'),
               dict(rect=(168, 48, 176, 76), to='forest', spawn=(14, 60), face=270, label='To the forest'),
               dict(rect=(58, 112, 82, 120), to='field', spawn=(54, 18), face=0, label='To the field')],
        cameras=[dict(zone=(0, 0, 88, 120), yaw=-28, tilt=34, zoom=4.0, target=(54, 56)),
                 dict(zone=(88, 0, 176, 120), yaw=38, tilt=30, zoom=4.0, target=(126, 60))],
    ),
    'forest': dict(
        name='Forest Clearing', size=(150, 120),
        floor=dict(style='forest', decals=[dict(kind='clearing', center=(82, 60), radius=42),
                                           dict(kind='path', points=[(0, 60), (36, 60), (58, 58)], width=14)]),
        props=[dict(asset='tree', pos=(18, 18), block=(6, 6)), dict(asset='tree2', pos=(54, 8), block=(6, 6)),
               dict(asset='tree', pos=(96, 6), block=(6, 6)), dict(asset='tree2', pos=(140, 30), block=(6, 6)),
               dict(asset='tree', pos=(142, 82), block=(6, 6)), dict(asset='bush2', pos=(18, 100), block=(9, 9)),
               dict(asset='tree', pos=(128, 112), block=(6, 6)),
               dict(asset='bush', pos=(54, 112), block=(9, 9)), dict(asset='bush2', pos=(92, 114), block=(9, 9)),
               dict(asset='bush', pos=(10, 38), block=(9, 9)), dict(asset='rocks', pos=(36, 92), block=(7, 5)),
               dict(asset='thorns', pos=(124, 10), block=(17, 6)),
               dict(asset='crystal_dim', pos=(116, 40), block=(8, 8), swap='crystal_lit',
                    interact=dict(id='crystal', label='The dark crystal', at=(92, 74))),        # cast from a few steps away
               *[dict(asset='mushroom_big' if i in (2, 6) else 'mushroom',
                      pos=(round(82 + 24 * math.cos(i * 0.785 + 0.3)), round(58 + 17 * math.sin(i * 0.785 + 0.3))))
                 for i in range(8) if i != 2]],          # a gap in the ring faces the path
        npcs=[dict(asset='fairy', pos=(82, 56), face=200, bob=3, interact=dict(id='fairy', label='Talk to the fairy', at=(82, 80)))],
        exits=[dict(rect=(0, 46, 8, 74), to='garden', spawn=(160, 62), face=90, label='Back to the garden')],
        cameras=[dict(zone=None, yaw=-22, tilt=29, zoom=4.0, target=(78, 58))],
    ),
    'field': dict(
        name='Field', size=(280, 192),
        floor=dict(style='meadow', decals=[]),
        props=[# from the planner, scaled to the larger field
               dict(asset='stump', pos=(73, 74), block=(8, 8),
                    interact=dict(id='stump', label='Examine the tree stump', at=(73, 92))),
               dict(asset='boulder', pos=(140, 90), block=(12, 10)),
               dict(asset='wildflowers', pos=(29, 42)), dict(asset='wildflowers2', pos=(32, 144)),
               dict(asset='wildflowers2', pos=(207, 29)), dict(asset='wildflowers', pos=(210, 144)),
               dict(asset='wildflowers2', pos=(251, 58)),
               # added so the bigger field doesn't feel empty
               dict(asset='pond', pos=(104, 146), block=(19, 13),
                    interact=dict(id='pond', label='Look into the pond', at=(104, 168))),
               dict(asset='log', pos=(196, 112), block=(15, 5)),
               dict(asset='wildflowers', pos=(118, 40)), dict(asset='wildflowers2', pos=(160, 168)),
               dict(asset='wildflowers', pos=(256, 110)), dict(asset='wildflowers2', pos=(60, 118)),
               dict(asset='rocks', pos=(36, 100), block=(7, 5)), dict(asset='rocks', pos=(246, 166), block=(7, 5)),
               dict(asset='rocks', pos=(166, 66), block=(7, 5)),
               dict(asset='mushroom', pos=(176, 40)), dict(asset='mushroom_big', pos=(181, 45)), dict(asset='mushroom', pos=(172, 47)),
               dict(asset='mushroom', pos=(58, 176)), dict(asset='mushroom', pos=(63, 181)),
               dict(asset='tree2', pos=(96, 66), block=(6, 6)), dict(asset='tree', pos=(236, 82), block=(6, 6)),
               # north edge: the garden's fence borders x -16..160 (it is only 176 long); trees continue the edge east of it
               dict(asset='tree', pos=(182, 8), block=(6, 6)), dict(asset='tree2', pos=(226, 4), block=(6, 6)),
               dict(asset='tree', pos=(268, 10), block=(6, 6)),
               dict(asset='bush', pos=(8, 70), block=(9, 9)), dict(asset='bush2', pos=(8, 128), block=(9, 9)),
               dict(asset='bush', pos=(272, 56), block=(9, 9)), dict(asset='bush2', pos=(272, 136), block=(9, 9)),
               dict(asset='bush', pos=(46, 186), block=(9, 9)), dict(asset='bush2', pos=(132, 188), block=(9, 9)),
               dict(asset='bush', pos=(222, 186), block=(9, 9))],
        npcs=[dict(asset='wizard', pos=(210, 96), face=0, wander=dict(radius=48, pause=(1.5, 4.0)),
                   interact=dict(id='wizard', label='Talk to the wizard', at=(210, 112)))],
        exits=[dict(rect=(42, 0, 66, 10), to='garden', spawn=(70, 104), face=180, label='Back to the garden')],
        # four quadrants, each with its own fixed angle; all look north-ish so the tree edge stays at the back
        cameras=[dict(zone=(0, 96, 140, 192), yaw=-45, tilt=32, zoom=3.6, target=(70, 138)),
                 dict(zone=(140, 96, 280, 192), yaw=45, tilt=32, zoom=3.6, target=(210, 138)),
                 dict(zone=(0, 0, 140, 96), yaw=-30, tilt=34, zoom=3.6, target=(70, 54)),
                 dict(zone=(140, 0, 280, 96), yaw=30, tilt=34, zoom=3.6, target=(210, 54))],
    ),
}
