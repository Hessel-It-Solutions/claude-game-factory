---
name: gf-art-direction
description: Pixel art direction for the game: style exploration (style tiles in Runway), logical resolution, character and tile size, master palette, outline/light/shadow rules, Runway model choice by A/B test, and the official prompt blocks. Owns docs/02-art-direction.md, docs/palette.hex and art/_refs/. Use in W1 (exploration) and W2 (style guide) of /game-factory, or when the user wants to change the look, the palette or the pixel art scale, "pick the art style", "make the palette".
---

# gf-art-direction: style and visual rules

Always read the `gf-runway` skill before generating.

## W1: exploration (cheap)

Three distinct style tiles from the concept interview. Each style tile is a single image with: the protagonist in a neutral pose, a piece of scenery, a UI element (button or health bar) and the visible palette. One prompt per direction, `count: 1`, the same model for all three (nano-banana-pro), ratio of the game's orientation.

Suggested directions (adapt to the concept): (A) 16-bit SNES, 32px, short palette; (B) HD pixel 64px, dramatic light, medium palette; (C) painted pixel art, large portraits, scenery with a lot of depth.

Save to `art/_refs/explore/<A|B|C>.png` and show them to the user in 1c.

## W2: style guide

### 1. Scale (technical decision, everything derives from it)

| Item | How to decide |
|---|---|
| Logical screen | landscape 640x360 or 480x270; portrait 360x640 or 270x480. Integer scale on the phone (nearest). |
| Character | height in logical px (example: 48 to 64 for HD pixel, 24 to 32 for 16-bit). Takes 12% to 20% of the screen height in action. No fractional scale on characters: it blurs the pixels. |
| Tile | 16 or 32 px, coherent with the character (character ~2 to 3 tiles tall). |
| Dialogue portraits | height in logical px (example: 96 or 128). |
| sprite-gen atlas cell | character + margin for weapons/effects (example: 96x96 for a 64 character). `logical_height` must be an integer divisor of the cell. |

Agree with gf-game-design (camera and scale section of the GDD). A divergence becomes a question for the user.

### 2. Master palette

`docs/palette.hex`: one `RRGGBB` per line, 32 to 64 colors, grouped in ramps (skin, hair, fabrics, metal, vegetation, sky, stone, UI). Extract it from the chosen style tile with `pixelize.py --colors N` and adjust by hand. Ramps with 4 to 6 tones, hue shift in the shadows (shadow leans blue/purple, light leans yellow), no pure black or pure white outside the UI.

### 3. Drawing rules

Outline (color, selective or not), light direction, shadows (layers, dithering yes/no), head/body proportion, level of detail on the face, how to represent metal, fabric, skin, fire. One line per rule, with a right/wrong example generated when it helps.

Section 0 of the document is the visual bar taken from the storyboard (when it exists): character height in the frame, desaturated color, volume through light and shadow masses, continuous outline on actors, cast shadow. Section 0.1 is the detail coherence rule: no character less detailed than the scenery, and no scenery more detailed than the characters. Fonts: pixel fonts only for titles and buttons at 20 px or larger (they deform at small sizes on device); body text in a legible font.

### 4. Official Runway model (A/B test)

The same character prompt and the same scenery prompt in `nano-banana-pro`, `gpt-image-2` and `seedream-5-pro` (and any other the user wants). Run each result through `pixelize.py` at the decided logical resolution. Compare grid, palette fidelity, consistency with `@style`. Record the winner per category (character, scenery, UI, portrait) and the reason.

### 5. Official prompt blocks

Fill the `[STYLE]`, `[FRAMING]`, `[BACKGROUND]` blocks of gf-runway with this game's values, per category: side sprite, top-down sprite (if any), portrait, tile, parallax, prop, UI, key art, storyboard. From here on, all skills copy these blocks without changing them.

### 6. Anchor

`art/_refs/style-tile.png`: the final style tile, regenerated with the official model and the palette locked. It is the `@style` reference of every generation.

## Sprite test (allowed in pre-production)

Generate a test of the protagonist in 2 states (idle and walk) through the gf-sprites pipeline, with the run in `art/_refs/sprite-test/`, to prove that the scale and style survive the pixel unfake. Mark it `draft`. If it does not survive, adjust scale/prompt before G2.

## Output

`docs/02-art-direction.md` with sections 1 to 6, linked example images, and a final section "What to reject" (signs that an asset left the style). Gate G2.
