extends PanelContainer

var extensions_api

@onready var status_label = $MarginContainer/VBoxContainer/StatusLabel
@onready var connect_button = $MarginContainer/VBoxContainer/VBoxContainer2/ConnectButton
@onready var disconnect_button = $MarginContainer/VBoxContainer/VBoxContainer2/DisconnectButton
@onready var websocket_client: WebSocketClient = $WebSocketClient
var uv_overlay: UVOverlay


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	connect_button.pressed.connect(on_connect_button_pressed)
	disconnect_button.pressed.connect(on_disconnect_button_pressed)
	websocket_client.connected_to_server.connect(_on_server_connected)
	websocket_client.connection_closed.connect(_on_server_closed)
	var canvas = extensions_api.general.get_canvas()
	uv_overlay = UVOverlay.new()
	uv_overlay.set_uv_data({
	  "type": "GET_UV_OVERLAY",
	  "data": [
		  [[0.375, 1.0], [0.625, 1.0], [0.625, 0.75], [0.375, 0.75]],
		  [[0.375, 0.75], [0.625, 0.75], [0.625, 0.5], [0.375, 0.5]]
	  ],
	  "noshow": true,
	  "requestId": -1
  	})
	if canvas:
		canvas.previews.add_child(uv_overlay)
		uv_overlay.queue_redraw()


func _on_cel_texture_changed():
	if websocket_client.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return  # Don't do anything if not connected

	if not extensions_api or not extensions_api.project.is_project_open():
		return

	var current_image = extensions_api.project.get_current_cel_image()
	if not current_image:
		return

	var png_buffer = current_image.save_png_to_buffer()
	var base64_string = Marshalls.raw_to_base64(png_buffer)

	var project_name = extensions_api.project.get_project_name()
	if project_name.is_empty():
		project_name = "Untitled"

	var payload = {
		"type": "texture_update",
		"texture_data": base64_string,
		"metadata": {"project_name": project_name}
	}

	var message = JSON.stringify(payload)
	print(message)

	#if websocket_client.get_ready_state() == WebSocketPeer.STATE_OPEN:
		#websocket_client.send(var_to_bytes(message))
		# print("Sent texture update to Blender.") # Optional: can be noisy

func _handle_uv_data(uv_data):
	pass
			
func _on_server_connected():
	status_label.text = "Status: connected"
	
func _on_server_closed():
	status_label.text = "Status: Closed"


func _on_recive_message(msg: String) -> void:
	var message = JSON.parse_string(msg)
	print(message)


func on_connect_button_pressed() -> void:
	websocket_client.connect_to_url("ws://127.0.0.1:8765")


func on_disconnect_button_pressed() -> void:
	websocket_client.close()
