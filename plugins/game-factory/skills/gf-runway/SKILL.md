---
name: gf-runway
description: "Field manual for the Runway MCP in the game factory, used to generate consistent pixel art (images, pose sheets, animation videos, music, SFX and voice), download the results, keep visual identity through references and log cost. Use whenever any gf-* skill needs to generate or edit art, animation or audio with Runway, or when the user asks to \"generate the art\", \"make the sprite in Runway\", \"generate the scenery\", \"make a sound effect\"."
---

# gf-runway: generation with Runway

Runway generates concept art, identity bases, scenery, static illustrations and audio. Runway video is only an internal tool for extracting locomotion cycles for sprites; the game has no video (a cutscene is a portrait plus a text box). Sprite pose strips come from Codex through sprite-gen (see gf-sprites); Runway only generates strips as a fallback. Scripts and sprite-gen turn everything into real pixel art. AI images "in pixel art" never come out with a clean grid, so **every asset that goes into the game gets post-processing** (sprite-gen `extract` with `pixel_unfake`, or `scripts/pixelize.py`).

Reply to the user in the user's language. The Runway MCP tools are used by their short names below (`whoami`, `generate_image`...). When Runway is connected through claude.ai they are exposed as `mcp__claude_ai_Runaway__whoami`, `mcp__claude_ai_Runaway__generate_image`, and so on.

## Tools

| Need | Tool | Notes |
|---|---|---|
| New image or edit | `generate_image` | `referenceImages` with tags for consistency; `count` up to 4 for variations |
| Animation from a still | `generate_video` | i2v with `startFrame`; expensive, use only where a pose strip cannot solve it |
| Upscale | `upscale_image` | marketing art only; never on game pixel art |
| Cutout | `remove_image_background` | fallback when chroma fails; also the SAM cutout tool (see Gotchas) |
| Music | `generate_music` | `lyria-3-clip` for loops and stings, `lyria-3-pro` for a full track |
| SFX | `generate_sound_effect` | `loop: true` for ambiences |
| Voice | `generate_speech` | grunts and short character lines |
| Status / URL | `get_task` | when there is no inline viewer |
| Balance and models | `whoami` | before and after every wave |

Costs: use the value reported in each tool description and response. Log it in `art/_prompts/<asset_id>.md` and in the wave report. Respect the budget passed in the dispatch, and ask for approval before spending above the agreed threshold.

## Image model

The game's official model is chosen by gf-art-direction in W2 (A/B test with the same prompt) and stored in `docs/02-art-direction.md`. Until then, starting points:

- `nano-banana-pro`: best fidelity to references, default for characters and poses.
- `gpt-image-2` / `gpt-image-2.5-flare`: text and layout (logo, UI, store screens).
- `seedream-5-pro`: wide scenery and key art.

Do not switch models in the middle of a set (for example, all poses of one character come from the same model).

## Consistency

1. **Anchors**: `art/_refs/style-tile.png` (style), `art/characters/<chr_id>/base/base.png` (identity), `docs/palette.hex` (colors).
2. Pass the anchors in `referenceImages` with short tags and cite them in the prompt: `@style`, `@hero`, `@guide`.
3. An image generated in this conversation can be a reference by `taskId` instead of a URL.
4. Fixed prompt per category: build the prompt from the blocks below, saved in `docs/02-art-direction.md`. Do not improvise the style block on every generation.

### Prompt blocks

```text
[STYLE]    detailed pixel art, <game logical resolution>, crisp hard pixel edges, no anti-aliasing,
           no blur, no gradient smoothing, limited palette of <N> colors matching @style,
           <outline: 1px dark selective outline>, <light: top-left key light>
[SUBJECT]  <character/object description from the bible>, matching @<chr_id> exactly
[FRAMING]  <side view orthographic | 3/4 top-down>, full body, centered, feet visible,
           character fills <X>% of frame height
[BACKGROUND] flat solid <#FF00FF magenta | #00FF00 green> background, no floor, no cast shadow,
           no text, no labels, no grid lines, no border
```

