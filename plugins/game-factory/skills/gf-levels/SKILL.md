---
name: gf-levels
description: "Level design and assembly in Godot 4: blockout, TileSet with terrains from the gf-environments tiles, TileMapLayer, parallax, collisions, enemy and item spawns, checkpoints, cutscene and music triggers, difficulty pacing and mechanic onboarding. Use from W6 on for each level in the content plan, or when the user asks to create, adjust or balance a level (\"build the level\", \"fix the collision\")."
---

# gf-levels: levels

Inputs: `docs/08-content-plan.md` (level: location, goal, mechanics, enemies, duration), `docs/04-world/<loc_id>.md`, `game/assets/environments/<loc_id>/` (tiles, `tiles_layout.md`, `parallax.json`, props), gf-gameplay actors. Owner of `game/scenes/levels/`, `game/data/levels/`.

## Process per level

1. **Plan** in `game/data/levels/<lvl_id>.md`: level beats (introduce, practice, combine, test), ASCII map with sections, where each new mechanic first appears **safely**, checkpoints every 30 to 60 s of play, target duration (short mobile session).
2. **Blockout**: TileMapLayer with gray collision tiles, real actors. Play it (headless with a simple bot script when possible, or manual) and adjust distances with the GDD parameters (the jump reaches, the enemy gives time to react). For painted rooms, the blockout is the real floor plan assembled from the paintings at their in-game positions with solid blocks on top (see gf-environments); never ask Codex to compose a level layout from scratch.
3. **Art**: the location's `TileSet` (`game/scenes/levels/tilesets/<loc_id>.tres`, terrain sets per `tiles_layout.md`), painting by terrain, layers: decorative background, playable (collision), decorative foreground. `Parallax2D` per layer from `parallax.json`. Props as instanced scenes.
4. **Gameplay**: spawns (markers with exported type and parameters), collectibles, `Checkpoint`, `LevelExit`, triggers (`Area2D`) that emit on `Events`: cutscene (`seq_id`), music change, dialogue.
5. **Camera limits** and death zones.

## Level type

The level plan declares `camera: topdown | side`. Top-down: TileMapLayer with y-sort (characters behind/in front of objects by the y coordinate), collision at the feet, connected rooms or screens as in Zelda. Side: ground with gravity, parallax in layers as in the style reference, usually short and scripted (a dramatic moment). The transition between the two modes is a swap scene with a `Scenes` fade, never a live camera change in the same scene.

## Collision gotchas

- **TileSet collision polygons are relative to the tile center**, not the top-left corner.
- **Painted levels: collision comes from the painting.** Store a mask PNG with real alpha. A grayscale (mode L) mask passed to `BitMap.create_from_image_alpha` has alpha 1 everywhere: `opaque_to_polygons` returns one polygon the size of the image and the level has no wall. The game mask needs alpha (write RGBA). Always check the polygon count.
- **`CollisionPolygon2D` with `BUILD_SEGMENTS` has only the outline**: the interior of a rock does not collide (a physics query says "free" inside). Mark the interior by the mask in the navigation grid, and use `BUILD_SOLIDS` or a body-sized check where the interior matters.
- A reach grid of 8 px does not see a gap of about 12 px; test gaps pixel by pixel or step 2 px. A mask converted by threshold leaves stray pixels that become snag points: filter components under about 64 px.
- Generated files such as `collision_polygons.json` are produced from the mask; never edit them by hand, and keep the tests that guard them. Fix the mask or the generator instead.
- When retouching a painted collision, measure by a point-in-polygon grid sweep against the previous version: only the retouch box plus a 3 px border may change. A batch once "opened the mask to the free area" and erased a whole wall with the suite green.
- To see the exact collision of a level, rasterize it: `godot --headless --path game -s tools/dump_collision.gd -- <scene.tscn> <out.png> <width> <height>` (StaticBody2D + TileMapLayer with physics to a PNG mask, plus `<out>.json` with each shape). It shows the initial state (doors closed).
- Painted image coordinates and world coordinates differ by an offset in some setups: always state the system in retouch prompts and tests.
- Textures and TileSet atlases must be loaded on the main thread and via `preload`/scene references (see gf-godot-core).
- Top-down bodies use `MOTION_MODE_FLOATING` (see gf-gameplay).

## Rules

- Readability: what is floor, wall and hazard must be obvious from the art alone (contrast agreed with gf-world).
- Mobile: no stretch demands pixel precision; hard jumps are optional (shortcut or collectible).
- New mechanic: first time without risk, second with low risk, third combined.
- Level fits in memory: TileMap in one scene, off-screen enemies paused (`VisibleOnScreenEnabler2D`).
- Blocking a path back must consider a save at an earlier checkpoint: move the checkpoint to the exit side together with the block.

## Verification

- Scene loads headless without errors; every spawn references existing scenes.
- Playable from start to finish (bot route or logged playtest), time measured against the target duration.
- Checkpoints restore state (GUT save/load test of `Game`).
- Report with a screenshot of each section (headless capture via `get_viewport().get_texture().get_image().save_png()` in a test script). Captures from a Codex run often photograph the initial scene without building the state: check them in a window in the main session.
