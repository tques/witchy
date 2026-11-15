# spritestack

Turn 2D pixel-art character sprites into sprite-stacked 3D models in one consistent house style. The reference character is the witch. The rules are in [STYLE_GUIDE.md](STYLE_GUIDE.md).

Requires Python 3 with `numpy`, `scipy` and `pillow`:

```bash
pip install numpy scipy pillow
```

## New character in 4 steps

1. **Prepare the sprite.** The tool detects the pixel size of upscaled art, removes the background and crops:

   ```bash
   python tools/prep_sprite.py path/to/sprite.png knight
   ```

   This writes `sprites/knight.png` (native size), `sprites/knight_grid.png` (zoomed with coordinates) and `sprites/knight_palette.txt`. If it warns that the image isn't a clean pixel grid (AI-upscaled or filtered art), check the grid image and pass `--cell <size>`.

2. **Start from the template:**

   ```bash
   python tools/new_character.py knight
   ```

3. **Shape it.** Edit `characters/knight.py`:
   - Read positions off `sprites/knight_grid.png`.
   - Pick colours from the palette file.
   - Copy the eyes using the command below.

   ```bash
   python tools/prep_sprite.py sprites/knight.png x --dump 20,27,26,33
   ```

4. **Build and look.** The `--quick` build takes a few seconds and skips the GIF and viewer:

   ```bash
   python -m spritestack.build characters/knight.py --quick --views 0,35,90,180
   ```

   When it passes the checklist in the style guide, run a full build:

   ```bash
   python -m spritestack.build characters/knight.py
   ```

## Outputs (`out/NAME/`)

| file | what |
|---|---|
| `viewer.html` | self-contained drag-to-rotate viewer |
| `turntable.gif` | 36-frame spin |
| `sheet.png` | front, side, back and side views |
| `views.png` | angles from `--views`, for review |
| `atlas.png` + `meta.json` | layers for a game engine: H slices of W × D stacked top to bottom; draw bottom slice first, each one a pixel higher |
| `volume.npy` | raw RGBA voxels `[y][z][x]` |
| `play.html`, `walk.*`, `run.*` | animations, if the character has any (see below) |

## Animations

Each animation frame is the character rebuilt with a pose. The gait module (`spritestack/gait.py`) does the motion maths, so a character only says which parts follow which limb.

```python
from spritestack.gait import gait

ANIMATIONS = {'walk': {}, 'run': {}}          # presets; override per character, e.g. {'run': dict(stride=8)}

def build(m, sprite, pose=None):              # pose None = standing (every offset is exactly 0)
    g = gait(pose)
    g.apply(m, pivot_y=FEET_Y)                # body bob + running lean
    dz, dy = g.foot(side)                     # boot offset; side -1 = screen-left, +1 = screen-right
    g.arm(side), g.arm_lift(side)             # free hand forward/up
    g.prop_arm(side)                          # a hand holding something (swings less)
    g.hem(side)(y)                            # skirt half follows its leg (and trails when running)
    g.trail                                   # 0..1: stream hair, capes, hat tips backward
```

The presets are tuned on the witch:

| preset | frames, fps | stride | lift / heel kick | bob | lean | trail |
|---|---|---|---|---|---|---|
| walk | 8 @ 10 | 5.5 | 2.6 / 0 | +1 as feet pass | none | 0 |
| run | 8 @ 18 | 9 | 4.5 / 3 | +2 in flight | 0.09 | 1 |

Ground speed is derived from the stride, so feet don't slide. To add a new gait (sneak, skip, march), add an entry to `PRESETS`.

Outputs in `out/NAME/`:

| file | what |
|---|---|
| `play.html` | buttons for every animation; drag or ← → to steer; hold Shift to run; Space to cast |
| `walk.gif`, `run.gif`, `cast_*.gif` | each animation over the ground (one-shots shown between their hold loops) |
| `walk/atlas.png`, `run/atlas.png` + `meta.json` | frames left to right, each a column of H slices (W × D); meta has fps and speed |
| `walk/frames.png`, `run/frames.png` | every frame from the side, for checking the steps |

### Spellcasting (`spritestack/cast.py`)

