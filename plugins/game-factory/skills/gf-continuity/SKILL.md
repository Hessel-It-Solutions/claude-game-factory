---
name: gf-continuity
description: "Continuity and consistency reviewer of the game Bible and assets. Cross-checks concept, GDD, script, characters, scenery, storyboard, content plan, ASSETS.md and the Godot project looking for orphan IDs, contradictions, missing or off-style assets. Read-only; writes production/continuity-report.md. Use at the end of W4 (before G3), at the end of each chapter, after renaming anything, or when the user asks \"is everything consistent?\" or \"check continuity\"."
---

# gf-continuity: continuity

A read-only reviewer that cross-checks the whole bible and the game: concept, GDD, script, characters, locations, storyboard, content plan, the asset registry and the Godot project. It reports orphan IDs, contradictions and missing or off-style assets, with file, line and owning skill. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Before gate G3 at the end of the storyboard wave
- At the end of each chapter
- After renaming anything

Produces: `production/continuity-report.md`.

Works with: gf-producer and every skill that owns a document.

---

Read-only. It fixes nothing: it points, with file and line, and says which skill owns the fix.

## Checks

**IDs and references**
- Every `chr_`, `loc_`, `seq_`, `chNN`, `lvl_` cited in any doc exists in its sheet.
- Every character and location in the Bible appears in at least one scene or level (or is marked as cut).
- Every script scene with a cutscene has a storyboard; every storyboard points to an existing scene.

**Narrative coherence**
- Name, age, appearance and relationships are the same in sheet, script and storyboard.
- Order of events is coherent between outline, chapters and content plan.
- Emotions used in the lines exist in the character's expression list.

**Design**
- Every GDD mechanic has a touch input and appears in some level of the content plan.
- Every animation state in the content plan is in the character sheet.
- GDD scale (screen, character, tile) equals the art direction's.

**Assets** (from W5)
- Every `approved` asset in ASSETS.md exists at its path and has `art/_prompts/<asset_id>.md`.
- Every asset referenced in a Godot `.tscn` or `.tres` scene is `approved`.
- Game images: colors outside `docs/palette.hex` (quick Pillow script in the sprite-gen venv; zero tolerance for sprites and tiles).
- Audio: every event in `audio_map.json` points to an existing file.

## Report: `production/continuity-report.md`

```markdown
# Continuity: <date>, <scope>
Result: OK | N problems (X blocking)
| # | Severity | Where | Problem | Fix owner |
|---|---|---|---|---|
```

Severity: **blocking** (prevents a gate: story contradiction, broken ID, game asset outside the palette), **medium**, **cosmetic**. The producer turns blocking items into an adjustment mini-wave before opening the gate.

## Script first

Run `tools/gf/gf.sh check --scope <scope>` before reading any doc. It covers paths, ids, lines longer than 80 characters, expressions against portraits and expressions.md, palette and storyboard. The LLM review only handles what is semantic (factual contradiction, order of events, tone), reading only the files changed since the last review (`git diff --stat <commit of the last review>`). Use the `opus` model only if the diff is large; otherwise `sonnet`.
