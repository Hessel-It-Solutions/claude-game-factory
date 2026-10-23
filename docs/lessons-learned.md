# Lessons learned

This is a running log of what went wrong while making *David: Rise of a King* and what we changed because of it. Most of these lessons are already baked into the skills as rules or gotchas. They are collected here so you can read them in one place, and so contributors can add their own.

Add to this file when you learn something the hard way. Keep each entry concrete: what happened, what to do instead.

## Art direction and fidelity

- **The storyboard is the bar.** Nothing visual goes into the game unless it follows the approved storyboard and art direction. Every visual delivery ships with a side-by-side board: the asset at game scale, next to the storyboard frame and the hero, on top of the real level. Below the bar, it gets redone.
- **Keep detail consistent.** A character must not look less detailed than the scenery, or the other way around. The producer rejects a delivery where one side looks more worked than the other.
- **Cut character bases out of the storyboard; do not ask AI to redraw them.** When we asked Runway or Codex to redraw a character from scratch, it came back with a small head, realistic proportions and detail that turned into noise. Cutting the character out of the approved frame (background removal on an 8x enlargement, close holes, keep the largest component, reduce by majority color vote) kept the identity. AI is only used to complete what the frame does not show (other directions, animations), always anchored on the cutout.
- **Secondary characters need their own reference.** A brother generated without his storyboard cutout inherited the hero's colors and came out red-haired.
- **A gesture pose is a bad anchor.** A profile cut from a frame where the character points at something contaminated the walk and idle. Ask for an upright posture or pick another pose.
- **Tiles by script or tileable textures did not reach the key art.** Important rooms became one painted piece over the real blockout of the level, with collision traced from the painting and a little wider than the drawing in passages.
- **Paint big maps in sections.** Use the style storyboard and the first section as tone reference. Fix seams by repainting a band centered on the seam and pasting only the middle with a soft ramp.
- **Image models skip flat color areas.** A blockout with large flat regions comes back unpainted there. Draw blocks in the blockout.
- **Pixel fonts break at small sizes on phones.** Our pixel font was only crisp at 12, 16, 20, 24, 32 and 40 px, and at the ~2.2x scale of a phone small sizes deformed. Body text moved to a legible font (Inter); the pixel font is only for titles and buttons at 20 px or more.
- **No fractional scale on characters.** A 0.8 scale left the hero at about 48 px and blurred the pixels. The storyboard had him at about 70 px in a 640x360 frame.

## Sprites (sprite-gen + Codex)

- Pass `--provider codex` explicitly; without it sprite-gen falls back to another provider.
- Pass the character description with `--description`. The `character` field of `--request-json` is ignored.
- Generate the base at 8x on magenta, or Codex redraws the character.
- `prepare --safe-margin 2`. The default margin (about 9.4% of the cell) cut a 75 px character in an 80 px cell.
- Each raw strip comes back at its own scale. Use `fit.fixed_scales` per state and check the head on a board. `tools/gf/strip_rescale.py` crops a raw strip into frames and rescales it with one factor measured on the body.
- `gen-set` rebuilds the anchor of each direction from `frames/<dir>/idle/frame-0.png` every round. A noisy anchor frame produces a "camouflaged" creature in every action. Put a clean, color-voted strip in the idle frames and run `anchor --all` before `gen-set`.
- Leftover placeholders in `raw/` or manifest rows for states never generated break `gen-set` with "corrupt frames manifest".
- sprite-gen calls Codex internally, so it cannot run inside `codex exec`. Run it from a normal terminal.
- Inserting a new strip into an atlas by sequential index once corrupted neighbor animations. One animation per row, and build the atlas from a config.
- Chroma removal by exact color equality misses the dark fringe. Remove by hue (285 to 330 degrees, saturation above 0.6).

## Godot 4

- Top-down bodies need `MOTION_MODE_FLOATING`. The default (grounded) treats a slanted edge as a floor and the body sticks to it.
- `CollisionPolygon2D` with `BUILD_SEGMENTS` only has an outline; the inside of a rock does not collide.
- A collision mask image converted to `BitMap` needs an alpha channel. A grayscale PNG makes `opaque_to_polygons` return one polygon the size of the image, and the level has no walls. Check the polygon count.
- Filter tiny components (under ~64 px) from a thresholded mask; loose pixels become snag points.
- A TileSet collision polygon is relative to the tile center.
- `load()` on a path that is already in `load_threaded_request` deadlocked on a fresh install. `load_threaded_get` consumes the request: keep the resource you got.
- A TileSet whose atlas was loaded in a worker thread did not draw on Android. Load it on the main thread.
- Fonts only through `preload`. A dynamically loaded `.ttf` disappeared in the APK. Textures without preload became white squares in the export.
- Music imports with `loop=false`. Turn looping on in code for everything except stingers.
- A freed object does not compare reliably with `null`. Use signals or `is_instance_valid`.
- A new `class_name` needs `godot --headless --import` before GUT sees it. After changing art, `--import` again, or captures use the old texture.
- Two Godot processes in the same project folder corrupt `.godot/`. Run parallel work on copies with their own `HOME`.
- A `-s` script that references a `class_name` compiles the chain before autoloads exist. In bots, use `load("res://...")` for those classes.
- `"%s" % array` spreads the array as arguments. Use `"%s" % [array]`.
- Android export needs `rendering/textures/vram_compression/import_etc2_astc=true`.