Chroma background: magenta by default; green when the subject has pink, purple or magenta. Scenery and key art do not use chroma.

## Download and log

1. Take the result URL (tool response, or `get_task` once `SUCCEEDED`).
2. `curl -L -o <owner path>/<asset_id>.png "<url>"`. Signed URLs expire: download right away.
3. Write `art/_prompts/<asset_id>.md`:

```markdown
# <asset_id>
- model: <id>  · ratio: <r>  · task_id: <id>  · credits: <n>
- refs: @style=<task_id|file>, @hero=<...>
- status: draft
## prompt
<full text>
```

4. Add the asset line to the wave report (format in gf-producer).

## Post-processing for pixel art

- **Characters and animation**: gf-sprites pipeline (sprite-gen with `--fit-pixel-unfake`).
- **Scenery, tiles, props, UI, portraits**: `tools/gf/pixelize.py` (copied into the game repo by gf-setup; `PIX=tools/gf/pixelize.py`):

```bash
$SPRITE_GEN_ROOT/.venv/bin/python $PIX \
  in.png out.png --pitch auto --palette docs/palette.hex [--chroma magenta] [--preview 4]
```

`--pitch auto` measures the size of the generated "pixel". When the logical resolution of the asset is known (32px tile, 640x360 background), prefer `--width`/`--height` (exact output size): the AI draws blocks of fractional size and the automatic measurement rounds. Other options: `--palette` locks colors to the master palette; `--chroma` turns the chroma color into transparency; `--exclude` forbids palette colors for that asset (for example, characters without UI colors, or without a color ramp reserved for one character; the reserved rows live in `docs/02-art-direction.md`); `--preview N` also writes an N× nearest-neighbor copy for review.

The `tools/gf/gf.sh post <raw> <final> --width <W>` command wraps this script, cleans fringes and validates the palette. Register the result in `production/waves/<wave>.assets.jsonl`.

- Cutting isolated objects: `$SG cutout in.png --white-check`.
- Sheet with several variants of one subject (expressions, props): `$SG slice-sheet --sheet in.png --chroma-key magenta --grid CxR --names ...`.

## Video for animation

Use when a pose strip cannot solve it (cape, hair, effects, attacks with a wide arc):

1. Canvas: `$SG video-canvas` from the base (chroma background, safe margin).
2. `generate_video` with `startFrame` = canvas, a prompt describing **only the motion**, locked camera, no zoom, no cut, constant chroma background. Model: start with `seedance-2` or `kling-3-turbo`; shortest supported duration.
3. Download the mp4 and follow `$SG video-frames` then `$SG video-loop` (details in gf-sprites).

Ask the user for approval before generating videos in batch.

## Gotchas

- `list_recent` dumps huge URLs into the context. Do not call it in the main thread. Download through a Sonnet subagent with `get_task` instead.
- SFX prompts containing "boy" (and similar words about children) hit moderation (CHILDREN). Describe the sound by source and action ("short wooden step", "small grunt") instead of the subject.
- `search_voices` may not be enabled on the account; check before planning voice casting and fall back to `generate_speech` defaults.
- Runway called from a subagent is sometimes blocked by the permission classifier. Do not work around it: ask the user for approval and generate in the main session.
- Background removal for cutouts: `remove_image_background` (SAM) works on the cutout enlarged 8x with soft interpolation; it may answer "No detections" on small objects, in which case cut from the higher-resolution original and retry. A failed call is refunded. Afterwards close holes, keep the largest component and reduce back by majority color vote.
- Hand-made masks from Codex come out with holes; use the SAM route.
- A secondary character generated without the cutout reference inherits the colors of the main character. Always pass the right `@<chr_id>` cutout.

## Do not

- Do not use `upscale_image`/`upscale_video` on game assets: it destroys the grid.
- Do not ask for "pixel art" without a logical resolution and palette: the model invents the scale on each image.
- Do not generate a character without `@style` and `@<chr_id>` once the base exists.
- Do not leave an asset without an entry in `_prompts`: without it you cannot regenerate the same result.
