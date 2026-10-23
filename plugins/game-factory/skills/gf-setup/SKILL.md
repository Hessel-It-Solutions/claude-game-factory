---
name: gf-setup
description: Prepares and verifies the game factory toolchain (Godot 4 + export templates, Python 3.11+, sprite-gen in a venv, ffmpeg/img2webp, Android SDK/JDK, Xcode, Codex CLI, Runway MCP access) and vendors the factory tools into the game repo (tools/gf, tools/codex, tools/playtest, game/tools). Use in W0 of every new game, when a build or sprite-gen fails because of the environment, or when the user asks to "set up the environment", "install godot", "install sprite-gen", "vendor the factory tools".
---

# gf-setup: toolchain

Runs in the main context (it may ask for a password, a license acceptance or a decision). Each step: **check first, install only what is missing**, and record the result in `production/waves/00-setup.md`. Closes gate G0.

The instructions target macOS first. Linux and Windows differences are noted where they are obvious (package manager, paths, `timeout`).

## Checklist

| Item | Check | Install (macOS) |
|---|---|---|
| Godot 4.x | `godot --version` or `/Applications/Godot.app/Contents/MacOS/Godot --version` | `brew install --cask godot`; create a `godot` alias pointing to the app binary |
| Export templates | `ls ~/Library/Application\ Support/Godot/export_templates/` contains the exact Godot version | download `Godot_v<ver>_export_templates.tpz` from the official site and extract it into the `<ver>.stable` folder. Without templates, exports fail even when the editor works. Linux: `~/.local/share/godot/export_templates/` |
| Python >= 3.11 | `ls /opt/homebrew/bin/python3.1[1-3]`, `pyenv versions`, `which uv` | prefer an already installed Python (Homebrew `python@3.12` or `uv python install 3.12`). `pyenv install` compiles from source and segfaulted in `ensurepip` on a recent macOS. Never change the user's global Python; use it only for the sprite-gen venv |
| sprite-gen | `tools/sprite-gen/.venv/bin/sprite-gen --help` | see below |
| ffmpeg, img2webp | `which ffmpeg img2webp` | `brew install ffmpeg webp` (Linux: apt/dnf equivalents). See the Vorbis gotcha below |
| JDK 17 (Android) | `/usr/libexec/java_home -V` | `brew install openjdk@17` (formula, no sudo). Then check `export/android/java_sdk_path` in `~/Library/Application Support/Godot/editor_settings-4.x.tres`: Godot may auto-detect the Android Studio JBR; point it to `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home` (Apple Silicon Homebrew prefix; Intel uses `/usr/local/opt`) |
| Android SDK | `$ANDROID_HOME` or `~/Library/Android/sdk` with platform-tools, build-tools, platforms;android-34 | `brew install --cask android-commandlinetools` and `sdkmanager "platform-tools" "build-tools;34.0.0" "platforms;android-34"`. `adb` is usually not in `PATH`: call `$ANDROID_HOME/platform-tools/adb` or export the path in the scripts |
| Debug keystore | Godot creates its own in `~/Library/Application Support/Godot/keystores/` the first time the editor opens (`godot --headless -e --quit --path <proj>`); otherwise `~/.android/debug.keystore` | `keytool -genkey -v -keystore ~/.android/debug.keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -validity 10000 -dname "CN=Android Debug,O=Android,C=US"` |
| Android emulator (AVD) | `$ANDROID_HOME/emulator/emulator -list-avds` | create one with `avdmanager` (arm64 image on Apple Silicon). Set `hw.gpu.mode=host` and `hw.keyboard=yes` in the AVD `config.ini`; with `hw.gpu.enabled=no` it falls back to software rendering (SwiftShader), shader compilation takes minutes and the game looks frozen. Confirm the real GPU name in the emulator log |
| Xcode (iOS) | `xcodebuild -version` | App Store; only needed in WF, or if the user wants to test on an iPhone earlier |
| Runway MCP | the Runway `whoami` tool authenticated (`mcp__claude_ai_Runaway__whoami` when connected through claude.ai); note credits and models | reconnect the MCP in the client |
| Codex CLI (sprite provider, code engine) | `codex --version` (recent enough for native alpha in sprite-gen) and `codex login status` = "Logged in using ChatGPT" | update by the same method you installed it; `codex login` is interactive: ask the user to run `! codex login` |
| git | repository started at the game root | `git init` + the `.gitignore` from gf-producer |

## Vendor the factory tools

The plugin ships reusable tools. Skills reference game-repo-relative paths such as `tools/gf/gf.sh`, so the tools must live inside each game repo. The plugin tools directory is two levels up from this skill's base directory: `<skill base dir>/../../tools` (the base directory is shown when the skill is loaded). Layout in the plugin:

```text
tools/gf/        CLI, run with tools/gf/gf.sh
tools/codex/     batch launcher for Codex jobs
tools/godot/     GDScript tools (bot template, capture, collision dump), copied to game/tools/
tools/playtest/  blind playtest kit
```

Copy them into the game repo (replace `PLUGIN_TOOLS` with the resolved path):