Any mage can use the cast presets. They chain: `cast_raise` (once, prop comes up) → `cast_hold` (loop) → `cast_flick` (once, from and back into the hold) → `cast_lower` (once, prop goes back down).

```python
from spritestack.cast import cast

ANIMATIONS = {..., 'cast_raise': {}, 'cast_hold': {}, 'cast_flick': {}, 'cast_lower': {}}

c = cast(pose)                                   # inert unless a cast animation
c.apply(m, pivot_y=FEET_Y)                       # small lean: back on the wind-up, forward on the snap
hand = c.hand(rest_hand, raised_hand)            # casting hand position
aim = c.aim(rest_dir, cast_dir)                  # prop direction, with wind-up / snap pitch
butt, tip = c.place([butt, tip], grip, rest_dir, hand, aim)   # re-aim a rigid prop around its grip
R = c.rotation(rest_dir, aim)                    # for oriented shapes: m.ell_oriented(centre, radii, R)
m.cuffed_arm_to(shoulder, hand, ...)             # arm that reaches the hand
m.glow('orb', boost=1 + 0.3 * c.pulse)           # pulsing focus
m.sparkle(c.sparkles(tip, aim), colour, size=c.sparkle_size)   # orbiting motes / burst ring
for p, size in c.bolt(tip, aim): m.sparkle([p], white, size=size)  # released bolt + trail
c.breeze                                         # 0..1 magic wind for hair and hems (like gait.trail)
```

| preset | frames, fps | what happens |
|---|---|---|
| cast_raise / cast_lower | 6 @ 12, once | prop eases up into the hold (or back down), focus and motes fade in (or out) |
| cast_hold | 8 @ 8, loop | prop raised and swaying ±4°, focus pulses, 6 motes circle it, light breeze |
| cast_flick | 10 @ 14, once | wind back −35°, snap to +22°, release at 42%: bolt and burst ring, then settle into the hold |

Keep the standing code path untouched (`if not c.active:`) so the approved standing model can't change. Aim the raised prop up and out to the side so it never covers the face. In `play.html`, Space casts.

**Centring:** engines and viewers spin each slice around its middle. If a character is modelled off-centre (the witch sits at x=23 to leave room for her staff), set `CENTER_X` to the body's centre line. For props that reach far forward (a raised staff), use a deeper `GRID` and set `CENTER_Z` to its middle. The build sizes one box to fit the standing pose and every frame, with the body centred in it.

### Showcase sequences

Chain any built animations into one GIF, for previews and pitches:

```bash
python tools/sequence.py witch "stand:1s walk:2 run:3 walk:1 stand:0.6s cast_raise cast_hold:1 cast_flick cast_hold:2" --labels
```

- Steps are `name:cycles` or `name:seconds` followed by `s`. `stand` is the standing pose.
- The ground scrolls at each animation's own speed.
- `--orbit 40` swings the camera across the sequence to show off the 3D.
- Output goes to `out/NAME/sequence.gif`.

## Layout

```
spritestack/style.py      house-style numbers (light, bands, face, camera)
spritestack/model.py      Model: shapes, brim, membrane, cuffed_arm, recess_panel, paint_eyes, lean, shade
spritestack/gait.py       walk/run presets: feet, arms, hem, bob, lean, trail, ground speed
spritestack/cast.py       cast_hold / cast_flick presets: raise, aim, wind-up, snap, pulse, sparkles, bolt
spritestack/render.py     preview frames, turntable, sheet, atlas, viewer
spritestack/build.py      build command
characters/witch.py       reference character
characters/fairy.py       winged character (membranes, antennae, leaf skirt)
characters/_template.py   starting point for new characters
tools/prep_sprite.py      sprite prep: pixel size, background, grid, palette, colour dump
tools/new_character.py    copy the template
tools/sequence.py         chain animations into a showcase GIF
prototype/                click-to-move adventure/RPG prototype built from sprite stacks (see prototype/README.md)
editor/                   Room Planner: lay out rooms with text markers for Claude to build (see editor/README.md)
```

Changing a value in `style.py` changes every character on its next build. Rebuild all characters with:

```bash
for f in characters/[!_]*.py; do python -m spritestack.build "$f"; done
```
