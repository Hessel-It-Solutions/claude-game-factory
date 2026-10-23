---
name: gf-gameplay
description: "Implementation of the game mechanics in Godot 4: player character (movement, physics, combat, abilities), enemies and bosses with state machine AI, hitbox/hurtbox, damage and health, collectibles, camera, game feel (coyote time, buffer, hitstop, screen shake, particles) and data-driven balancing. Use from W6 on, or when the user asks to implement, fix or tune a mechanic, enemy, boss or the feel of the controls."
---

# gf-gameplay: mechanics

Implements the mechanics in Godot 4: the player (movement, combat, abilities), enemies and bosses with state machine AI, hitboxes, damage and health, pickups, camera, and game feel (coyote time, input buffer, hitstop, screen shake, particles), with balance values kept in data files. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Implementing or fixing a mechanic, enemy or boss
- Tuning how the controls feel
- Rebalancing damage, health or timing

Produces: `game/scenes/actors/`, `game/scripts/gameplay/`, `game/data/balance/`.

Works with: gf-game-design, gf-sprites, gf-autotest.

---

Inputs: `docs/01-gdd.md` (mechanics, parameters, enemies), `docs/08-content-plan.md`, sprites in `game/assets/sprites/`, gf-godot-core contracts. Owner of `game/scenes/actors/`, `game/scripts/gameplay/`, `game/data/balance/`.

## How to work

1. For each GDD mechanic in the wave scope: GUT test first when the rule is verifiable (damage, cooldown, jump reaches X tiles), then the implementation.
2. Parameters in `data/balance/<actor>.json` (speed, gravity, heights, health, damage, cooldowns), with the initial numbers from the GDD. The script reads from the Resource, never hardcodes. Confirm that something actually reads each JSON before tuning it.
3. Each actor is a scene: `CharacterBody2D` + `AnimatedSprite2D` (SpriteFrames from the importer) + `StateMachine` + `Hitbox`/`Hurtbox` (`Area2D` on collision layers documented in `game/core/collision_layers.md`).
4. Animation follows state: the state requests the animation; frame events (the hit lands on frame 3) through the `frame_changed` signal with a table in the balance file, not a loose timer.

## Two controllers when the camera is hybrid

`PlayerTopDown` (8 directions on the joystick, animation in 4 directions with flip, no gravity) and `PlayerSide` (gravity, jump if the GDD asks, side-mode mechanics). Both share `PlayerStats` (health, items, flags) through `Game` and the same SpriteFrames (`side_*` states). Do not make a single controller full of `if camera_mode`.

## Godot 4 physics gotchas

- **Top-down bodies use `MOTION_MODE_FLOATING`.** `CharacterBody2D` defaults to GROUNDED: a sloped edge (normal within 45 degrees of "up") counts as floor and the body gets stuck instead of sliding.
- Every `Area2D` needs a `CollisionShape2D`; an area without a shape never triggers (a pickup that could never be collected passed all tests).
- Z order: confirm actors are not drawn behind the scenery; in top-down use y-sort.
- Do not scale actor sprites by a fractional factor (it blurs the grid); fix size in the art pipeline.
- `move_and_slide` tests must wait for real physics frames.
- Measure the true collision shape of the player (capsule size at the real world scale) before measuring corridors: testing with a smaller shape hides gaps that the real body cannot cross.
- A freed object does not compare with `null` reliably: use `is_instance_valid`.
- Tell aim range from hit radius: a global "aim radius" that was overwritten to a huge value made distant projectiles hit. A fix for one actor must not change a global rule.
- A blocked return path must account for a save at an earlier checkpoint: move the checkpoint to the exit side together with the block.
- Gameplay time in physics frames and randomness in `Game.rng`, so bots can reproduce a run.
- A bot that walks in straight lines and presses keys fails against real walls: it needs a navigation grid per level and route points on free ground computed from the body-dilated mask. A small movement vector falls into the dead zone; use a strong vector (around 200 in the input units).

## Game feel for mobile (mandatory for platformer/action)

- Coyote time (~0.1 s) and jump buffer (~0.12 s); variable jump by hold time.
- Short hitstop (2 to 4 frames) and light screen shake on hit; respect the reduce-motion option in `Settings`.
- Damage feedback: sprite flash (white flash shader using a palette color), knockback, short invincibility.
- Vibration (`Input.vibrate_handheld`) on strong hits, with an option to turn it off.
- Camera: `Camera2D` with smoothing and per-level limits, integer pixel position snapping, look-ahead in the movement direction. Never place the camera outside the world.
- Touch is imprecise: generous player attack hitbox, fair player hurtbox. Do not restrict manual aim to fix an unrelated bug.
- Latency matters when reading a blind playtest: "I hit it 13 times and the bar did not move" can be adb tap latency against a 0.8 s window, not a damage bug. Probe with a fixed reaction before touching damage.

## Enemies and bosses

- Minimum states: idle/patrol, notice, attack (with a visible telegraph of at least 0.4 s), recover, hurt, death.
- Bosses: phases by health percentage, patterns in data (`data/balance/boss_<id>.json`), each attack with an animation and sound telegraph.
- Spawns and positions come from the level (gf-levels), not from the enemy script.
- A "sleeping" or resting enemy must not flatten the standing sprite; use a dedicated pose or animation.

## Integration

- Global events (death, pickup, checkpoint) through `Events`; UI and audio listen.
- SFX by id (`Audio.play_sfx("sfx_sling_throw")`) per `audio_map.json`.
- Need a new animation or a frame adjustment? Request it from gf-sprites in the report, with state and frames.

## Verification

- `gut` green; each actor's test scene runs without errors headless.
- Guided manual test: GDD checklist (heights, distances) checked in the test scene, with the result in the report.
- 60 fps in the test scene with 10 active enemies (measure with `Performance.get_monitor`).
- Run the level bot and a windowed render before saying it is playable. If a Codex batch changed the bot to make a test pass, compare the batch bot against the baseline and validate with the original bot.
