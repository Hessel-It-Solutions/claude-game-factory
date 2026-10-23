---
name: gf-mobile
description: "Mobile platform for the Godot 4 game: Android export presets (debug APK, release AAB) and iOS, signing, adaptive icons and splash, permissions, on-device performance (fps, memory, app size, battery), lifecycle (pause, resume), and monetization when the concept asks (ads, IAP, through official plugins). Use in W7 (vertical slice build), in WF (release), or when the user asks \"build the apk\", \"test on the phone\", \"the game is slow on the phone\", \"add ads/purchases\"."
---

# gf-mobile: build, performance and technical store side

Gets the game onto phones: Android export presets (debug APK, release AAB) and iOS, signing, adaptive icons and splash, permissions, on-device performance (fps, memory, size, battery), pause and resume, and ads or in-app purchases when the concept calls for them. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Building and installing an APK for testing
- The game is slow or broken on a phone but fine on desktop
- Preparing store builds, signing or monetization

Produces: `game/export_presets.cfg`, `game/scripts/platform/`, `builds/`.

Works with: gf-setup, gf-qa, gf-release.

---

Owner of `game/export_presets.cfg`, `game/scripts/platform/`, `builds/`. Toolchain from gf-setup.

## Android export

- "Android" preset: `package/unique_name` = `com.<studio>.<game>`, increasing integer `version/code`, semver `version/name`, architectures `arm64-v8a` (and `armeabi-v7a` if the audience has old devices), orientation from the concept, `screen/immersive_mode = true`.
- Gradle build enabled for AAB and plugins (`gradle_build/use_gradle_build = true`, install the build template from the editor or `--install-android-build-template`).
- Adaptive icon: foreground and background 432x432 from the character key art (gf-release delivers the art; here only configuration). Splash: palette color + pixel art logo, nearest filter.
- The project needs `rendering/textures/vram_compression/import_etc2_astc=true`, otherwise the export fails.
- **Only the compiled `.translation` files go into the APK**, not the source CSV. After a batch of string changes, run `godot --headless --path game --import` so the new `.translation` files exist, and confirm the export includes them.
- Textures and fonts must be loaded through `preload` or scene references, or they turn into white squares or vanish in the export.

```bash
godot --headless --path game --export-debug "Android" ../builds/android/<game>-debug.apk
adb install -r builds/android/<game>-debug.apk && adb logcat -s godot
```

- **The export needs the real `HOME`** (that is where the Android export templates live). With an isolated `HOME` the export fails, and `adb install -r` then reinstalls the old APK. Do not run the export from a sandbox that fakes `HOME`; run it in the main session.
- **Verify what got installed**: compare size and time of the built APK with the one on the device (`adb shell pm path <package>`, then `adb shell ls -l <base.apk path>`). `adb shell dumpsys package` can hang; avoid it for this check.
- `adb` lives in `~/Library/Android/sdk/platform-tools/adb` on macOS and is usually not on `PATH`.
- macOS has no `timeout`: use `perl -e 'alarm N; exec @ARGV' cmd`.
- Do not `cd` into `game/` inside a compound command and then use relative paths for `builds/`; use absolute paths.

Release (WF): upload keystore created **by the user** (password never in the repository; use the variables `GODOT_ANDROID_KEYSTORE_RELEASE_PATH/USER/PASSWORD`), `--export-release "Android" ... .aab`.

## Emulator and device testing

- **Always `adb shell pm clear <package>` and open the APK on a clean first boot before releasing the build to a tester.** A first boot with no saved language once left the game black while all tests were green.
- Check `adb devices` before installing; the emulator sometimes closes on its own.
- The emulator must use host GPU (`hw.gpu.mode=host` in the AVD `config.ini`, plus `hw.keyboard=yes`). With software rendering (SwiftShader) shader compilation takes minutes and the game looks frozen. Confirm the real GPU name in the emulator log.
- `adb shell screencap` takes about 0.5 s; for animation use `adb shell screenrecord` and ffmpeg (the mp4 may not close cleanly).
- An overloaded host causes ANR for everything and kills the game: check the machine load, `adb emu kill`, wait for the old qemu process to exit (otherwise "multiple emulators with the same AVD"), start again with `-no-snapshot-load`. The first tap right after the splash screen sometimes disappears.
- If the emulator stops relaying mouse clicks, the game still answers `adb shell input tap`; restart the emulator.
- A host keyboard arrives as a down/up pair of about 30 ms; `adb emu event send` does not reach Android and `adb shell input keyevent` mimics the pair.
- Read the save of a debug build with `adb shell run-as <package> cat files/save_0.json`. Flags only reach the save at a checkpoint.
- To wait for a process, wait on the PID (`while kill -0 PID`), never on `ps | grep "text"` (the loop's own command line matches).
- Media volume in the emulator can be low: `KEYCODE_VOLUME_UP`.

## iOS export

"iOS" preset with bundle id, the user's team id, icons; `--export-release "iOS"` generates an Xcode project; build and upload through Xcode/Transporter. Signing and the Apple account belong to the user: ask, do not invent.

## Performance (slice targets)

| Metric | Target |
|---|---|
| FPS | stable 60 on a mid-range device (define the reference device with the user), never below 30 |
| Memory | < 300 MB |
| AAB size | < 150 MB (no asset pack) |
| Level load | < 2 s |

Tools: a `Performance` monitor in a debug overlay (debug build only), `adb shell dumpsys gfxinfo`, the Godot remote profiler. Pixel art textures: no mipmaps, lossless compression (VRAM compression ruins pixel art), one atlas per character.

## Lifecycle

`scripts/platform/lifecycle.gd`: pause and save on `NOTIFICATION_APPLICATION_PAUSED` and focus out; resume with a pause screen; the Android back button opens pause or confirms exit.

## Tip / donation (when the concept asks)

- Fixed-value consumable products ("Support the project": US$ 2, 5, 10) through the official Godot Google Play Billing and StoreKit plugins. No reward that affects the game.
- Never an external donation link (PayPal, bank transfer, Buy me a coffee): Apple 3.1.1 and Play payment policies reject it, except an approved non-profit (tax proof) and, on Apple, with Apple Pay.
- A thank-you screen after the purchase; restoring purchases does not apply to a consumable.

## Monetization (only if the concept defines it)

- Ads: community-maintained AdMob plugin for Godot 4 (check the compatible version at the time, record in DECISIONS.md), rewarded by player choice, never an interstitial in the middle of a level.
- IAP: official Godot Google Play Billing and StoreKit plugins.
- Consent (GDPR, UMP) and age rating before any ad.
- Everything behind `scripts/platform/monetization.gd` with a null implementation on desktop.

## Delivery

`builds/` with the artifact, `production/waves/NN-*.gf-mobile.md` with: device tested, measured fps, memory, size, problems. For G4, the user installs the APK and plays the slice on their own phone.