```bash
PLUGIN_TOOLS="<skill base dir>/../../tools"
mkdir -p tools game/tools
cp -R "$PLUGIN_TOOLS/gf"       tools/gf
cp -R "$PLUGIN_TOOLS/codex"    tools/codex
cp -R "$PLUGIN_TOOLS/playtest" tools/playtest
cp -R "$PLUGIN_TOOLS/godot/."  game/tools/
chmod +x tools/gf/gf.sh
tools/gf/gf.sh --help
```

Rules:

- Copy, do not symlink: the game repo must be self-contained and the tools get versioned with it.
- If `tools/gf` already exists (second run, plugin updated), compare with `diff -r` and ask before overwriting. Local fixes may exist.
- Commit the vendored tools with the game. Do not put `tools/` in `.gitignore` (only `tools/sprite-gen/`).
- Record the plugin version (or the date) of the copy in `production/waves/00-setup.md`.
- Skills never write new loose scripts; if a command is missing, extend `tools/gf` (see gf-producer, "Tools").

## sprite-gen

Library: https://github.com/aldegad/sprite-gen (Python CLI + skill). It lives in `tools/sprite-gen` of each game, with its own venv.

```bash
git clone https://github.com/aldegad/sprite-gen tools/sprite-gen
cd tools/sprite-gen
/opt/homebrew/bin/python3.12 -m venv .venv   # or another installed Python >= 3.11 (3.12 worked well)
.venv/bin/pip install -e .
.venv/bin/sprite-gen --help
```

Export in the shell used by the skills: `SPRITE_GEN_ROOT=<root>/tools/sprite-gen` and `SG=$SPRITE_GEN_ROOT/.venv/bin/sprite-gen`.

The sprite-gen venv already has Pillow and NumPy. The factory scripts run with that same Python: `$SPRITE_GEN_ROOT/.venv/bin/python`.

The factory's sprite-gen provider is **`codex`** (the user's ChatGPT subscription). Export `SPRITE_GEN_DEFAULT_PROVIDER=codex` and still pass `--provider codex` explicitly on every `gen`/`gen-set`: without it sprite-gen falls back to another provider (grok) the user probably has no access to. Do not use `openai` (billed per call). Quick test at G0:

```bash
$SG gen --provider codex --prompt "pixel art red apple, 32x32 pixel grid, transparent background" \
  --out /tmp/sg-codex-test.png --transparent --report /tmp/sg-codex-test.json
```

Concept art, identity bases, scenery, video and audio stay on Runway (see gf-runway).

## Environment gotchas

- **Codex login**: the Codex CLI must be logged in with the ChatGPT account (`codex login status`). Run it as `codex exec ... < /dev/null` or it hangs waiting on stdin.
- **macOS has no `timeout`**: use `perl -e 'alarm N; exec @ARGV' command args` (or `brew install coreutils` and `gtimeout`). Linux has `timeout`.
- **ffmpeg without libvorbis**: Homebrew's ffmpeg may lack `libvorbis`. For `.ogg` use the native encoder: `-c:a vorbis -strict -2`. Quality is acceptable for game audio; a build with libvorbis is better if you need it.
- **Android export needs the real `HOME`**: the Android export templates live there. With an isolated `HOME` the export fails and `adb install` can silently reinstall the old APK. After exporting, check the file size and time, and check the install on the device with `adb shell pm path <package>`.
- **`adb` outside `PATH`**: see the Android SDK row. Scripts should resolve `adb` from `$ANDROID_HOME`.
- **Export needs ETC2/ASTC**: set `rendering/textures/vram_compression/import_etc2_astc=true` in `project.godot` or the Android export refuses to build.
- **Two Godot processes in the same directory corrupt `.godot/`** (autoloads fail to compile, null player). For parallel runs, work in a copy (`rsync -a game/ /tmp/game_copy/`) with a different `HOME`.
- **sprite-gen**: `prepare` does not expose `--directions`/`--mirror`; pass them through `--request-json`. Pass the character description with `--description` (the `character` field in `--request-json` is ignored). Do not run sprite-gen inside a `codex exec` sandbox.
- **Python**: never rely on the system or the user's global Python; the venv Python is the one the factory scripts use.
- **Emulator**: if it goes offline, kill the qemu process and start again with `-no-snapshot-load`, and wait for the old qemu to exit first (otherwise "multiple emulators with the same AVD"). `adb screencap` takes about 0.5 s per frame; for animation use `adb shell screenrecord` + ffmpeg.
- **Windows**: use WSL or Git Bash for the shell scripts; paths and `HOME` differ. Not covered in detail here.

## Godot project

If `game/project.godot` does not exist, the scaffold belongs to gf-godot-core in W5. Setup only makes sure Godot opens in headless mode:

```bash
godot --headless --version
```

## Android proof

A throwaway project in /tmp with an Android preset (`gradle_build/use_gradle_build=false`, arm64) and `godot --headless --path <proj> --export-debug "Android" test.apk`; check it with `apksigner verify`.

## Output

`production/waves/00-setup.md` with a table item | version | status | note. Blocking items for G0: Godot, sprite-gen working with codex, Runway, and the vendored tools (`tools/gf/gf.sh --help` runs). Android and Xcode can stay pending until W7/WF, noted as an open item in STATE.md.
