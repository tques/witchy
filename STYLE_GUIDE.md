# Sprite-Stack Style Guide

Every character is a small voxel model built by hand from simple 3D shapes, using the 2D sprite as the reference for proportions, colours and face. It is not an extrusion of the sprite. The reference character is the witch (`characters/witch.py`). When in doubt, match her.

The numbers live in `spritestack/style.py`; the reusable pieces live in `spritestack/model.py`. The rules below explain what each one is for and what went wrong without it.

## 1. Scale and camera

- **One sprite pixel = one cube.** A sprite about 88 px tall fills the default 72 × 90 × 48 box. Depth (z) is invented: aim for a body about 0.7× as deep as it is wide.
- **Same camera for everything:** 22° look-down, 4 px per cube in previews. Don't tune these per character, or characters stop matching.
- Characters are chibi: big head (radius ≈ 8.5 for an 88 px sprite), short body, rounded boots.

## 2. Build from shapes, not from the sprite outline

- Use ellipsoids, capsules, flat cylinders, lathes (stacked ellipses) and tapered strands.
- The sprite is a 3/4 or front view. Build the character **facing straight forward** and symmetric, apart from props and deliberate asymmetry such as a hair flick.
- `put()` never overwrites, so **the first shape placed wins**. Place props, the head and hair before the body. To change colours later, recolour `m.col[...]` instead of placing the shape again.

## 3. Lighting

- **One light, from the upper front left** (`LIGHT`). The light is baked into the cubes and turns with the model; that is intended.
- **Bold bands:** brightness is rounded to steps of 0.15 (`BAND`). Don't add smooth gradients to the body.
- **Large flat parts** such as brims, capes, shields and wings use `m.brim()`-style smooth shading instead. It uses an analytic surface normal, finer 0.05 steps (`SMOOTH_BAND`) and a soft contact shadow where the part meets the body.
  - Why: per-cube normals on a stepped flat surface produce dark seams at every step.
- **Glowing parts** (orbs, gems, magic): `m.glow(part)`. They stay bright and get one white highlight.

## 4. Faces

- **Flat face plate:** cut the head flat 5 cubes in front of its centre (`FACE_PLATE`).
  - Why: on a round head the two eyes sit at different depths and break apart when the head turns.
- **Copy the eyes from the sprite pixel for pixel.** Copy one eye and mirror it.
  - Get the colours with `prep_sprite.py --dump`.
  - The eye's inner column sits 2 cubes from the centre line (`EYE_GAP`).
- Eyes are **painted 3 cubes deep** (`EYE_DEPTH`) and **unlit** (exact colours).
  - Why: one-cube-deep paint turns into skin-coloured slivers at 20° or more.
- **No mouth, nose or blush unless the sprite has them.**
- Face skin is one flat tone (`SKIN_FACE`), slightly darker than body skin.

## 5. Hair

- **Solid base shape first:** a shell around the head, a mass down the back, and side locks.
- Then add **only a few strands** curving off it with `m.strand()`:
  - chunky bangs that end just above the eyes, with an optional thin one between the eyes
  - 1–2 locks curling out at the sides
  - optional flicks at the ends of the back hair
- **Avoid many separate strands.** That reads as stringy and noisy, not chunky.
- Alternate 3 close shades for strands so they separate, and use one darker shade for the base.
- Trim hair that pokes through hats with `m.carve(...)`.

## 6. Clothing and trim

- **Trim stays flat.** Gold stripes and piping are recoloured surface cubes, not raised beads. Raised vertical piping looked wrong.
- **Make panels between trim read as inset** with `m.recess_panel()`: push the panel 1 cube in and add a slightly darker edge line where it meets the trim.
- **Hems can have a raised band:** one extra cube of radius over 2–3 rows.
- **Cuffs** use `m.cuffed_arm()`:
  - a flat-ended cuff, wider than the sleeve, with a dark opening
  - a thin wrist and a hand that comes out of the opening
  - Use flat cylinders for cuffs and bands, never capsules. Capsule ends swallow the hand.
- **Belts** run flush across openings.

## 7. Thin flat parts: level or steep, never slightly tilted

