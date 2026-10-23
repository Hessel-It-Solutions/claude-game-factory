---
name: gf-godot-core
description: "Architecture and technical base of the Godot 4 pixel art mobile game project: scaffold, pixel-perfect settings, folder structure, autoloads (Events, Game, Save, Audio, Scenes, Settings), Aseprite JSON to SpriteFrames importer, state machine, abstract touch input, save system, GDScript code patterns and GUT tests. Use in W5 of /game-factory, and whenever something requires changing project.godot, autoloads, addons or contracts between systems (\"set up the Godot project\", \"add an autoload\")."
---

# gf-godot-core: technical base

Owner of `game/project.godot`, `game/autoload/`, `game/core/`, `game/addons/`. Other skills request changes to these files through the wave report.

## Scaffold

```text
game/
  project.godot
  autoload/   events.gd game.gd save.gd audio.gd scenes.gd settings.gd
  core/       state_machine/ (state_machine.gd, state.gd), input/ (touch_input.gd), util/
  addons/     gut/ (tests), aseprite_importer/ (ours, see below)
  assets/     sprites/ environments/ ui/ audio/ portraits/ fonts/
  scenes/     main.tscn  actors/  levels/  cutscenes/  ui/
  scripts/    gameplay/ dialogue/ platform/
  data/       balance/ levels/ dialogue/
  tools/      dump_collision.gd and capture/bot scripts (copied by gf-setup)
  tests/
```

## project.godot (pixel-perfect mobile)

- `display/window/size/viewport_width|height` = logical screen from the art direction.
- `display/window/stretch/mode = "viewport"`, `aspect = "expand"`, `scale_mode = "integer"` (allow `fractional` only if integer leaves bars that are too large on some device; record the decision).
- `display/window/handheld/orientation` per the concept.
- `rendering/textures/canvas_textures/default_texture_filter = 0` (Nearest).
- `rendering/2d/snap/snap_2d_transforms_to_pixel = true`, `snap_2d_vertices_to_pixel = true`.
- `rendering/renderer/rendering_method = "mobile"` (or `gl_compatibility` if the target includes old Android; decide with gf-mobile).
- `rendering/textures/vram_compression/import_etc2_astc = true`: the Android export fails without it.
- `input_devices/pointing/emulate_touch_from_mouse = true` to test on desktop.
- Physics: `physics/common/physics_ticks_per_second = 60`.
- Audio: `default_bus_layout.tres` with buses Master, Music, SFX, UI, Voice, Ambience (rules from gf-audio).
- Translations: the project ships only compiled `.translation` files in the export, not the source CSV (see gf-mobile). Run `godot --headless --path game --import` after a batch of strings changes so the new `.translation` files exist.

## Autoloads

| Autoload | Responsibility |
|---|---|
| `Events` | global signals only (player_died, dialogue_started, level_completed...). Decouples UI, audio and gameplay. |
| `Game` | session state: chapter, level, checkpoint, story flags; also the gameplay RNG per level (`Game.rng`) |
| `Save` | `user://save_<slot>.json` with schema version and migration; saves on pause and focus loss (`NOTIFICATION_APPLICATION_PAUSED`) |
| `Audio` | plays by id using `assets/audio/audio_map.json`; music crossfade; SFX player pool; turns the loop on for music |
| `Scenes` | scene change with transition (fade/pixel dissolve) and threaded loading (`ResourceLoader.load_threaded_request`) |
| `Settings` | volume per bus, vibration, controls side, language, controls opacity |

## Sprite importer

`addons/aseprite_importer/`: EditorImportPlugin (or a tool script run headless) that reads `game/assets/sprites/<id>/<id>.json` (sprite-gen Aseprite JSON) + `anim.json` and generates `<id>.tres` (SpriteFrames): one animation per `meta.frameTags`, `AtlasTexture` per frame with the JSON `region`, speed and loop from `anim.json` (per-frame duration from the JSON when frames are not uniform, via relative frame duration). Run:

```bash
godot --headless --path game --script res://addons/aseprite_importer/build_all.gd
```

GUT test covering: number of animations = number of tags, frames per tag, region of the first frame.

## Code patterns

