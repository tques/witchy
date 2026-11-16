# Room Planner

A top-down planner for the prototype's rooms. You lay out a room with text markers ("Pumpkin", "Old wizard", "Door to the cellar") and Claude turns them into real sprite-stacked props, characters, doors and cameras in `prototype/rooms.py` and `prototype/props.py`.

- **Live version:** https://claude.ai/artifact/RNMHtaN12iw2kwvPsGanTb. Rooms save automatically to the page's shared storage, where Claude can read them directly. Ask, for example, "build the Pumpkin Kitchen from the planner".
- **Sharing one room:** **Brief for Claude** covers just the room you have open by default. Switch to **All rooms** for the whole world.
- **Offline copy:** `room_planner.html`. Open it in a browser. Rooms save in that browser. Use **Brief for Claude** to copy a brief, or **Save file** to write `rooms.plan.json`.

## Markers

| marker | use it for | key |
|---|---|---|
| Decoration | small set dressing: pumpkin, vase, hanging herbs | 1 |
| Furniture | table, bookshelf, bed | 2 |
| NPC | wizard, shopkeeper; put personality and lines in Details | 3 |
| Enemy | slime, bat swarm | 4 |
| Interactable | chest, lever, spellbook; say what clicking does | 5 |
| Door / exit | snaps to the nearest edge; link it to another room | 6 |
| Player start | where she appears | 7 |
| Camera | place it, then drag its handle to aim; pick a height | 8 |
| Area | drag a rectangle: rug, pond, garden bed, camera zone | 9 |
| Path | click points, double-click to finish | 0 |
| Note | anything else | N |

Every marker has a **label** (what it is) and **details** (anything Claude should know). Point markers also have a size (S, M, L) and an optional facing.

## Conventions (shared with rooms.py)

- **Units:** base units, the same as `prototype/rooms.py`. The witch is about 35 tall and 14 wide. The grid is 8 units, and wall segments are 16.
- **Axes:** x runs east, z runs south, and (0, 0) is the north-west corner.
- **Facing:** 0 = south (toward the camera side), 90 = west, 180 = north, 270 = east.
- **Cameras:** a marker's facing is where it looks. The brief converts it to `rooms.py` terms:
  - yaw = 180 − facing
  - tilt: low 26, medium 32, high 38
  - Claude picks the zoom and the target.
- **Size presets** (sized for the 1920×1080 game view): 80×60, 120×90, 140×105 (the cottage), 160×120, 220×150 (the garden), 280×120, 260×200, 280×190, 320×220 and 350×240 (the field), or a custom size in steps of 2.

## Files

| file | what |
|---|---|
| `room_planner.html` | the planner (the same page as the live version) |
| `rooms_to_plan.py` | converts `prototype/rooms.py` into planner rooms (`prototype_rooms.plan.json`) so existing rooms can be edited |
| `prototype_rooms.plan.json` | the cottage, garden and forest as planner rooms |
