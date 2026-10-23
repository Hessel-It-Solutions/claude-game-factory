# Godot 4 test tools

Generic templates. `gf-setup` copies them into the game repo as `game/tools/`; adapt them
there. They reference no autoload and no game class, and parse on Godot 4.x
(checked with `godot --headless --check-only --script <file>`).

All three are `extends SceneTree` scripts run with `-s`. Because of that they compile before the
autoloads exist: do not type game classes in them (use untyped variables and `load()`).

| File | Purpose | Needs a window |
|---|---|---|
| `dump_collision.gd` | Rasterizes static collisions of a scene into a mask PNG plus a JSON of shapes | no |
| `capture_scene.gd` | Mounts a scene and saves a screenshot after N frames | yes |
| `bot_template.gd` | Skeleton of an input-only scenario bot with invariants | no |

## dump_collision.gd

```bash
HOME="$PWD/.godot_home" godot --headless --path . -s tools/dump_collision.gd -- \
    res://scenes/level_01.tscn /tmp/level_01.png 1920 1080
```

Arguments: scene, output PNG, width, height (or env `COLLISION_SCENE`, `COLLISION_OUT`,
`COLLISION_W`, `COLLISION_H`). White pixels are walls. Handles `StaticBody2D` rectangles and
polygons and `TileMapLayer` tiles with physics polygons. Use it to compare a painted map against
real collision, and to test gaps pixel by pixel (a coarse grid does not see a 12 px gap).

## capture_scene.gd

```bash
HOME="$PWD/.godot_home" perl -e 'alarm 60; exec @ARGV' godot --path . -s tools/capture_scene.gd -- \
    res://scenes/level_01.tscn /tmp/shot.png 60 2
```

Arguments: scene, output PNG, frame to capture (default 60), integer scale (default 2, nearest).
Headless cannot render, so run it in a window and always with a time limit.

Autoload `_ready` gotcha: with `-s`, each autoload's `_ready` runs after the script's
`_initialize` and can reapply saved settings (language, volume). The scene is therefore mounted
on the 2nd frame. To prepare state (reset progress, set a locale, set flags), copy the file and
fill `_setup()`; it runs after the autoloads and before the scene is mounted.

After changing art, run `godot --headless --path . --import` first. `-s` does not reimport a
changed PNG, and the capture would use the old texture. Open the PNG afterwards: a capture
script can silently photograph the wrong state.

## bot_template.gd

A short skeleton (about 200 lines) of a scenario bot. Edit `SCENE`, `EXPECTED_CHECKS`, the
scenario in `_initialize`, how the player is found, and `_invariants`.

```bash
HOME="$PWD/.godot_home" godot --headless --fixed-fps 60 --path . -s tools/bot_level_01.gd
BOT_SEED=7 BOT_VERBOSE=1 ... # fixed seed, log every 3 s
```

What it enforces:

- **Real input.** Steps use `Input.action_press` and mouse events at the control's window position.
  Never write the player's movement vector or call game functions to progress.
- **Physics-frame time.** `now()` is `frames / physics_ticks_per_second`. `Time.get_ticks_msec`
  breaks under `--fixed-fps` and under machine load.
- **Seed.** `BOT_SEED` seeds the global RNG (default 1). Give gameplay its own per-level RNG so
  effects do not consume the same stream.
- **Invariants every frame**, read at the instant of the event. Example set: stays inside the world,
  never stuck while walking, dead stays on the last death frame, damage only with an enemy close,
  a hit only lands in front. Add the ones your game needs.
- **PASS/FAIL lines and a count.** Green means FAIL count 0 **and** PASS count equal to
  `EXPECTED_CHECKS`; a bot that exits early prints no FAIL and proves nothing. Exit code 1 on failure.
- **Watchdog.** A scenario that does not finish within `TIME_LIMIT` fails as a softlock.

Run rules: one Godot per project directory. Parallel runs only on a copy of the project with its own
`HOME`, or the shared `.godot` and `user://` save give false failures. Run the final regression
alone. Never edit the bot to make it pass: find out whether the game regressed. Run it 3 times;
differing results mean a timing or randomness bug.
