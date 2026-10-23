extends SceneTree
## Windowed capture of a scene after N frames. Headless does NOT render (no viewport
## texture), so run this in a real window, with a time limit (macOS has no `timeout`):
##
##   perl -e 'alarm 60; exec @ARGV' godot --path . -s tools/capture_scene.gd -- \
##       <scene.tscn> <output.png> [frames=60] [scale=2]
##
## Env alternatives: CAPTURE_SCENE, CAPTURE_OUT, CAPTURE_FRAMES, CAPTURE_SCALE.
## The image is saved at `scale` with nearest filtering (pixel art stays sharp).
##
## Gotcha: with `-s`, the _ready of every autoload runs AFTER _initialize and can reapply
## saved settings (language, volume, ...). So the scene is mounted on the 2nd frame, not in
## _initialize. If you need to set up game state first (reset progress, set a locale, flags),
## copy this file and put that code in `_setup()`, which runs right before mounting.
##
## Do not trust a capture you did not look at: a script can photograph the initial scene
## without building the state you wanted. Open the PNG and check it.

var frames := 0
var scene_path := ""
var out_path := ""
var capture_frame := 60
var scale_factor := 2
var scene: Node
var saving := false


func _arg(index: int, env_name: String, fallback := "") -> String:
	var args := OS.get_cmdline_user_args()
	if args.size() > index:
		return args[index]
	var value := OS.get_environment(env_name)
	return value if value != "" else fallback


func _initialize() -> void:
	scene_path = _arg(0, "CAPTURE_SCENE")
	out_path = _arg(1, "CAPTURE_OUT", "/tmp/capture.png")
	capture_frame = int(_arg(2, "CAPTURE_FRAMES", "60"))
	scale_factor = maxi(1, int(_arg(3, "CAPTURE_SCALE", "2")))
	if scene_path == "":
		push_error("usage: -s capture_scene.gd -- <scene.tscn> <output.png> [frames] [scale]")
		quit(2)


## Override point: runs on frame 2, after the autoloads' _ready, before the scene is mounted.
func _setup() -> void:
	pass


func _process(_delta: float) -> bool:
	if scene_path == "":
		return true
	frames += 1
	if frames == 2:
		_setup()
		var packed = load(scene_path)
		if packed == null:
			push_error("cannot load " + scene_path)
			quit(2)
			return true
		scene = packed.instantiate()
		root.add_child(scene)
	if frames >= capture_frame and not saving:
		saving = true
		_save()
	return false


func _save() -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_viewport().get_texture().get_image()
	if img == null or img.is_empty():
		push_error("empty image: run in a window, not --headless")
		quit(3)
		return
	if scale_factor > 1:
		img.resize(img.get_width() * scale_factor, img.get_height() * scale_factor, Image.INTERPOLATE_NEAREST)
	var err := img.save_png(out_path)
	print("saved %s (%dx%d, err %d)" % [out_path, img.get_width(), img.get_height(), err])
	quit(0 if err == OK else 1)
