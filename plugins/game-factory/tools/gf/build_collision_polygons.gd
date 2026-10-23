extends SceneTree
## Builds collision polygons from a painted collision mask (opaque = solid).
##
## Usage:
##   godot --headless --path game -s tools/gf/build_collision_polygons.gd -- \
##       res://assets/environments/loc_x/collision_mask.png \
##       res://assets/environments/loc_x/collision_polygons.json [epsilon] [min_area]
##
## epsilon: simplification tolerance in pixels (default 1.5).
## min_area: drops polygons smaller than this area in px^2 (default 0, keep all).
## Output JSON: {"epsilon": e, "size": [w, h], "polygons": [[[x, y], ...], ...]}
##
## Per-level cleanups (trimming a jagged vertex, bevelling a tooth) belong in a
## small project-specific post step, not here: keep the mask itself clean.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		push_error("usage: -- <mask.png> <out.json> [epsilon] [min_area]")
		quit(2)
		return
	var epsilon := float(args[2]) if args.size() > 2 else 1.5
	var minimum_area := float(args[3]) if args.size() > 3 else 0.0
	_generate(args[0], args[1], epsilon, minimum_area)
	quit()

func _generate(mask_path: String, output_path: String, epsilon: float, minimum_area := 0.0) -> void:
	var image := (load(mask_path) as Texture2D).get_image()
	var bitmap := BitMap.new()
	bitmap.create_from_image_alpha(image)
	var polygons: Array = []
	for polygon in bitmap.opaque_to_polygons(Rect2i(Vector2i.ZERO, image.get_size()), epsilon):
		if minimum_area > 0.0 and _area(polygon) < minimum_area:
			continue
		var points: Array = []
		for point in polygon:
			points.append([point.x, point.y])
		polygons.append(points)
	var file := FileAccess.open(output_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"epsilon": epsilon, "size": [image.get_width(), image.get_height()], "polygons": polygons}))

func _area(polygon: PackedVector2Array) -> float:
	var area := 0.0
	for index in polygon.size():
		var next := (index + 1) % polygon.size()
		area += polygon[index].cross(polygon[next])
	return absf(area) * 0.5