- A thin part tilted by less than one layer per cube is cut into **plank-like stripes** by the horizontal layers.
- Keep brims, capes and plates level, and add droop as a whole-layer step at the rim, or tilt them steeply.

## 8. Wings, fins, capes and other thin sheets

Use `m.membrane()` (see `characters/fairy.py`).

- **Keep sheets vertical**, hinged at the back of the body and swept about 30° back from straight out. Vertical sheets slice cleanly into layers; near-horizontal ones get plank stripes (section 7).
- **Two cubes thick**, with smooth shading (`m.smooth_surface(..., two_sided=True)`). Translucent sheets catch light from either side, so they never go dark from behind.
- **Size them from the sprite and lean generous.** Wings drawn in 3/4 view look smaller once squared up in 3D.
- **Colour pattern:**
  - a base colour
  - a bluer tint near the body
  - a few light diagonal bands
  - a two-step rim, light then dark (`rr > 0.80`, `rr > 0.92`)
- **Shape the back view too:** a character seen from behind is mostly hair and wings, so give the back hair 2–3 curling tufts.

## 9. Animation

- **Every frame is the same character rebuilt with a pose.** Never edit frames by hand, so the style can't drift between frames.
- **Use `spritestack/gait.py` for locomotion.** It keeps every character's walk and run consistent. Override a preset value per character rather than writing new motion code.
- **Walk** (8 frames at 10 fps):
  - stride about 5.5 cubes, big enough to read clearly
  - the forward foot lifts about 2.6 layers
  - the body rises 1 layer as the feet pass
  - arms swing opposite their legs, and a hand holding a prop swings about half as much
  - each hem half follows its leg
- **Run** (8 frames at 18 fps, about 2.5–3 times walking speed):
  - stride about 9, with a high knee lift and the back heel kicking up
  - the body rises 2 layers in flight, when the legs are split, and is lowest at mid-stance
  - forward lean of 0.09, made by shifting whole layers, so brims stay level and no planks appear
  - arms pump harder, and the forward hand rises
  - hair, hems, capes and hat tips stream backward (`g.trail`)
- **Casting** (`spritestack/cast.py`, any mage):
  - The hold raises the prop up and out to the side, never across the face.
  - The focus (orb or gem) pulses with `glow(boost)`, and 6 small unlit plus-shaped sparkles orbit it.
  - The flick has a clear wind-up, a fast snap past the aim, then a release with a bolt and a trail plus an expanding sparkle ring that thins out.
  - It ends back in the hold pose, so the two chain.
  - Magic wind (`c.breeze`) lifts hair the same way running does.
  - Sparkles are the only unlit colours besides eyes; keep them near-white tinted with the spell's colour.
- **Ground speed comes from the stride** (`2 × stride ÷ (frames ÷ 2)`), so feet don't slide. Don't hand-tune it.
- **Centre the body** (`CENTER_X`, plus `CENTER_Z` with a deeper `GRID` when props reach far forward). Everything spins around the middle of each layer, and nothing may be cut off at the box edge.
- **The standing pose must not change** when animation is added: with no pose, every gait offset is exactly 0.

## 10. Colours

- Take colours from the sprite's palette (`sprites/NAME_palette.txt`).
- Give every material a base colour. Shading supplies the light and dark versions, so don't paint shadows into base colours, except:
  - the inside of sleeves and openings (very dark)
  - edge lines next to recessed panels

## 11. Review checklist (before calling a character done)

Run `python -m spritestack.build characters/NAME.py --quick --views 0,35,90,180` and check each item:

- [ ] Front view matches the sprite's proportions and colours.
- [ ] Eyes hold their shape at 35°, and no face paint breaks into slivers.
- [ ] No dark seams or ring on large flat parts.
- [ ] No plank stripes on brims, capes or other thin parts.
- [ ] Hands clearly separate from cuffs; props are held.
- [ ] Nothing pokes through hats or helmets.
- [ ] The back view is believable (hair mass, clothing back), not a dark copy of the front.
- [ ] Animations: feet don't slide in `walk.html`, and the steps read clearly in `walk/frames.png`.
- [ ] Side-by-side with the witch (`out/witch/sheet.png`): same scale, lighting and band style.
