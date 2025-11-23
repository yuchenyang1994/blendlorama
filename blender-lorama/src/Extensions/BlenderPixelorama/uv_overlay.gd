class_name UVOverlay
extends Node2D

var extensions_api
var uv_data: Dictionary = {}
var overlay_color := Color.RED * Color(1, 1, 1, 0.7) 
var line_width: float = 1.0
var is_enabled: bool = true
# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	z_index = 100  # 确保在内容之上
	set_process(true)
	 
func _draw() -> void:
	if uv_data.is_empty():
		return
	var faces_data = uv_data.get("data", [])
	if faces_data.is_empty():
		return
	var project = extensions_api.project.current_project
	var canvas_size = project.size
	for face in faces_data:
		if face is Array and face.size() >= 3:
			_draw_uv_face(face, canvas_size)
	
func _draw_uv_face(face: Array, canvas_size: Vector2i) -> void:
	var points = PackedVector2Array()
	for uv_coord in face:
		if uv_coord is Array and uv_coord.size() >= 2:
			var u = float(uv_coord[0])
			var v = float(uv_coord[1])
			u = clamp(u, 0.0, 1.0)
			v = clamp(v, 0.0, 1.0)
			var x = u * canvas_size.x
			var y = v * canvas_size.y
			points.append(Vector2(x, y))
	if points.size() >= 3:
		for i in range(points.size()):
			var current_point = points[i]
			var next_point = points[(i + 1) % points.size()]
			points.append(current_point)
			points.append(next_point)
			if not points.is_empty():
				draw_multiline(points, overlay_color)
		
func set_uv_data(data: Dictionary) -> void:
	uv_data = data
	queue_redraw()
	
func set_overlay_color(color: Color) -> void:
	overlay_color = color
	queue_redraw()
	
func set_line_width(width: float) -> void:
	line_width = width
	queue_redraw()
	
func set_enabled(enabled: bool) -> void:
	is_enabled = enabled
	visible = enabled
	queue_redraw()
	
func clear_uv_overlay() -> void:
	uv_data.clear()
	queue_redraw()
