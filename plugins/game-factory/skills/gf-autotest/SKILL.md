---
name: gf-autotest
description: Automated testing specialist for the Godot 4 game. Turns everything that was implemented into an acceptance-criteria (AC) matrix, links each AC to an automated test (GUT, real scene, scenario bot with invariants, visual capture), runs everything and only delivers with the matrix green. Use after any fix or feature, before installing on a device, when the user asks "did you test it?", reports a bug that slipped through, or says "test everything", "test the ACs", "run the tests", "write a bot for this level".
---

# gf-autotest: ACs that are tested, not just "it compiles and passes"

This skill complements gf-qa (layers, report, gates). Here is the **how**: prove each
acceptance criterion through the path the player actually uses. Rule: **nothing ships
with an AC that has no test or a red test.** If an AC cannot be automated, it appears in
the matrix as `manual` with the reason, and the user is told.

Reply to the user in the user's language.

## Flow (every delivery)

1. **Collect the ACs** for what was implemented in the session: the user's request, the
   location sheet / GDD / script the change touches, `production/DECISIONS.md` and the
   diff. An AC is a verifiable sentence: "a hit from behind does not hurt the lion", not
   "good combat". Include the **implicit** ACs the player expects (dead stays dead,
   whoever walks faces the walking direction, damage only from close range, the level
   ends, Continue returns to the right place).
2. **Write the matrix** in `production/qa/ac/<scope>.md`:

   ```markdown
   # AC <scope> (<date>)
   | # | Criterion | Origin | Test | Type | Status |
   |---|---|---|---|---|---|
   | L3 | A hit from behind does not hurt the lion | bug report | test_side_enemies::test_staff_misses_the_lion_behind_hero; bot_side "hit only in front" | scene + bot | PASS |
   ```
   Types: `unit` (plain GUT), `scene` (GUT that instantiates the real .tscn), `bot`
   (scenario played to the end with invariants), `visual` (window capture, reviewed),
   `manual`.
3. **Write the missing tests** before running. A reported bug becomes a test that fails
   first (run it and see red) and passes after the fix.
4. **Run everything**: the whole GUT suite, the scenario bots (3 runs: the bot is
   deterministic, so any variation points to a timing bug), visual captures.
5. **Update the matrix** with the results, and only then build the APK (gf-mobile) and
   install it.
6. **Report** the summarized matrix to the user: how many ACs, how many PASS, what is manual.

## Commands

Templates for the tools live in `tools/godot/` (`bot_template.gd`, `capture_scene.gd`,
`dump_collision.gd`). Each game copies and adapts them under `game/tools/`.

```bash
cd game
HOME="$PWD/.godot_home" godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit
HOME="$PWD/.godot_home" godot --headless --fixed-fps 60 --path . -s tools/bot_<scenario>.gd   # exits 1 on failure
BOT_VERBOSE=1 BOT_SEED=7 ...bot_<scenario>.gd                                                # log every 3 s, fixed seed
# Single test file (note: -gtest is ignored and runs the whole suite)
... -gselect=test_file.gd -gdir=res://tests -gexit
# Visual: needs a window (headless does not render), with a time limit (macOS has no `timeout`)
HOME="$PWD/.godot_home" perl -e 'alarm 40; exec @ARGV' godot --path . -s tools/capture_scene.gd -- res://scenes/x.tscn /tmp/out 60
```

## Reading the result

- **Count the PASS lines, not only the absence of FAIL.** A bot that crashes at startup,
  quits early or never reaches a check prints no FAIL and still proves nothing. The
  expected number of PASS lines (one per check) goes in the matrix, and the run is green
  only when `PASS count == expected` and `FAIL count == 0`.
- A suite that exits 0 with "0 tests" or a script that failed to parse is not green.
  Read the summary line, not just the exit code.
- Green tests have missed real defects: an `Area2D` without a `CollisionShape` (a pickup
  that could never be collected) and actors drawn behind the scenery (z-order). Before
  saying a level is playable, run the scenario bot **and** a render in a real window.

## Real input path (what escapes most often)

- **HUD buttons**: click at the button position, do not call the function. Screen position
  = `root.get_final_transform() * button.get_global_rect().get_center()`, then
  `Input.parse_input_event` with an `InputEventMouseButton` (press now, release on the
  next frame). `push_input` with a viewport coordinate misses the button when the window
  is scaled.
- **Press vs. release**: `Button.pressed` fires on release by default. Test jump/attack
  ordering the way the player does it (one finger, one click at a time).
- **Drags** (manual aim): `InputEventMouseMotion` with `button_mask`, from a point of the
  area to the screen point of the desired vector.
- **Emulator keyboard**: keys arrive in ~30 ms pulses. Logic based on
  `Time.get_ticks_msec` breaks under `--fixed-fps` (the game runs faster than the wall
  clock): pulse tests run in real time, without `--fixed-fps`.
- **Bot movement**: `Input.action_press("move_left")` goes through the same input
  abstraction as the keyboard. Never write `move_vector` directly (an old bot did and
  missed a broken Shift key on the emulator).
- **Follow the game's own hint**: if the scene says "stand under the beehive", the bot
  does exactly that. If the hint does not work, it is a design bug, not a bot bug.

## Bot determinism

- Bot time is counted in **physics frames**, never `Time.get_ticks_msec`. With
  `--fixed-fps` the machine load changes wall-clock results.
- Gameplay randomness uses a **per-level RNG** (`RandomNumberGenerator` with a seed set
  at level start), not the global RNG shared with visual effects. The bot seeds with
  `BOT_SEED` (default 1) so a failing run reproduces.
