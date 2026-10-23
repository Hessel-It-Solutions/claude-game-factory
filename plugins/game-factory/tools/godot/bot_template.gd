extends SceneTree
## Skeleton of an input-only scenario bot with invariants. Copy to game/tools/bot_<name>.gd.
##
##   HOME="$PWD/.godot_home" godot --headless --fixed-fps 60 --path . -s tools/bot_<name>.gd
##   BOT_SEED=7 BOT_VERBOSE=1 ...      fixed seed / log every 3 s
##
## Rules this skeleton encodes:
## - Real input only: Input.action_press / parse_input_event, never write the player's
##   move vector or call game functions to "cheat" through a step.
## - Time counts physics frames (`frames / Engine.physics_ticks_per_second`), never
##   Time.get_ticks_msec: --fixed-fps makes wall-clock time meaningless.
## - Seed the global RNG from BOT_SEED (default 1). Gameplay should use its own
##   per-level RNG, seeded at level start.
## - Output is PASS/FAIL lines. The run is green only if FAIL count == 0 AND the PASS
##   count equals EXPECTED_CHECKS (an early exit prints no FAIL and proves nothing).
## - Exit code 1 on any failure. A watchdog fails a scenario that never finishes.
##
## Do not type game classes or autoloads here: a `-s` script compiles before the
## autoloads exist ("Identifier not found: X"). Use untyped variables and load().

const SCENE := "res://scenes/level_01.tscn"   # edit: the scenario's scene
const TIME_LIMIT := 120.0                       # seconds of game time before "softlock"
const STUCK_LIMIT := 6.0                        # seconds walking without moving
const EXPECTED_CHECKS := 4                      # edit: number of check() names below

var frames := 0
var level: Node
var player                                      # untyped on purpose
var verbose := false
var checks := {}                                # name -> bool
var failures: Array[String] = []
var held: Array[StringName] = []
var steps: Array[Callable] = []                 # scenario, consumed one at a time
var step_started := 0.0
var last_pos := Vector2.ZERO
var stuck_t := 0.0
var finished := false
var log_t := 0.0


func _initialize() -> void:
	verbose = OS.get_environment("BOT_VERBOSE") == "1"
	var seed_text := OS.get_environment("BOT_SEED")
	seed(int(seed_text) if seed_text.is_valid_int() else 1)
	# Fresh game state here (reset progress, clear the session save) via the autoloads:
	#   root.get_node("Game").reset_progress(); root.get_node("Save").clear_session()
	steps = [
		go_to(Vector2(400, 300)),
		press_action(&"attack", 0.2),
		wait_until(func(): return level_done(), "level ends"),
	]
	change_scene_to_file.call_deferred(SCENE)


func now() -> float:
	return float(frames) / float(Engine.physics_ticks_per_second)


func say(msg: String) -> void:
	print("[%6.1f] %s" % [now(), msg])


## Record a named invariant. First failure wins and is reported once.
func check(check_name: String, ok: bool, detail := "") -> void:
	if not checks.has(check_name):
		checks[check_name] = true
	if not ok and checks[check_name]:
		checks[check_name] = false
		failures.append("%s: %s" % [check_name, detail])
		say("FAIL %s %s" % [check_name, detail])


# ---------------------------------------------------------------- real input

func hold(action: StringName) -> void:
	if not action in held:
		held.append(action)
	Input.action_press(action)


func release_all() -> void:
	for a in held:
		Input.action_release(a)
	held.clear()


## Click a Control the way a finger would: window coordinates, press now, release next frame.
func click_control(control: Control) -> void:
	var pos: Vector2 = root.get_final_transform() * control.get_global_rect().get_center()
	for pressed in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = pressed
		e.position = pos
		e.global_position = pos
		Input.parse_input_event(e)   # simplified: release in the same frame; queue it for strict tests


# ---------------------------------------------------------------- scenario steps
# A step is a Callable called every physics frame; it returns true when finished.

