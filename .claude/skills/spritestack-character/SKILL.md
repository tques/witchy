---
name: spritestack-character
description: Turn a 2D pixel-art sprite (or a written description) into a sprite-stacked 3D voxel character in this repo's house style, with walk/run/cast animations, viewer, turntable and engine atlas. Use when the user shares a sprite or asks for a new character, NPC, enemy or creature model, or wants an existing character changed or animated.
---

# Make a sprite-stacked character

The house style lives in `STYLE_GUIDE.md`. Read it before building. The witch (`characters/witch.py`) is the reference; new characters must look like they belong next to her.

## 1. Prepare the sprite

Save the user's image under `sprites/NAME_source.<ext>`, then:

```bash
python tools/prep_sprite.py sprites/NAME_source.png NAME
```

This writes:
- `sprites/NAME.png`: native size
- `sprites/NAME_grid.png`: 10× zoom with coordinates; read positions off it
- `sprites/NAME_palette.txt`

If it warns that the image isn't a clean pixel grid (AI-upscaled art), re-run with `--cell` (the witch and fairy used `--cell 15.9`) and check the grid image.

Copy the eye colours exactly:

```bash
python tools/prep_sprite.py sprites/NAME.png x --dump x0,y0,x1,y1
```

With no sprite, design directly in the style, as `characters/wizard.py` does.

## 2. Build it

```bash
python tools/new_character.py NAME
```

Then edit `characters/NAME.py`, working from the grid image:

- **Order:** props, head (with a flat face plate), hair, arms, body, legs, then face paint last. Earlier `put()` calls win.
- **Hair:** a solid base plus a FEW chunky strands (bangs, one or two curls), never many thin strands.
- **Eyes:** copy them from the sprite with `m.paint_eyes`. Painting is 3 cubes deep and unlit. No mouth or blush unless the sprite has them.
- **Trim:** stays flat. Push panels in with `m.recess_panel`. Use flat-ended cuffs via `m.cuffed_arm`.
- **Brims and capes:** use `m.brim`, level only. Wings and capes are vertical `m.membrane` sheets with `two_sided=True`.
- **Glowing parts:** `m.glow(part)`.
- **Off-centre bodies:** if the body isn't at the middle of the box, set `CENTER_X` (and a deeper `GRID` plus `CENTER_Z` for long props).

## 3. Check it

```bash
python -m spritestack.build characters/NAME.py --quick --views 0,35,90,180
```

Look at `out/NAME/views.png` and go through the review checklist in `STYLE_GUIDE.md`:
- eyes hold at 35°
- no plank stripes or seams
- hands clear of cuffs
- nothing pokes through hats
- the back has shape
- it matches the witch in scale and lighting

Fix and repeat. When the user is happy, run a full build without `--quick`.

## 4. Animate (if wanted)

Add `ANIMATIONS = {'walk': {}, 'run': {}}`. Mages also get `'cast_raise': {}, 'cast_hold': {}, 'cast_flick': {}, 'cast_lower': {}`.

Read motion from the presets: `g = gait(pose)` from `spritestack/gait.py` and `c = cast(pose)` from `spritestack/cast.py`, as `characters/witch.py` does. Override a preset per character (e.g. `dict(stride=4.5)` for an old man's walk) rather than writing new motion code.

With `pose=None`, the build must produce the standing model exactly.

Check the steps in `out/NAME/walk/frames.png`, and play everything in `out/NAME/play.html`.

## 5. Put it in the game (if it's an NPC)

1. Add it to the character list in `prototype/build_game.py` (e.g. `('NAME', ['stand', 'walk'])`).
2. Place it in `prototype/rooms.py` under `npcs`. Add `wander=dict(radius=…, pause=(…))` for a wanderer.
3. Add its lines in `interact()` in `prototype/game.js`.
4. Rebuild the game:

```bash
python prototype/build_game.py
```

## Deliver

Send the user:
- `out/NAME/views.png`
- `out/NAME/viewer.html`, or `play.html` for animated characters
- the turntable GIF

Say plainly what you designed yourself and what came from the sprite.
