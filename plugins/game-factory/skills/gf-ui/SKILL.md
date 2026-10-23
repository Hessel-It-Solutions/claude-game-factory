---
name: gf-ui
description: "Pixel art UI and HUD for mobile: UI kit (buttons, 9-slice panels, bars, icons), bitmap font, game HUD, on-screen touch controls, dialogue box with portrait, menus and flow screens, Godot Theme (.tres), safe areas and accessibility. Use from W5 on, or when the user asks for a menu, HUD, buttons, icons, font, pause/game over screen, or a phone layout fix (\"make the HUD\", \"fix the layout on the phone\")."
---

# gf-ui: interface

Builds the pixel art interface for phones: UI kit (buttons, 9-slice panels, bars, icons), fonts, HUD, on-screen touch controls, dialogue box with portrait, menus and flow screens, the Godot Theme, safe areas and accessibility. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Making the HUD, menus, pause or game over screens
- Adding touch controls or a dialogue box
- Fixing layout on a phone or a notch

Produces: `art/ui/`, `game/assets/ui/`, `game/scenes/ui/`, the Theme.

Works with: gf-art-direction, gf-godot-core, gf-mobile.

---

Inputs: GDD sections 2 (controls) and 9 (screens), screen flow board in `docs/06-storyboard/`, `docs/02-art-direction.md` (UI prompt block). Read `gf-runway`.

## UI kit (art)

1. `generate_image` with the official UI model (usually `gpt-image-2`, good at layout), `@style`, one grid sheet with: button normal/pressed/disabled, panel, dialogue frame, health bar (background and fill), item slot, the GDD icons. Chroma background, "flat front view, no perspective, no text".
2. `$SG slice-sheet` to separate the pieces, then `pixelize.py` at the exact logical size (button 32x16, panel 48x48 etc.) with the palette.
3. Panel and button pieces are **9-slice**: draw or adjust them so borders and corners have a fixed size (for example 6 px) and the middle is repeatable. Record the margins in `art/ui/ui_kit.md`.

Small icons (16x16, 24x24) almost always need script retouching or regeneration on a larger grid; AI fails on tiny icons. Validate at 1x.

## Fonts

Prefer a free-license (OFL) pixel font that covers every language of the concept (for EN/PT/ES: á, ã, ç, ê, õ, ñ, ¿, ¡) and a size that is legible on a phone. Record font and license in `art/ui/ui_kit.md`. AI-generated fonts do not work well; do not try.

Rules learned on device:

- **A pixel font is only crisp at a few sizes.** Test the chosen font and keep a list of the sizes that render cleanly (Example (David: Rise of a King): Pixelify Sans was clean only at 12, 16, 20, 24, 32 and 40 px; at 10 px a name rendered with a malformed first letter). Make the theme helper round every requested size to the nearest clean one.
- **Body text goes in a legible font, not the pixel font.** At phone scale (about 2.2x) a small pixel font deforms. Use the pixel font only for titles and buttons at 20 px or more; use a plain readable font (Example: Inter) for dialogue, descriptions and settings.
- Glyphs the font lacks (for example decorative symbols like ◆) render as a white square. Check every symbol you use, or draw it as an icon.
- **Fonts only through `preload`.** A `.ttf` loaded dynamically by path at runtime disappears in the Android APK.
- Godot `FontFile`: `antialiasing = None`, `hinting = None`, `subpixel_positioning = Disabled`, size as an integer multiple of the native size.

## Godot Theme

`game/assets/ui/theme.tres`: StyleBoxTexture with the 9-slice margins, the default font, palette colors for text and focus. All screens use this Theme; no local color overrides.

## Screens and HUD (scenes)

`game/scenes/ui/`: `main_menu.tscn`, `pause.tscn`, `game_over.tscn`, `hud.tscn`, `dialogue_box.tscn` (text box at the bottom of the screen, animated character portrait beside it (`AnimatedSprite2D` with the portrait SpriteFrames), name, character-by-character reveal and tap to advance; portrait on the left or right depending on who speaks), `touch_controls.tscn`, plus the GDD flow screens.

Mobile rules:

- Touch targets at least 44x44 pt real (compute from the logical screen scale factor).
- Respect the safe area: `DisplayServer.get_display_safe_area()` applied to a root container of the screens and the HUD.
- Fixed-width layouts (for example 640 px) must be centered with a stage helper on wide screens (20:9), not left-aligned.
- Touch controls: virtual joystick with dead zone and dynamic area (appears where the thumb touches on the left half), action buttons on the right; adjustable opacity; option to swap sides (left-handed) in settings.
- Portrait or landscape per the concept; lock the orientation in the project.
- Text always through `tr()` with a key (localization), including labels built by helper functions.
- Navigation also works with controller/keyboard (visible focus) for desktop tests and accessibility.
- On Android, a HUD `Control` consumes touch before `_unhandled_input`. Set `mouse_filter` to ignore on decorative controls, and test the touch path on a device or emulator.
- Settings panels must not overlap; test them open, in every language.

UI signals to the game go through the events autoload of gf-godot-core; the UI does not access gameplay nodes directly.

## QA

Screenshots in 3 aspect ratios (16:9, 19.5:9, 4:3 tablet) through gf-qa headless runs or manual capture; no element under the notch or gesture bar; texts without clipping in every language of the concept (PT-BR and ES are often 20% to 30% longer than EN). A green unit test does not prove the UI is fine: capture the real screens in a window.
