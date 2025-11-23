class_name TextureExporter
extends Node

var extensions_api
var export_temp_dir: String
var export_temp_dir_relative: String

var last_project_hash: String = ""


func _ready() -> void:
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	export_temp_dir = "user://tmp/blenderlorama_realtime"
	_ensure_export_directory()
	if extensions_api:
		pass


func _ensure_export_directory():
	var dir = DirAccess.open("user://")
	if dir:
		dir.make_dir_recursive("tmp/blenderlorama_realtime")


func export():
	if not extensions_api:
		return

	var project = extensions_api.project.current_project
	var current_frame = project.frames[project.current_frame]
	var current_hash = _generate_project_hash(project)
	if current_hash == last_project_hash:
		return
	var blended_image = _create_blended_image(project, current_frame)
	var export_path = export_temp_dir.path_join("current_frame.png")
	if blended_image.save_png(export_path) == OK:
		last_project_hash = current_hash
		var sync_info = {
			"type": "SYNC_TEXTURE",
			"project_size": project.size, 
			"file_path": ProjectSettings.globalize_path(export_path)
		}
		return sync_info
	return


func _create_blended_image(project, frame) -> Image:
	var blended_image = project.new_empty_image()

	for i in range(project.layers.size()):
		var layer = project.layers[i]
		if layer.visible:
			if frame.cels.size() > i:
				var cel = frame.cels[i]
				var cel_image = cel.get_image()
				if cel_image:
					_blend_layer_onto_image(blended_image, cel_image, layer)

	return blended_image


func _blend_layer_onto_image(target, source, layer):
	var opacity = layer.opacity
	if opacity == null:
		opacity = 1.0

	for x in range(target.get_width()):
		for y in range(target.get_height()):
			var target_color = target.get_pixel(x, y)
			var source_color = source.get_pixel(x, y)

			if source_color.a > 0:
				var final_alpha = source_color.a * opacity
				var blended_color = target_color.lerp(source_color, final_alpha)
				target.set_pixel(x, y, blended_color)


func _generate_project_hash(project) -> String:
	var hash_string = ""
	hash_string += str(project.current_frame)
	hash_string += str(project.current_layer)
	hash_string += str(project.size.x) + "x" + str(project.size.y)

	# Include information from all visible layers
	for i in range(project.layers.size()):
		var layer = project.layers[i]
		if layer.visible:  # Use the visible property
			hash_string += str(i) + "_"

			# Get the current frame image hash - cels are in Frame, not Layer
			if project.current_frame < project.frames.size():
				var frame = project.frames[project.current_frame]
				if i < frame.cels.size():
					var cel = frame.cels[i]
					var cel_image = cel.get_image()
					if cel_image:
						# Include simple hash of actual pixel data
						hash_string += _generate_simple_image_hash(cel_image)

	return hash_string


# fast hash
func _generate_simple_image_hash(image: Image) -> String:
	var simple_hash = ""
	var width = image.get_width()
	var height = image.get_height()

	# Sample some key pixels to generate hash
	# Sampling strategy: edges, center, corners, etc.
	var sample_points = [
		Vector2i(0, 0),  # Top-left corner
		Vector2i(width - 1, 0),  # Top-right corner
		Vector2i(0, height - 1),  # Bottom-left corner
		Vector2i(width - 1, height - 1),  # Bottom-right corner
		Vector2i(width / 2, height / 2),  # Center
	]

	# Add more sampling points (if size is sufficient)
	if width > 10 && height > 10:
		(
			sample_points
			. append_array(
				[
					Vector2i(width / 4, height / 4),
					Vector2i(3 * width / 4, height / 4),
					Vector2i(width / 4, 3 * height / 4),
					Vector2i(3 * width / 4, 3 * height / 4),
				]
			)
		)

	for point in sample_points:
		if point.x < width && point.y < height:
			var color = image.get_pixel(point.x, point.y)
			simple_hash += str(color.r8) + str(color.g8) + str(color.b8) + str(color.a8)

	# Add non-transparent pixel count
	var non_transparent_count = 0
	for x in range(min(width, 50)):  # Limit check range to improve performance
		for y in range(min(height, 50)):
			var color = image.get_pixel(x, y)
			if color.a > 0:
				non_transparent_count += 1

	simple_hash += str(non_transparent_count)
	return simple_hash
