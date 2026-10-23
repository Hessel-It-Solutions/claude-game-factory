---
name: gf-cutscenes
description: "Implementation of cutscenes and dialogue in Godot 4 in the classic 2D RPG style, with no video: animated character portrait with a text box at the bottom, cutscenes with the game's own sprites on the scenery driven by AnimationPlayer (camera, tweens, effects), static full-screen illustrations at climaxes, subtitles, skip, and wiring to level triggers. Use from W6 on, or when the user asks to build a scene, adjust in-game dialogue or create the opening/ending (\"make the cutscene\", \"wire the dialogue\")."
---

# gf-cutscenes: scenes and dialogue

Inputs: `docs/06-storyboard/<seq_id>.md` (Implementation column), `game/data/dialogue/<seq_id>.json` (gf-narrative), portraits in `game/assets/portraits/`, `dialogue_box.tscn` (gf-ui). Owner of `game/scenes/cutscenes/`, `game/scripts/dialogue/`.

## House rule: no video

Story scenes are made as in classic 2D RPGs: **character portrait + text box at the bottom**, with the game sprites acting on the scenery. The portrait can loop-animate (blink, move the mouth), like a GIF. There is no video in cutscenes, opening or ending. A climax gets at most one still full-screen illustration.

## Dialogue system

`scripts/dialogue/dialogue_runner.gd`: loads the sequence JSON, emits line by line to the `dialogue_box` (animated portrait `chr_id/emotion`: animation `<emotion>_talk` while the text is revealed, `<emotion>_idle` with a blink when it ends; name, text through `tr(text_key)`), advances on tap, speeds up the text on tap during the reveal, supports inline commands from the JSON (`{"cmd":"anim","target":"chr_hero","anim":"attack"}`, `wait`, `camera`, `sfx`, `music`). Dialogue pauses gameplay through `Game`, not a loose `get_tree().paused`.

## Cutscene

One scene per sequence: `scenes/cutscenes/<seq_id>.tscn` with an `AnimationPlayer` that reproduces the storyboard panel by panel (camera, positions, actor animations, tweens, flash, shake) and calls the `dialogue_runner` at speaking points. Durations from the storyboard table are the starting point.

- Always with a "skip" button (hold for 1 s) and record in `Game` that the scene was seen.
- A level trigger emits `Events.cutscene_requested(seq_id)`; `Scenes` plays the cutscene and hands control back.
- Characters on stage are shown at game scale with integer scaling; do not shrink sprites by a fractional factor to fit the frame.
- Use tweens of the node itself or bound methods for timing, not `SceneTreeTimer` or lambdas on root nodes, which outlive the scene.

## Full-screen illustrations

Panels marked as final illustration in the storyboard: redo at production quality with `generate_image` (key art model), `@style`, the character bases and the location key art, at the logical screen resolution; `pixelize.py --width <logical width> --palette docs/palette.hex`. Delivery in `game/assets/illustrations/<seq_id>_<NN>.png`. The illustration is static. Extra life, if the scene asks, comes from engine resources: a slight camera pan, fade, particles (dust, embers), shake, or the dialogue box over it.

## Verification

- Each cutscene in scope runs from start to finish headless without errors; skip works.
- All lines use an existing `text_key`; no emotion without a portrait.
- Real duration compared with the storyboard's in the report.
- Open the scenes in a window (captures), in each language: the localized text must differ from the source language, and the portrait you review must be the one the game loads.
