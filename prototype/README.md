# Witch RPG prototype

A small click-to-move adventure/RPG built entirely from sprite stacks. Open `witch_rpg.html` in a browser; it's self-contained.

**Rooms:**
- the witch's cottage
- the garden, with two camera zones that cut as she crosses
- a forest clearing with the fairy

**Quest:** read the note, learn Spark from the bookshelf, find the fairy, then cast at the dark crystal.

## Controls

- Click the ground to walk; double-click to run.
- Hover to see what can be used. Click objects, the fairy or doorways to walk over and interact.
- Space or a click advances dialogue. The Potion button refills mana.

## How it's built

| file | what |
|---|---|
| `rooms.py` | room layouts in base units: walls, fences, props, NPCs, exits, camera zones, floor decals |
| `props.py` | environment props (walls, furniture, trees, well, crystal…) built with the spritestack toolkit and house lighting |
| `build_game.py` | bakes every prop and the witch/fairy animations into atlases and writes `witch_rpg.html` |
| `game.js` | the engine: fixed cameras, sprite-stack renderer, A* click-to-move, interactions, dialogue, quest, casting |
| `game_template.html` | page layout and HUD |

Rebuild after changing characters, props or rooms (build the characters first):

```bash
python -m spritestack.build characters/witch.py
```

```bash
python -m spritestack.build characters/fairy.py
```

```bash
python prototype/build_game.py
```

**Scale.** Characters are one cube per sprite pixel, about 88 cubes tall. Rooms and props are designed in smaller base units and enlarged by `WORLD_SCALE` (2.5) at bake time, using `Model.scaled()`. That keeps props in proportion to the characters, and the lighting is computed at full resolution.

**Screen size.** The game renders at 1920 × 1080 and scales to fit the browser window. `VIEW_SCALE` in `game.js` (1.5) sets how big the world is drawn on screen; at 1080p the witch is about 180 pixels tall. Rooms were laid out 1.25× larger for this view, so they fill the screen without feeling cramped.

**Cameras.** Each camera zone has a camera that is either a **fixed shot** (interiors, composed views) or **follows** the player (`follow=True` in `rooms.py`, "Follows player" in the planner). A following camera keeps its angle and only slides: she can move inside a dead zone in the middle of the screen, then it eases after her, stops at the room's edges, and moves in whole pixels so the art doesn't shimmer. Crossing into another zone still cuts to that zone's camera. Rooms with `outskirts='trees'` get a look-only border of trees just outside their edges (bushes and rocks on the camera's south side), so a following camera never shows bare ground at the edge.

*Built for a turning camera later.* Each camera is its settings plus a live pose (yaw, tilt, zoom, centre) that `updateCamera()` advances every frame; drawing, clicking, the floor and the dead zone all read the pose and work at any angle. A `turn` mode would ease `pose.yaw` too. Stack images are cached per angle, so a turning camera should round its yaw (say to 3°) to keep that cache small.

**Out of bounds.** All ground outside the current room is drawn darker (`OUT_OF_BOUNDS` in `game.js`, 0.7), including a neighbouring room's ground and paths, so the walkable area always reads clearly. Props outside keep their normal colours.

**Rendering.**
- Each room or zone has a fixed camera (yaw, tilt, zoom).
- Walls on the camera side are cut away, dollhouse style.
- Walls and fences are split into short segments, and everything is depth-sorted per frame.
- Every stack is rendered once per camera, facing and frame into a cached image, so a frame is a few dozen image draws. It runs at about 60 fps.
- Anything that covers the witch fades out.
- Clicks and hovers are pixel-accurate against those cached images.

**Movement.** Walking and running speeds come from the animation strides (played 1.4× and 1.25× faster in-game for pacing), so feet don't slide.

**Neighbouring rooms.** Outdoor rooms are placed relative to each other by lining up each pair of linked exits, gate to gate (`build_game.py` prints the offsets). Past a room's edge you see the neighbour's real ground, paths, fences and props, at their true positions and lengths. They're for looking only: no clicks and no walking. A neighbour's fence covers only its own length, so the rest of a longer edge keeps that room's own border (the Field's tree line continues east of where the garden ends). Indoor rooms don't show neighbours.

## Adding a room

1. Add an entry to `ROOMS` in `rooms.py`. Doors and windows must sit inside one 16-unit wall segment.
2. Point an exit in another room at it.
3. Add any new props to `props.PROPS`.
4. Rebuild.

Interactions are handled in `interact()` in `game.js`.
