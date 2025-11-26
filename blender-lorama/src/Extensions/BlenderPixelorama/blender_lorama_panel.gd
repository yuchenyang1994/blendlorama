extends PanelContainer

var extensions_api

@onready var status_label = $MarginContainer/VBoxContainer/StatusLabel
@onready var connect_button = $MarginContainer/VBoxContainer/HBoxContainer/ConnectButton
@onready var disconnect_button = $MarginContainer/VBoxContainer/HBoxContainer/DisconnectButton
@onready var websocket_client: WebSocketClient = $WebSocketClient
@onready
var uv_overlay_enable_button: CheckButton = $MarginContainer/VBoxContainer/EnableContainer/SwitchUvOverlay
@onready var texture_exporter = $TextureExporter
@onready var image_options: OptionButton = $MarginContainer/VBoxContainer/ImageListContainer/ImageOptions
var current_select_image
var uv_overlay: UVOverlay


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	var canvas = extensions_api.general.get_canvas()
	uv_overlay = UVOverlay.new()
	if canvas:
		canvas.previews.add_child(uv_overlay)
	

	uv_overlay_enable_button.set_pressed_no_signal(true)

	# Connect to texture changed signal instead of using timer
	if extensions_api and extensions_api.signals:
		extensions_api.signals.signal_current_cel_texture_changed(_on_texture_changed)
		extensions_api.signals.signal_project_switched(_on_project_changed)

	connect_button.pressed.connect(on_connect_button_pressed)
	disconnect_button.pressed.connect(on_disconnect_button_pressed)
	websocket_client.connected_to_server.connect(_on_server_connected)
	websocket_client.connection_closed.connect(_on_server_closed)
	websocket_client.connection_failed.connect(_on_connection_failed)
	websocket_client.message_received.connect(_on_recive_message)
	uv_overlay_enable_button.toggled.connect(_on_overlay_toggle)
	image_options.item_selected.connect(_on_blender_image_selected)
	


func _on_server_connected():
	status_label.text = "Blender: connected"
	print("Successfully connected to Blender server")


func _on_server_closed():
	status_label.text = "Blender: Disconnected - Reconnecting..."
	print("Connection to Blender server closed, attempting to reconnect...")


func _on_connection_failed():
	status_label.text = "Blender: Connection Failed"
	print("Failed to connect to Blender server")


func _on_overlay_toggle(toggled_on):
	uv_overlay.set_enabled(toggled_on)
	
func _on_blender_image_selected(index):
	var image_name = image_options.get_item_text(index)
	current_select_image = image_name
	
func _on_project_changed():
	var current_project = extensions_api.project.current_project
	var _index = _get_image_list_index_by_name(current_project.name)
	if _index > -1:
		image_options.select(_index)
	else:
		image_options.select(0)
	


func _on_recive_message(msg: String) -> void:
	var message = JSON.parse_string(msg)
	var type = message["type"]
	print(message)
	match type:
		"GET_UV_OVERLAY":
			_handle_uv_data(message)
		"GET_IMAGES":
			_handle_blender_images(message)
		_:
			pass


func _handle_uv_data(uv_data):
	uv_overlay.clear_uv_overlay()
	uv_overlay.set_uv_data(uv_data)
	
func _handle_blender_images(image_list):
	image_options.clear()
	image_options.add_item("Please select blender image")
	for image in image_list["data"]:
		image_options.add_item(image["name"])


func _on_texture_changed():
	# Handle texture change signal from Pixelorama
	print("Texture changed detected by signal")
	_export_texture_now()


func _export_texture_now():
	# Export texture immediately when signal is received
	var current_project = extensions_api.project.current_project
	var same_image = current_project.name == current_select_image 
	if websocket_client.socket.get_ready_state() == WebSocketPeer.STATE_OPEN and same_image:
		var message = texture_exporter.export(current_project.name)
		if message:
			var msg = JSON.stringify(message)
			var result = websocket_client.send(msg)
			if result != OK:
				print("Failed to send texture message, error code: ", result)


func on_connect_button_pressed() -> void:
	websocket_client.connect_to_url("ws://127.0.0.1:8765")


func on_disconnect_button_pressed() -> void:
	websocket_client.close()
	
func _get_image_list_index_by_name(name: String) -> int:
	for i in range(image_options):
		if image_options.get_item_text(i) == name:
			return i
	return -1 