func go_to(target: Vector2, tolerance := 8.0) -> Callable:
	return func() -> bool:
		if player == null:
			return false
		var delta: Vector2 = target - player.global_position
		release_all()
		if delta.length() <= tolerance:
			return true
		if absf(delta.x) > tolerance:
			hold(&"move_right" if delta.x > 0.0 else &"move_left")
		if absf(delta.y) > tolerance:
			hold(&"move_down" if delta.y > 0.0 else &"move_up")
		return false


func press_action(action: StringName, seconds: float) -> Callable:
	var started := [-1.0]
	return func() -> bool:
		if started[0] < 0.0:
			started[0] = now()
			Input.action_press(action)
		if now() - started[0] >= seconds:
			Input.action_release(action)
			return true
		return false


func wait_until(condition: Callable, label := "") -> Callable:
	return func() -> bool:
		if condition.call():
			if label != "":
				say("reached: " + label)
			return true
		return false


func level_done() -> bool:
	# Edit: how the game signals the end (a flag, a signal-fed variable, a scene change).
	return level != null and level.get("finished") == true


# ---------------------------------------------------------------- main loop

func _process(_delta: float) -> bool:
	frames += 1
	if finished:
		return true
	level = current_scene
	if level == null:
		return false
	if player == null:
		player = level.get("player")   # edit: how your scene exposes the player
		if player != null:
			last_pos = player.global_position
			check("player exists", true)
	if now() > TIME_LIMIT:
		check("scenario ends in time", false, "softlock after %.0f s" % now())
		return _report()
	if player != null and is_instance_valid(player):
		_invariants(1.0 / float(Engine.physics_ticks_per_second))
	if verbose:
		log_t += 1.0 / float(Engine.physics_ticks_per_second)
		if log_t >= 3.0 and player != null:
			log_t = 0.0
			say("pos=%s held=%s steps_left=%d" % [player.global_position.round(), held, steps.size()])
	if not steps.is_empty():
		if steps[0].call():
			steps.pop_front()
			step_started = now()
	else:
		check("scenario ends in time", true)
		return _report()
	return false


## Check these EVERY frame. Read state at the instant of the event, not later.
func _invariants(dt: float) -> void:
	var at: Vector2 = player.global_position
	# 1. Inside the world (edit: use your world bounds).
	check("player stays inside the world", Rect2(-64, -64, 4096, 4096).has_point(at), "at %s" % at)
	# 2. Never stuck while trying to walk.
	if not held.is_empty() and at.distance_to(last_pos) < 0.05:
		stuck_t += dt
		if stuck_t > STUCK_LIMIT:
			check("player never stuck walking", false, "stuck at %s holding %s" % [at.round(), held])
			stuck_t = -1000.0
	else:
		stuck_t = 0.0 if stuck_t >= 0.0 else stuck_t
	last_pos = at
	# Add game-specific invariants here, e.g.:
	#   dead stays on the last death frame; damage only with an enemy close;
	#   a hit only lands on a target in front; time scale normal outside slow-motion.
	if not checks.has("player never stuck walking"):
		check("player never stuck walking", true)


func _report() -> bool:
	release_all()
	var passes := 0
	var fails := 0
	print("---- bot: %.1f s game time ----" % now())
	for check_name in checks:
		if checks[check_name]:
			passes += 1
			print("PASS  " + check_name)
		else:
			fails += 1
			print("FAIL  " + check_name)
	for failure in failures:
		print("  - " + failure)
	if passes != EXPECTED_CHECKS and fails == 0:
		print("FAIL  expected %d PASS lines, got %d (the bot ended early or a check never ran)" % [EXPECTED_CHECKS, passes])
		fails += 1
	print("RESULT: %d PASS, %d FAIL" % [passes, fails])
	finished = true
	quit(1 if fails > 0 else 0)
	return true
