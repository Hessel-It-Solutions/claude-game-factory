---
name: gf-environments
description: Pixel art scenery production with Runway: tilesets (with autotile for the Godot TileMap), repeatable parallax layers, props, interactive objects and time-of-day/weather variations, pixelized to the master palette and delivered to Godot. Use from W5 on when a location in the content plan needs tiles, backgrounds or props, or when the user asks to "make the tileset", "make the background", "create the scenery objects", "paint the room".
---

# gf-environments: tiles, parallax and props

> **Detail coherence guardrail:** all content follows the same art standard; no character less detailed than the scenery, no scenery more detailed than the characters. Detail is volume (light and shadow in masses, continuous outline on actors, desaturated color from the storyboard), not loose pixels. Character and animal bases are cut out of the storyboard art; the AI only completes directions and animations, anchored on the cutout. Before delivering: a coherence board with the asset at game scale over the real scenery, next to the approved main character and the storyboard cutout. Full rule in `docs/02-art-direction.md` section 0.1.

Inputs: `docs/04-world/<loc_id>.md` (tile list, layers, props), key art in `art/environments/<loc_id>/keyart/`, `docs/02-art-direction.md`. Read `gf-runway`. `SG=$SPRITE_GEN_ROOT/.venv/bin/sprite-gen`, `PY=$SPRITE_GEN_ROOT/.venv/bin/python`, `PIX=tools/gf/pixelize.py`.

The approved key art is the `@place` reference of every generation for the location, together with `@style`.

## Tileset

AI pixel art does not close seams by itself. Flow:

1. **Tile sheet**: `generate_image` with `@place` and `@style`, asking for a grid of terrain tiles (for example 4x4) as seen in the game: "each tile exactly square, seamless edges, top surface with grass lip, inner fill, left and right edge caps, corner pieces, one-way platform, no perspective, flat lighting from top-left, no background", with a chroma background.
2. `$PY $PIX sheet.png sheet_px.png --width <columns × tile> --palette docs/palette.hex --chroma magenta --preview 4`.
3. Cut into tiles with Pillow in the venv and **fix seams**: every fill tile must repeat without a seam (3x3 test of the tile against itself). If it does not close, use `$SG background-tile --source tile.png --period <tile> --overlap <n> --out tile_seamless.png` or fix pixels by script.
4. Build the final atlas `game/assets/environments/<loc_id>/tiles.png` in an exact grid of `<tile>` px, no spacing, in the autotile layout order.
5. Godot terrain set (3x3 autotile minimum, "match corners and sides" with 47 tiles when the location needs rich edges; 16 tiles "match sides" for the basics). Deliver `game/assets/environments/<loc_id>/tiles_layout.md` saying which tile is which peering bit; gf-levels builds the `TileSet` from it.

Also generate decoration tiles (rocks, tall grass) and animated tiles (water, torch) as separate frames.

## Painted rooms (top-down or large open scenes)

When the location is a painted room or map instead of a tile grid:

- Build a **real blockout first**: the true floor plan assembled from the paintings at their in-game positions, with solid blocks drawn on top. Codex does not compose a level layout from scratch (open rooms and inverted maps came out in repeated rounds), so the plan comes from a script or from you, not from a text prompt.
- Paint in sections with the storyboard as the style reference and the first section as the tone reference. To join sections, repaint a strip centered on the seam (about 832x468 at 2x on input) and paste back only the middle (about ±56 px) with a 28 px feathered ramp.
- Smooth-colored areas of the blockout come back unpainted from the image model, and plateaus only get painted if the blockout has drawn blocks on them. Leftover blockout color on flat areas must be found and patched with neighbor texture.
- **The painting does not follow the guide, so collision comes from the painting**, not from the blockout. Color detection fails after the palette pass, and Codex does not trace by hand (it returns the layout claiming it traced). Trace in the main session, in 2x quadrants with a grid, and store the result as a mask with alpha (see gf-levels).
- Keep one explicit coordinate system for painted images versus world (for example image = world + offset). Every retouch prompt states it; a batch that retouches a painting or mask without knowing it opens gaps in the wrong wall.

## Parallax

Per layer in the world sheet (sky, mountains, hills...):

1. `generate_image` of the isolated layer, wide ratio, "horizontally seamless, wraps left to right"; front layers with a chroma background to become transparent; the sky without chroma.
2. `$PY $PIX layer.png layer_px.png --height <logical layer height> --palette docs/palette.hex [--chroma magenta]`.
3. Horizontal seam: `$SG background-tile --source layer_px.png --period <width> --overlap 32 --out layer_loop.png`.
4. Delivery: `game/assets/environments/<loc_id>/parallax/<NN>_<name>.png` with `parallax.json` (`{"layers":[{"file":"00_sky.png","motion_scale":0.0}, ...]}`) so gf-levels can build `Parallax2D`.

Reading rule: background layers have less contrast and are cooler than the playable plane.

## Props

Location prop sheet (grid, chroma background, same scale as the character with `@hero` as a ruler) then `$SG slice-sheet --grid CxR --names ...` then pixelize each. An isolated prop can also come from Codex with native alpha: `$SG gen --provider codex --prompt-file <prompt> --ref art/_refs/style-tile.png --ref <keyart> --transparent --out <prop>.png`, then `pixelize.py`. Animated props (flag, fire) follow route A of gf-sprites with `--subject effect`. Delivery: `game/assets/environments/<loc_id>/props/<prop_id>.png`.

## Variations

Night, rain, sunset: prefer recoloring by palette (`$SG recolor`, or swapping the palette by ramp mapping) over generating again. It keeps seams and geometry.

## Gotchas

- Textures must be loaded with `preload` (or referenced from a scene); a texture that is only `load()`ed by path at runtime can become a white square in the Android export.
- Image models drift on scale; always state the logical size and give a character as a ruler.
- Use `--width`/`--height` in `pixelize.py` instead of `--pitch auto` when the target size is known.
- After changing art, run `godot --headless --path <project> --import` before capturing; a `-s` script does not reimport changed PNGs and the capture shows the old texture.

## QA

- 3x3 tile without a seam; parallax running 3 laps without a jump.
- Colors 100% in the master palette.
- Mockup in Godot (ask gf-levels or build a test scene) compared with the key art and the gf-world mockup.
- Entry in `art/_prompts/` and in the wave report; status `candidate` until approved.