- GDScript 2 with static typing everywhere (`var speed: float`, `func f() -> void`).
- Actors with `StateMachine` (node with child states); states do not call UI.
- Balance data in `data/balance/*.json`, loaded into a `Resource`; no magic numbers in gameplay scripts. Before tuning a number, check who reads the JSON: a balance file nobody reads changes nothing.
- Small composed scenes; communication: parent calls child, child emits signal; global through `Events`.
- Input: `core/input/touch_input.gd` translates touch, keyboard and controller into InputMap actions (`move_left`, `jump`, `attack`...). Gameplay only reads actions. A keyboard on an emulator arrives as a down/up pair of about 30 ms even while held, so touch input should hold a direction for a short pulse.
- Game time is counted in physics frames, never `Time.get_ticks_msec`; gameplay randomness uses `Game.rng` per level, not the global RNG shared with effects. Otherwise bots are not reproducible.

## Godot 4 gotchas

- **Threaded loading:** a synchronous `load()` on a path that has a pending `load_threaded_request` can deadlock on a fresh install. `load_threaded_get` consumes the request: on the next frame the status is `INVALID_RESOURCE`, so keep the resource you already got. A `TileSet` whose atlas came from a worker thread may not draw on Android: load it on the main thread.
- **Textures must be preloaded** (or referenced by a scene): a texture loaded by path at runtime can turn into a white square in the Android export.
- **Fonts only by `preload`** (a dynamically loaded `.ttf` disappears in the APK).
- A freed object does not compare reliably with `null`: use a signal or `is_instance_valid`.
- A new `class_name` requires `godot --headless --import` before GUT can see it.
- A `-s` script (bot, capture) that references a `class_name` compiles that chain before the autoloads exist ("Identifier not found: Game/Audio"). In bots call `load("res://...").method()`; do not replace the autoload with `get_node("/root/X")` (it breaks tests outside the tree).
- In a `-s` capture script, the `_ready` of the Settings autoload runs after `_initialize` and re-applies the saved language: change the locale and build the scene on the second frame.
- `"%s" % array` spreads the array as arguments: use `% [array]`.
- A `Control` in the HUD consumes touch before `_unhandled_input` on Android.
- Music imports with `loop = false`; the Audio autoload turns the loop on (except stingers).
- Two Godot processes on the same project directory corrupt `.godot` (autoload not compiled, null player). Parallel runs only on copies (`rsync -a game/ /tmp/game_copy/` or an APFS clone `cp -cR`) and with a different `HOME` each.
- Two GUT or bot runs at once share `user://` and fail falsely; give each its own `HOME` (for example `HOME=$PWD/.godot_home`) and run the final round alone.
- The first boot with no saved language was not covered by tests and left the game black on Android: always test a clean install.

## GUT

- Use the official GUT release for your Godot line, in `game/addons/gut`, config in `game/.gutconfig.json`; exclude it from the export.
- `assert_almost_eq` needs a tolerance; use `autofree` / `add_child_autofree`.
- A test using `move_and_slide` must wait for real `physics_frame`s.
- A test that calls "New game" for real switches the scene and builds the level at the root in the middle of the suite; failures then show up in other tests (doubled canopies, ghost collision). `SceneTreeTimer` and lambdas on root nodes outlive the HUD: use the node's own tween or a bound method.
- To run a single file: `-gselect=<file> -gdir=res://tests`. `-gtest=res://...` is ignored and runs the whole suite.
- Never accept a test that only reads source (`assert_string_contains` on `.gd` text) or a localization test that only checks "not empty": compare against the source language and open the screens in each language.

## Minimum verification

```bash
godot --headless --path game --import            # imports assets without errors
godot --headless --path game -s addons/gut/gut_cmdln.gd -gexit   # tests
godot --headless --path game --quit-after 300    # runs main for 300 frames without log errors
```

W5 delivery: the project opens, the test scene shows the animated protagonist (gf-sprites assets) walking on a test floor, with touch control emulated by the mouse, at 60 fps. Also run a windowed render before declaring anything playable: green tests have missed an `Area2D` without a `CollisionShape` (a pickup that could never be collected) and actors drawn behind the scenery (z order).
