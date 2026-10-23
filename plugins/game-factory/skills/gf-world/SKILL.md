---
name: gf-world
description: "Worldbuilding and scenery for the game: world map, a sheet for each location (dramatic function, atmosphere, time of day, weather, palette, parallax layers, tileset, props, hazards) and pixel art key art for each scene made in Runway. Use in W3 of /game-factory (one agent per group of locations), or when the user asks to create or redesign a scene, biome, city or map, \"design the world\", \"make the key art for this location\"."
---

# gf-world: world and scenery

Designs the world and its places: the world map, a sheet for each location (dramatic function, mood, time of day, weather, palette, parallax layers, tiles, props, hazards) and pixel art key art for each one. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Designing the world map and locations
- Creating or redesigning a scene, biome or town
- Producing key art that later guides tiles and painted rooms

Produces: `docs/04-world/` and `art/environments/<loc_id>/keyart/`.

Works with: gf-art-direction, gf-environments, gf-levels.

---

> **Detail coherence guardrail:** all content follows the same art standard; no character less detailed than the scenery, and no scenery more detailed than the characters. Detail is volume (light and shadow in masses, continuous outline on actors, desaturated storyboard color), not loose pixels. Character and animal bases are cut out of the storyboard art; the AI only completes directions and animations, anchored on the cutout. Before delivering: a coherence board with the asset at game size over the real scenery, next to the approved reference character and the storyboard cutout. Full rule in `docs/02-art-direction.md` section 0.1.

Inputs: `docs/05-script/outline.md` (locations), `docs/01-gdd.md` (mechanics the terrain must support), `docs/02-art-direction.md`. Load `gf-runway` before generating.

## `docs/04-world/world-map.md`

Geography, how locations connect, the order in which the player visits them, and a map (image generated in Runway as an old map or pixel art, according to the art direction) in `art/environments/_map/`.

## Sheet: `docs/04-world/<loc_id>.md`

```markdown
# <Name> (<loc_id>)
Chapters: ch01 · Dramatic function: <what this place means in the story>
## Atmosphere (time, weather, light, ambient sound)
## Palette (master palette ramps, dominant color, accent color)
## Gameplay reading
   where the player steps, what hurts, what is interactive; contrast between playable ground and background
## Parallax layers (back to front)
   sky (factor 0.0) · mountains (0.2) · hills (0.5) · playable background · foreground (1.2, optional)
## Tileset (for gf-environments)
   tile size, types: ground, edge, slope, platform, wall, water, decoration; autotile yes/no
## Props
   prop_id | description | interactive? | animated?
## Variations (night, rain, destroyed)
## Images: key art, mockups
```

## Images (Runway)

1. **Key art** (`art/environments/<loc_id>/keyart/keyart.png`): the scene as the player will see it, in the screen ratio, with the character at the right scale (the protagonist base as `@hero`). It is the target for gf-environments. With `@style`, no chroma.
2. **Gameplay mockup** (`keyart/mockup.png`): the same scene with a sketched HUD and readable platforms. Validates the contrast between background and ground.
3. Optional: time/weather variations.

Run the key art through `pixelize.py --width <logical screen width> --palette docs/palette.hex --preview 3` and evaluate it at real size.

## Rules

- The background never competes with the character: higher saturation and contrast on the playable plane, lower in the back.
- Each location has an identity color so the player knows where they are.
- Real or historical place: research architecture, vegetation and terrain; note the sources.

## Done criteria

Every location in the script has a sheet, key art and mockup; the tileset and prop list is enough for gf-environments to produce without asking.

## Tools

Post-processing and validation of key art and parallax: `tools/gf/gf.sh post` and `tools/gf/gf.sh validate`. Registry through the wave's `.assets.jsonl`.