- A bot that is not reproducible (passes 2 of 3 runs) is a failing test: fix the timing
  or the randomness, do not re-run until green.
- Never edit the bot to make it pass. If a bot needs a change to get through, find out
  whether the game regressed (a Codex batch once changed the bot for "unreachable enemy"
  and "return to arena center" and hid real regressions). When a clone's bot differs from
  the baseline, validate with the original bot.

## Bot-run hygiene

- Two Godot runs in the same project directory corrupt `.godot` (autoload does not
  compile, null player). Parallel runs only on **a copy** (`rsync -a game/ /tmp/game_copy/`
  or an APFS clone `cp -cR`) **and with their own `HOME`**, because `user://` holds the
  save and two runs sharing it give false failures. The final run goes alone.
- After changing art, `godot --headless --path <copy> --import` before capturing:
  `-s` scripts do not reimport a changed PNG, so the capture would use the old texture.
  A new `class_name` also needs `--import` before GUT.
- A GUT test that really starts a New Game swaps the scene and mounts the level at the
  root in the middle of the suite: failures then appear in other tests (doubled trees,
  phantom collisions). `SceneTreeTimer` and lambdas on root nodes outlive the HUD: use
  the node's own tween or a bound method.
- Tests that instantiate the level write a save (it saves on entry): clear it with
  `Save.clear_session()` and `Game.reset_progress()` at the end.
- Tests with `move_and_slide` must wait for real physics frames.
- Freed objects do not compare reliably with null: use `is_instance_valid` or a signal.
- Cover first boot with no saved language/settings: an untested first boot left a game
  black on Android. Before releasing a tester, `pm clear` and open the APK.

## Tests must test behavior

- **Reject tests that only read source code** (`assert_string_contains` on a script's
  text, or file-content greps dressed up as tests). Count `assert_string_contains` and
  `_source(` in the tests of every batch before accepting it. A test must run the thing.
- Localization tests compare against the source language (a PT column with the English
  copied still passes a "not empty" check) and open the screens in each language.
- A test must fail when the feature is removed. Prove it for new tests: break the feature,
  see red.
- Do not accept "pre-existing failures" in a batch report without comparing the diff
  against the old tests that broke. A batch once changed an old test to hide the
  regression it caused.

## Invariants for the scenario bot (check every frame)

Adapt the list to the game. Examples of invariants and the real bug each one caught:

| Invariant | Real bug it caught |
|---|---|
| the level ends (victory) within the time limit | a rock too tall cut the level; a beehive with less reach than the paw distance |
| dead stays on the last death frame | `play()` every frame restarted a non-looping animation (death in a loop) |
| damage to the player only with an enemy close | a lion's leap hurt from 100 px away |
| a hit only lands on a target in front | a wide lion body invaded the staff box from behind |
| whoever walks faces the walking direction | enemies walking backwards |
| slow motion only while aiming (and on the fall screen) | aim turned on with a still touch |
| the player is never stuck while walking | grass decals with collision blocked every 96 px |
| the player stays inside the world | with no wall at the edges, the hero left the map |

Read the state **at the instant of the event** (the game records `last_hit` on the hit):
reading it later in `_process` sees the already changed direction and creates false
positives. See `tools/godot/bot_template.gd` for the skeleton (PASS/FAIL lines,
`BOT_SEED`, physics-frame time, real input injection).

## Visual

Capture in a window every screen that was touched, enlarge it (`Image.get_region` +
`resize` nearest) and look at it: cut sprites, elements behind the HUD (the joystick
covers the first ~100 px, buttons the last ~140 px), overflowing text, hint arrow, a bar
with the wrong height (a `Control` gets its size only after entering the tree). Compare
with the location sheet: whatever it asks for and the scene lacks is a red AC.

- **Verify captures in a real window.** A capture script often photographs the initial
  scene without building the state (a Codex batch did this repeatedly), or a "new" capture
  is an old file copied from a cache. Run the capture yourself, check the timestamp, and
  open the image.
- Review boards must come from the asset the game loads, not from loose files: an
  approved board once hid sheets that were missing expressions. Capture inside the game.
- A green test with a broken UI exists (overlapping settings panel, a glyph missing from
  the font rendering as a white square). Only the window capture catches it.

## Tester latency vs. real damage bugs

When a blind tester reports "I hit 13 times and the bar did not move", suspect the
tester's adb latency against a short reaction window before touching damage. First run a
probe with a fixed reaction (a bot hitting at the right moment). Then check who reads
the data file you are about to tune: a balance JSON that nothing loads changes nothing.

## Tooling pitfalls

- A script that `extends SceneTree` cannot type game classes (`PlayerSide`, `SideEnemy`,
  ...): it compiles before the autoloads and fails with "Identifier not found: Audio". Use
  untyped variables, or `load("res://...")` for what you need. Do not swap the autoload
  for `get_node("/root/X")` in code under test (it breaks tests outside the tree).
- The `_ready` of an autoload runs **after** the `_initialize` of a `-s` script and can
  reapply saved settings (language, etc.). A script that sets them must mount the scene
  on the 2nd frame.
- Headless has no viewport texture: captures only in a window.
- A hand-made collision mask can leave holes; a range grid of 8 px does not see a 12 px
  gap. Test gaps pixel by pixel (or with a 2 px step) and filter components under 64 px.
- Do not use the user's emulator to test (they play on it in parallel); install the APK
  there only at the end, with the matrix green.
- Do not test a feature on a device with the machine overloaded: an overloaded emulator
  gives ANRs and slow captures that measure nothing about the game.
