---
name: gf-narrative
description: "Game narrative and script: premise, lore, act and chapter structure (beat sheet), cast with arcs, scene script with dialogue, and export of the dialogue to game data. Use in W2 (structure) and W3 (full script) of /game-factory, when the user asks to write or revise story, a scene, dialogue or lore, \"write the script\", or when gf-cutscenes needs the source text."
---

# gf-narrative: structure and script

Writes the story side of the game: premise, lore, act and chapter structure, cast arcs, and the full scene script with dialogue. It also exports the dialogue to data files that the game loads. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Structuring the story into acts and chapters
- Writing or revising a scene, dialogue or lore
- Preparing source text for cutscenes

Produces: `docs/05-script/` and `game/data/dialogue/`.

Works with: gf-characters, gf-storyboard, gf-cutscenes.

---

Inputs: `docs/00-concept.md`; in W3 also `docs/03-characters/` and `docs/04-world/` in progress. Outputs in `docs/05-script/`.

## W2: structure (`outline.md`)

```markdown
# Narrative structure
## Premise (2 to 3 sentences)
## Theme and tone
## Essential lore (what the player must know, what stays implicit)
## Cast (list for gf-characters)
   chr_id | name | role (protagonist, mentor, antagonist...) | arc in 1 sentence | chapters
## Locations (list for gf-world)
   loc_id | name | dramatic function | chapters
## Act structure
## Beat sheet per chapter
   chNN | player goal | conflict | turn | how it ends | sequences (seq_ids) with cutscene
```

For a mobile game: short chapters, a hook at the end of each, story told more through play and image than through text. Text target per cutscene: up to 12 short lines.

Historical, religious or literary source: list the sources used, separate what is faithful from what is adaptation, and treat sensitive themes with care. A relevant divergence becomes a question for the user, not a silent decision.

## W3: script (`chNN.md`)

Scene format:

```markdown
## seq_03_lion: The lion in the flock
Location: loc_fields · Time: dusk · Type: cutscene | in-game | gameplay with lines
Characters: chr_hero, chr_lion
Scene goal: <what changes>

ACTION: <short visual description, what the storyboard will draw>
HERO (determined): Stay behind me, little one.
ACTION: ...
[GAMEPLAY: dodge tutorial, see lvl_ch01_02]
```

- Each line at most ~80 characters (phone balloon). Longer lines become two.
- Emotion in parentheses: it becomes the portrait expression (the expression list goes to gf-characters).
- Every scene has a `seq_id`, a location and characters that exist in the Bible.

## Dialogue data (production, after G3)

Export each scene to `game/data/dialogue/<seq_id>.json`, which gf-cutscenes consumes:

```json
{ "id": "seq_03_lion", "lines": [
  { "speaker": "chr_hero", "emotion": "determined", "text_key": "seq_03_lion.001", "text": "Stay behind me, little one." }
]}
```

`text_key` prepares localization. The source language of the lines is the one set in the concept (Languages section). Translations come later as Godot CSV (`game/data/i18n/*.csv`), one column per language.

## Done criteria

Every chapter has a beat sheet; every scene referenced in the storyboard exists in the script; every character and location mentioned exists in the Bible (gf-continuity checks).
