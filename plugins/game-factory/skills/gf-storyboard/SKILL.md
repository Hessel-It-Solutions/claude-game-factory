---
name: gf-storyboard
description: "Game storyboard: breaks each script sequence into panels (framing, action, line, camera, duration, transition), generates the frames in pixel art in Runway with the approved characters and scenery, and assembles the board (no video: scenes become portrait + text box and sprites on the scenery). Includes the screen-flow storyboard and the first minute of gameplay. Use in W4 of /game-factory (one agent per chapter), or when the user asks for a storyboard, animatic, \"storyboard this scene\", or to visualize a scene."
---

# gf-storyboard: storyboard

Breaks every script sequence into panels (framing, action, line, camera, duration, transition) and draws the frames in pixel art with the approved characters and locations. The storyboard becomes the visual bar for production: assets that do not match it get redone. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Storyboarding a chapter before production (W4)
- Planning the screen flow and the first minute of play
- Visualizing a scene before it is built

Produces: `docs/06-storyboard/` and `art/storyboard/`.

Works with: gf-narrative, gf-characters, gf-world, gf-cutscenes.

---

> **Detail coherence guardrail:** all content follows the same art standard; no character less detailed than the scenery, and no scenery more detailed than the characters. Detail is volume (light and shadow in masses, continuous outline on actors, desaturated storyboard color), not loose pixels. Character and animal bases are cut out of the storyboard art; the AI only completes directions and animations, anchored on the cutout. Before delivering: a coherence board with the asset at game size over the real scenery, next to the approved reference character and the storyboard cutout. Full rule in `docs/02-art-direction.md` section 0.1.

Inputs: `docs/05-script/chNN.md` (the sequence), sheets and bases in `docs/03-characters/` and `art/characters/*/base/`, sheets and key art in `docs/04-world/`, `docs/02-art-direction.md` (the "storyboard" prompt block). Load `gf-runway`.

## Which sequences

- Every cutscene in the script.
- **The first minute of play** (opening the app until the player's first control): mandatory, it is where the player decides whether to stay.
- **Screen flow** (menu, pause, game over, victory, shop if any): simple board, one panel per screen, based on GDD section 9. Delivered to gf-ui.
- Gameplay moments that the script marks as `[GAMEPLAY: ...]` and that change the rules of the game (first appearance of a mechanic or boss).

## Document: `docs/06-storyboard/<seq_id>.md`

```markdown
# <seq_id>: <title>
Script: docs/05-script/ch01.md#seq_03_lion · Location: loc_x · Target duration: 25 s

| # | Frame | Framing | Action | Line / text | Camera | Duration | Transition | Implementation |
|---|---|---|---|---|---|---|---|---|
| 1 | ![](../../art/storyboard/seq_03_lion/01.png) | wide | flock grazing | (no line) | slow pan → | 3 s | fade in | parallax + idle sprites |
| 2 | ... | portrait close-up | Hero sees the lion | HERO (afraid): ... | fixed | 2 s | cut | portrait + dialogue box |
```

The **Implementation** column says how gf-cutscenes will do it in Godot with the assets that exist: sprites with animation X, portrait with expression Y, camera tween, shake, flash, full-screen static illustration. A panel that needs a new asset (full-screen illustration, special animation) lists the asset and its owner so it enters the content plan.

## Frames (Runway)

- One `generate_image` per panel, in the game screen ratio, with `@style`, the base of each character present (`@hero`, `@lion`) and the location key art (`@place`).
- Storyboard art is for deciding framing and emotion: it does not need a perfect grid, but it must respect scale and palette. Light post-processing: `pixelize.py --width <logical width> --palette docs/palette.hex`.
- A cutscene panel that becomes a **final illustration** in the game (full-screen epic moment) is marked `candidate` and redone at production quality by gf-cutscenes after G3.
- Names: `art/storyboard/<seq_id>/NN.png`.
- The storyboard is the visual bar for everything after it: keep character height in screen proportion (decide the target size in the art direction and keep it in every frame), no fractional scaling, and a cast shadow under characters.

## Board

- **Board**: contact sheet with the numbered frames, made with the Python of the sprite-gen venv (Pillow), at `art/storyboard/<seq_id>/board.png`.
- No animatic and no video. Each panel is implemented with what the engine does: sprites on the scenery, animated portrait + text box, or a static illustration (see gf-cutscenes). A panel that would only work as video must be redrawn.

## Done criteria

Every cutscene in the script has a board; each panel has the implementation column filled with existing assets or assets listed in the content plan; the first minute of play is drawn.

## Tools

Frames through Codex in batch: build a `jobs.json` and run `tools/gf/gf.sh codex jobs.json` (max 5 refs per job; it already does post-processing and the report). Board: `tools/gf/gf.sh board art/storyboard/<seq_id>`. Validation: `tools/gf/gf.sh validate`. Context: the producer pastes the output of `gf context storyboard --seq <seq_id>`. Do not write board or post-processing scripts.
