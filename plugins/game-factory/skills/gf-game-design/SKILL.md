---
name: gf-game-design
description: "Mobile game design: the GDD (docs/01-gdd.md) with mechanics, systems, touch controls, progression, economy, enemies and initial balance, plus the per-chapter content plan (docs/08-content-plan.md) that says which assets and levels each chapter needs. Use in W2 (GDD v1) and W3 (content plan) of /game-factory, or when the user asks to create, change or balance a mechanic, \"write the GDD\", \"balance the game\"."
---

# gf-game-design: GDD and content plan

Writes the game design document and the content plan. The GDD covers mechanics, systems, touch controls, progression, economy, enemies and the first balance numbers. The content plan lists, per chapter, every level and every asset that has to be made. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Writing GDD v1 after the concept is approved
- Creating, changing or balancing a mechanic
- Planning which levels and assets each chapter needs

Produces: `docs/01-gdd.md`, `docs/08-content-plan.md`.

Works with: gf-concept, gf-narrative, gf-gameplay, gf-levels.

---

Input: approved `docs/00-concept.md` (G1). Outputs: `docs/01-gdd.md` (W2) and `docs/08-content-plan.md` (W3).

## GDD v1 (W2)

```markdown
# GDD: <Title>
Version: 1 · Status: in review (G2)

## 1. Core loop (text diagram, with timings)
## 2. Touch controls
   - layout per orientation, minimum touch area 44x44 pt, safe zones (notch, gesture bar)
   - action → gesture mapping; accessibility alternative
## 3. Character mechanics
   table: mechanic | input | rule | initial parameters (speed in logical px/s, heights, cooldowns)
## 4. Systems
   health/damage, combat, inventory, abilities, dialogue, save, checkpoints (depending on the genre)
## 5. Enemies and obstacles
   table: id | behavior | attack | health | where it appears
## 6. Progression
   chapters, unlocks, difficulty curve, rewards
## 7. Economy (if any)
   currencies, sources and sinks, prices; link to the concept's monetization
## 8. Camera and scale
   main camera (3/4 top-down, side view) and, if hybrid, which moments change camera, whether they are playable or only cinematic, and the mechanics of the side mode
   proposed logical screen size, character size in logical px, tile size (confirm with gf-art-direction)
## 9. Screens and UI flow
   splash → menu → selection → game → pause → end; list for gf-ui and gf-storyboard (screen flow)
## 10. Fun metrics
   what to measure in the playtest (time to first death, completion rate per level)
## 11. Out of scope
```

Rules:

- Every number is **initial** and also lives in `game/data/balance/*.json` once production starts (owner: gf-gameplay). After G3 the GDD points there.
- Default unit: logical pixels of the base screen and seconds.
- Every mechanic must fit the chosen touch control. If it does not fit, cut or simplify it, and record it in DECISIONS.md.
- Think mobile: short sessions, automatic pause when focus is lost, frequent checkpoints, nothing that needs console-level precision.

## Content plan (W3)

It ties the script (gf-narrative), the world (gf-world) and the cast (gf-characters) to what must be produced. It is the shopping list of production.

```markdown
# Content plan
## Vertical slice (W5 to W7)
   chosen chapter/level, why it represents the game, exact assets
## Chapter chNN: <name>
   - levels: lvl_chNN_01 (location, objective, new mechanics, enemies, target duration)
   - characters and animation states: chr_x [idle, walk, attack, hurt, death]
   - scenery: loc_y (tileset, parallax layers, props)
   - cutscenes: seq_NN
   - music and SFX
   - new UI
```

The vertical slice is the smallest cut that proves the core loop, the art and the control on a phone: normally 1 complete level + 1 short cutscene + menu.

## Done criteria

Every mechanic has input, rule and parameter. Every chapter in the content plan lists animation states per character; gf-sprites can build the production queue from this document alone.