## Testing

- Green tests are not enough. They missed an `Area2D` without a `CollisionShape` (a stone that could never be picked up), actors drawn behind the scenery, an overlapping settings panel, and a glyph missing from the font that showed as a white square.
- Run the scenario bot and a windowed render before saying something is playable. Count the PASS lines, not only the absence of FAIL.
- Make the bot deterministic: game time in physics frames, gameplay RNG per level. `Time.get_ticks_msec` and a shared global RNG made results depend on machine load.
- Two GUT or bot runs at the same time share the save in `user://` and fail for no reason. Give each run its own `HOME`.
- A GUT test that triggers "New game" for real swaps the scene in the middle of the suite and breaks unrelated tests.
- First boot with no saved language was not covered and left the game black on Android. Always `pm clear` and open the APK before handing it to a tester.
- Check that the APK only ships `.translation` files, never the source `.csv`. In one round, raw translation keys showed on the phone, and neither GUT nor the bot noticed.
- Before tuning a number, find who reads it. A balance JSON for an enemy was not read by any code.

## Blind playtest

- The tester has to play like a person: think while the game is paused, act in bursts (one adb call with several taps), and keep a `lessons.md` file it re-reads after each death. Before that, enemies killed the tester before it could react.
- Deaths caused only by the tester's own latency are marked `[TESTER LATENCY]` and do not count as friction. "I hit it 13 times and the health bar did not move" turned out to be adb latency against a 0.8 s window, not a damage bug.
- If the method changes in the middle of a run, split the report into Phase A and Phase B. Data from before the change is biased.
- The same tester continues until the chapter ends. After each fix round, a fresh tester starts from zero.
- Players expect Zelda-style guidance. If a tester does not know where to go, that is a bug.
- Run the playtest with the machine idle. With other heavy work running, the emulator throws ANRs and screenshots take 12 to 20 s, and deaths stop measuring the game.
- Cost: a Fable or Opus tester costs about 700k tokens for a 35 to 50 minute session. A Codex tester (with high reasoning) costs ChatGPT quota instead. Pick per round.

## Android emulator

- Check the GPU. Our AVD had `hw.gpu.enabled=no` and spent minutes compiling shaders on a software renderer; the game looked frozen. Use `hw.gpu.mode=host`.
- `adb shell screencap` takes about 0.5 s. For animation use `adb shell screenrecord` and ffmpeg.
- A HUD `Control` consumes touches before `_unhandled_input`.
- When the emulator goes offline or stops forwarding clicks: `adb emu kill`, wait for the old qemu process to exit, start again with `-no-snapshot-load`.
- `adb shell dumpsys package` can hang. Use `pm path` and `ls -l` on the base APK to confirm an install.
- Export with the real `HOME` (the Android templates live there). With an isolated `HOME` the export fails and adb happily reinstalls the old APK. Check the size and time of the installed file.

## Shell and process gotchas (macOS)

- macOS has no `timeout`. Use `perl -e 'alarm N; exec @ARGV' cmd ...`.
- Wait for a process by PID (`while kill -0 $PID`), never with `ps | grep "text"`: the loop itself had the text in its command line and waited 40 minutes for nothing.
- An unquoted heredoc (`<<EOF`) with backticks in the text runs the command inside the backticks. Use `<<'EOF'`.
- zsh does not split `"$VAR"` into words. Build argument lists in bash with arrays.
- Homebrew ffmpeg may lack libvorbis: `-c:a vorbis -strict -2`.

## Process

- Pre-production approved before production. It felt slow in week one and saved the project in week two.
- A one-off request ("update the memory", "save the handoff") is only that. Do it, report, stop.
- When you show the user an asset, link the absolute path so they can click it.
- Keep `production/DECISIONS.md` append-only. When a batch contradicts an old decision, undo the batch, not the decision.
