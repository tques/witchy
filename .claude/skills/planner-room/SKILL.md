---
name: planner-room
description: Build or update a game room in the prototype from the user's Room Planner layout (text markers for decorations, furniture, NPCs, enemies, interactables, doors, cameras, areas and paths). Use when the user says to build, rebuild, resize or change a room from the planner, pastes a "Room plan for Claude" brief, or asks for a new room in the witch RPG.
---

# Build a room from the Room Planner

The planner is https://claude.ai/artifact/RNMHtaN12iw2kwvPsGanTb. Each room is a document in its `rooms` collection.

## 1. Read the plan

Prefer the stored room over a pasted brief, since it's always the latest:
- Use `ArtifactData` `list` on collection `rooms` with that URL.
- Add `out_dir` to save the rooms as files.
- Find the room by name. Its doc id may be like `new-room-4`; the game id can be friendlier (e.g. `field`).

If the user pasted a brief, use it. A brief covers one room by default. Compare it with `prototype/rooms.py` and change only what differs. Tilts are rounded to low/medium/high in the planner, so keep existing exact camera angles unless the user moved them.

## 2. Map markers to rooms.py

Everything is in base units, the same as the planner: x east, z south, facing 0 = south.

| marker | rooms.py |
|---|---|
| Decoration / Furniture | `props` entry: `asset`, `pos`, `block=(half_x, half_z)` if it should block walking |
| Interactable | `props` entry with `interact=dict(id, label, at=(x, z))`, plus a case in `interact()` in `prototype/game.js`. Use the marker's details for the text, exactly as written when the user gives wording. |
| NPC / Enemy | `npcs` entry: `asset`, `pos`, `face`, `interact`. Use `wander=dict(radius, pause)` if they wander. Needs a character; use the `spritestack-character` skill if it doesn't exist. |
| Door / exit | `exits` entry: a `rect` on that edge, `to`, `spawn` and `face` in the target room. Add the matching exit in the target room (e.g. a gap in its fence) and point its spawn back here. |
| Player start | `start` and `start_face` (only the first room uses them) |
| Camera (+ its zone area) | `cameras` entry: `yaw = 180 − facing`, tilt low 26 / medium 32 / high 38, `zone` from the matching area, `target` near the zone's middle, zoom about 3.6–4.4 (smaller for bigger zones) |
| Area (rug, clearing) | `floor.decals` (`rug`, `clearing`) or a prop |
| Path | `floor.decals` `path` with `points` and `width` |
| Room edges | indoors: `walls` (doors and windows inside one 16-unit segment); fence: `fences`; trees: trees on the far side, low bushes on the cameras' sides |
| Floor | `floor.style`: `wood`, `grass`, `meadow` or `forest`. Add a style in `groundColor()` in `game.js` if needed. |

**New props:**
- Add a builder to `prototype/props.py` and register it in `PROPS`. Design it small: it's enlarged 2.5×.
- Check it with a quick render before placing it.
- Keep flat parts level, as the pond's water does.

**Big rooms:**
- Split the cameras into zones of roughly 90–140 × 96–120 base units, so the player can't walk out of view.
- Add scenery so the room doesn't feel empty, and label your additions "Added by Claude" in the planner.

**Neighbours:** outdoor rooms show their outdoor neighbours past their edges. `build_game.py` lines up linked exits gate to gate and prints the offsets. Don't put tall props against an edge a neighbour's fence already borders. A neighbour's fence only covers its own length.

## 3. Build and check

```bash
python prototype/build_game.py
```

Then drive `prototype/witch_rpg.html` with Playwright (see `CLAUDE.md`):
- enter through each door
- walk into every camera zone and screenshot it
- click each interactable and check its text
- check NPCs wander or face the player
- look past the edges for neighbours
- no page errors, about 60 fps

## 4. Keep the planner in sync

If you changed the layout beyond the plan (resized, scaled, added scenery or cameras), write the room back so the user's next edits start from the game:
1. `get` the doc for its `version`.
2. `set` it with `if_version`, keeping the user's marker ids.
3. Label your additions "Added by Claude".

## Deliver

Commit on a branch and push. Send `prototype/witch_rpg.html` with a short summary of:
- what matches the plan
- what you interpreted or added
- anything you couldn't do
