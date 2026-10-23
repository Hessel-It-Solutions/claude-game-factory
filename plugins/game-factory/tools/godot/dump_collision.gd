extends SceneTree
## Rasterizes the static collisions of a scene into a mask PNG (white = wall) and writes
## <output>.json with the body name and rectangle/polygon of each shape.
##
##   godot --headless --path . -s tools/dump_collision.gd -- <scene.tscn> <output.png> <width> <height>
##
## The same values can come from the environment: COLLISION_SCENE, COLLISION_OUT,
## COLLISION_W, COLLISION_H. Command-line arguments win.
## Covers StaticBody2D with RectangleShape2D / CollisionPolygon2D and TileMapLayer tiles
## with physics polygons. Other shape types are skipped (counted in "skipped").
## Headless is fine here: nothing is rendered, the mask is drawn in an Image.
## Optional game setup (flags, save reset) is left to the caller: this file does not
## reference any autoload or game class.

var frames := 0
var scene: Node
var scene_path := ""
var out_path := ""
var width := 0
var height := 0


func _arg(index: int, env_name: String, fallback := "") -> String:
	var args := OS.get_cmdline_user_args()
	if args.size() > index:
		return args[index]
	var value := OS.get_environment(env_name)
	return value if value != "" else fallback


func _initialize() -> void:
	scene_path = _arg(0, "COLLISION_SCENE")
	out_path = _arg(1, "COLLISION_OUT", "/tmp/collision.png")
	width = int(_arg(2, "COLLISION_W", "1920"))
	height = int(_arg(3, "COLLISION_H", "1080"))
	if scene_path == "":
		push_error("usage: -s dump_collision.gd -- <scene.tscn> <output.png> <width> <height>")
		quit(2)
		return
	var packed = load(scene_path)
	if packed == null:
		push_error("cannot load " + scene_path)
		quit(2)
		return
	scene = packed.instantiate()
	root.add_child(scene)


func _process(_delta: float) -> bool:
	frames += 1
	if scene == null:
		return true
	# Wait a few frames so _ready chains and deferred spawns finish.
	if frames < 5:
		return false
	var img := Image.create(width, height, false, Image.FORMAT_L8)
	var shapes := []
	var skipped := 0
	for body in _collect(scene, "StaticBody2D"):
		for child in body.get_children():
			if child is CollisionShape2D and not child.disabled:
				if child.shape is RectangleShape2D:
					var size: Vector2 = child.shape.size
					var r := Rect2(child.global_position - size / 2.0, size)
					img.fill_rect(Rect2i(r), Color.WHITE)
					shapes.append({"body": String(body.name), "rect": [r.position.x, r.position.y, r.size.x, r.size.y]})
				else:
					skipped += 1
			elif child is CollisionPolygon2D and not child.disabled:
				var poly: PackedVector2Array = child.global_transform * child.polygon
				if poly.size() < 3:
					continue
				_fill_polygon(img, poly)
				shapes.append({"body": String(body.name), "polygon": Array(poly).map(func(p): return [p.x, p.y])})
	for layer in _collect(scene, "TileMapLayer"):
		var tile_set: TileSet = layer.tile_set
		if tile_set == null or tile_set.get_physics_layers_count() == 0:
			continue
		var cell := Vector2(tile_set.tile_size)
		for c in layer.get_used_cells():
			var data: TileData = layer.get_cell_tile_data(c)
			if data == null or data.get_collision_polygons_count(0) == 0:
				continue
			var top_left: Vector2 = layer.to_global(layer.map_to_local(c)) - cell / 2.0
			img.fill_rect(Rect2i(Rect2(top_left, cell)), Color.WHITE)
			shapes.append({"body": String(layer.name), "rect": [top_left.x, top_left.y, cell.x, cell.y]})
	img.save_png(out_path)
	var f := FileAccess.open(out_path.get_basename() + ".json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"shapes": shapes, "skipped": skipped}))
	f.close()
	print("shapes: %d, skipped: %d -> %s" % [shapes.size(), skipped, out_path])
	return true


func _fill_polygon(img: Image, poly: PackedVector2Array) -> void:
	var box := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		box = box.expand(p)
	for y in range(int(box.position.y), int(box.end.y) + 1):
		for x in range(int(box.position.x), int(box.end.x) + 1):
			if x >= 0 and y >= 0 and x < img.get_width() and y < img.get_height() \
					and Geometry2D.is_point_in_polygon(Vector2(x, y), poly):
				img.set_pixel(x, y, Color.WHITE)


func _collect(node: Node, type_name: String) -> Array:
	var out := []
	if node.is_class(type_name):
		out.append(node)
	for child in node.get_children():
		out.append_array(_collect(child, type_name))
	return out
