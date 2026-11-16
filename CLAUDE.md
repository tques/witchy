# witchy: sprite-stacked 3D characters and a small adventure RPG

This repo turns 2D pixel-art sprites into sprite-stacked voxel models in one house style, and uses them in a click-to-move adventure/RPG prototype. Read `README.md` for the workflow and `STYLE_GUIDE.md` for the look. Follow the style guide whenever you make or change a character or prop.

## Setup

```bash
pip install -r requirements.txt
```

Browser checks use Playwright. In Claude Code cloud sessions it's preinstalled; use `require('playwright')` from node and don't reinstall it.

## Layout

- `spritestack/`: the toolkit.
  - `style.py`: house-style numbers.
  - `model.py`: shapes, brims, membranes, cuffs, eyes, lean, `scaled()`, shading.
  - `gait.py`: walk and run.
  - `cast.py`: spellcasting.
  - `render.py`, `build.py`.
- `characters/`:
  - `witch.py`: the reference character. Its standing pose must never change.
  - `fairy.py`, `wizard.py`.
  - `_template.py`: start new characters from this.
- `tools/`:
  - `prep_sprite.py`: sprite pixel size, background removal, grid, palette, `--dump` for colours.
  - `new_character.py`.
  - `sequence.py`: showcase GIFs.
- `prototype/`: the game.
  - `rooms.py`: layouts in base units.
  - `props.py`: environment props.
  - `game.js`, `build_game.py`.
  - Output: `witch_rpg.html`.
- `editor/`: the Room Planner (`room_planner.html`) and `rooms_to_plan.py`.
- `out/NAME/`: built viewers, GIFs and atlases. Committed, except `volume.npy`.

## Commands

```bash
python -m spritestack.build characters/NAME.py --quick --views 0,35,90,180   # iterate: writes out/NAME/views.png
```

```bash
python -m spritestack.build characters/NAME.py                               # full build: viewer, GIFs, play.html
```

```bash
python prototype/build_game.py                                              # rebuild the game after any character/prop/room change
```

Build characters before the game; the game reads their atlases from `out/`.

## Conventions

- **Scale:** one sprite pixel = one cube. The witch is about 88 cubes tall.
- **Units:** rooms and props are designed in **base units** and enlarged by `WORLD_SCALE = 2.5` (`prototype/rooms.py`) at bake time. In base units the witch is about 35 tall and 14 wide.
- **Axes:** x runs east, z runs south, (0, 0) is a room's north-west corner, and the ground is height 0.
- **Facing:** 0 = south (toward the camera side), 90 = west, 180 = north, 270 = east.
- **Camera yaw (rooms.py):** 0 looks north; positive yaws look north-west. A planner camera's facing `f` becomes yaw `180 − f`.
- **Wall segments:** walls split into 16-unit segments. Doors and windows must sit inside one segment (e.g. 50–62 or 34–46).
- **Thin flat parts:** keep them level, never slightly tilted, or plank stripes appear. Wings and capes are vertical membranes.
- **Animation:** every frame is the character rebuilt with a pose. Use the presets in `gait.py` and `cast.py`. With no pose, `build()` must produce the approved standing model exactly.

## The Room Planner

The user lays out rooms in the published planner at https://claude.ai/artifact/RNMHtaN12iw2kwvPsGanTb. Each room is a document in its `rooms` collection. Read it with the `ArtifactData` tool (`list` or `get`, collection `rooms`, that URL) instead of asking the user to paste a brief.

Use the `planner-room` skill to turn a planner room into a game room, and the `spritestack-character` skill to make a character from a sprite.

When you write back to a planner room, read it first and pass `if_version`. Keep the user's marker ids. Label anything you add "Added by Claude".

## How to check your work

- **Characters:** look at `out/NAME/views.png` (0°, 35°, 90°, 180°). Check:
  - eyes hold at 35°
  - no plank stripes or dark seams
  - hands are clear of cuffs
  - nothing pokes through hats
  - the back view has shape

  Compare with the witch in a lineup.
- **The game:** drive `prototype/witch_rpg.html` with Playwright:
  - use `window.__S` (state) and `window.__G` (`enterRoom`, `walkTo`, `targetsAt`, `proj`, `interact`, `act`, `findPath`)
  - screenshot every room and camera zone you touched
  - make sure there are no page errors and about 60 fps
- **When you change something the witch uses** (`spritestack/`, `characters/witch.py`), confirm her standing pose and walk come out cube-for-cube identical. Compare contents after cropping, because box sizes can change.

## Git

The user reviews work on branches and asks for merges into `main`.

**Never merge `claude/trusting-dirac-d8tdu2` into `main`.** That branch holds the sci-fi grav-ball characters (`striker`, `heavyworlder`), a side experiment that doesn't belong in the witch RPG. Keep it as its own branch: don't merge, rebase or cherry-pick it into `main`, and don't open a pull request for it, even if asked to "merge everything".
