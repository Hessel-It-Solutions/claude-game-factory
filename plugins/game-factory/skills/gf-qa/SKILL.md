---
name: gf-qa
description: QA for the Godot 4 mobile game: GUT automated tests, headless smoke tests of every scene, level-run bot, playtest checklist per gate, screenshots in several aspect ratios, asset checks (palette, size, import), regression and a prioritized bug report. Use in W7 and at the end of each chapter, before any production gate, or when the user reports a bug or says "test the game", "run QA", "check the build".
---

# gf-qa: quality

Owner of `game/tests/` and `production/qa/`. A bug found becomes an item in the report with
an owner; gf-qa does not fix gameplay code, only tests and test tooling. Reply to the user
in the user's language. For the AC matrix and the "how" of proving each criterion, use
gf-autotest.

## Test layers

1. **Unit (GUT)**: damage rules, cooldown, save/load, sprite importer, dialogue parsing.
   `godot --headless --path game -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit`.
2. **Scene smoke**: a script that instantiates every `.tscn` in `scenes/` for N frames in
   headless mode and fails on any error or warning in the log.
3. **Level run**: a simple bot per level (timed action sequence, real input only) that
   must reach the `LevelExit`; measures time and deaths. Skeleton in `tools/godot/bot_template.gd`.
4. **Screenshots**: captures of menus, HUD and levels in 16:9, 19.5:9 and 4:3
   (`--resolution`), saved in `production/qa/screens/<date>/`. Captures need a window and
   must be checked in that real window, not assumed (`tools/godot/capture_scene.gd`).
5. **Assets**: colors outside `docs/palette.hex` in `game/assets/sprites`, `environments`,
   `ui`; textures with a filter other than nearest; audio without loop where it should
   loop; unreferenced files; the exported APK registering only `.translation` files and
   never raw `.csv` (translation keys once showed raw on the phone).
6. **Device**: checklist with the user (the agent has no phone): installation, touch,
   perceived fps, heat, audio with headphones, interruption by call/notification, locked
   rotation.
7. **Blind playtest**: gf-playtester, after gf-autotest, before a chapter gate.

## Hygiene rules

- **Count PASS lines, not only the absence of FAIL.** A run that exits early prints no
  FAIL. Compare the PASS count with the number of checks expected.
- Two Godot runs sharing a project directory or a `HOME` corrupt `.godot` and the save in
  `user://`. Parallel runs only on a copy of the project with a separate `HOME`; the
  final regression runs alone.
- Bots are deterministic: time in physics frames, per-level RNG, `BOT_SEED`. If three
  runs differ, that is a bug.
- Reject tests that only read source code. Validate a batch by running the full suite on
  the main tree, reading the whole diff, and checking that no old test or bot was changed
  to make a new batch pass.
- Green tests do not guarantee a playable level: an `Area2D` without a shape and
  z-order problems passed the suite. Run the bot and a window render before approving.
- Never trust a delegated report ("33/33 PASS", "capture done") without running it. Run the
  bot and view the captures in the main session.
- Do not run QA on a device while the machine is overloaded, and never on the user's own
  emulator or save.

## Playtest checklist (per gate)

- Does the player understand the objective in 10 s without text?
- Do the controls respond; no lost touches at the edges and corners.
- Does the first death come from a player mistake, not from illegibility?
- Are cutscenes skippable; is dialogue readable on a 6" phone.
- Are the fun metrics of GDD section 10 measured?

## Report: `production/qa/report-<date>.md`

```markdown
# QA <scope> <date>
Result: approved for gate | blocked
| # | Severity | Where | Steps | Expected | Got | Owner |
```

Severity: **blocking** (crash, impossible progress, save loss), **high** (wrong mechanic,
performance below target), **medium**, **low**. A production gate opens only with no
blocking and no open high items.
