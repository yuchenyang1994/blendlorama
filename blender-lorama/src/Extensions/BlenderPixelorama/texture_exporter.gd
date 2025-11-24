class_name TextureExporter
extends Node

var extensions_api
var export_temp_dir: String
var export_temp_dir_relative: String


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


func export(image_name):
	if not extensions_api:
		return

	var project = extensions_api.project.current_project
	var current_frame = project.frames[project.current_frame]

	# Directly export blended image (no hash checking needed with signal-based approach)
	var blended_image = _create_blended_image(project, current_frame)
	var export_path = export_temp_dir.path_join("%s_current_frame.png" %image_name)

	if blended_image.save_png(export_path) == OK:
		var sync_info = {
			"type": "SYNC_TEXTURE",
			"image": image_name,
			"project_size": project.size,
			"file_path": ProjectSettings.globalize_path(export_path)
		}
		print("Texture exported successfully: ", image_name)
		return sync_info
	else:
		print("Failed to export texture: ", image_name)
	return null


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


# Hash functions removed - using signal-based approach instead
