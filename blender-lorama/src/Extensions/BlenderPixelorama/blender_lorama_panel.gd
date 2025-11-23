extends PanelContainer

var extensions_api

@onready var status_label = $MarginContainer/VBoxContainer/StatusLabel
@onready var connect_button = $MarginContainer/VBoxContainer/HBoxContainer/ConnectButton
@onready var disconnect_button = $MarginContainer/VBoxContainer/HBoxContainer/DisconnectButton
@onready var websocket_client: WebSocketClient = $WebSocketClient
@onready
var uv_overlay_enable_button: CheckButton = $MarginContainer/VBoxContainer/EnableContainer/SwitchUvOverlay
@onready var texture_exporter = $TextureExporter
var uv_overlay: UVOverlay
var export_tex_timer: Timer


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	var canvas = extensions_api.general.get_canvas()
	uv_overlay = UVOverlay.new()
	if canvas:
		canvas.previews.add_child(uv_overlay)
	export_tex_timer = Timer.new()
	export_tex_timer.wait_time = 0.5
	export_tex_timer.one_shot = false
	export_tex_timer.autostart = true
	add_child(export_tex_timer)
	export_tex_timer.timeout.connect(_on_export_timer_timeout)
	connect_button.pressed.connect(on_connect_button_pressed)
	disconnect_button.pressed.connect(on_disconnect_button_pressed)
	websocket_client.connected_to_server.connect(_on_server_connected)
	websocket_client.connection_closed.connect(_on_server_closed)
	websocket_client.message_received.connect(_on_recive_message)
	uv_overlay_enable_button.toggled.connect(_on_overlay_toggle)


func _on_server_connected():
	status_label.text = "Blender: connected"


func _on_server_closed():
	status_label.text = "Blender: Closed"


func _on_overlay_toggle(toggled_on):
	uv_overlay.set_enabled(toggled_on)


func _on_recive_message(msg: String) -> void:
	var message = JSON.parse_string(msg)
	var type = message["type"]
	print(message)
	match type:
		"GET_UV_OVERLAY":
			_handle_uv_data(message)
		_:
			pass


func _handle_uv_data(uv_data):
	uv_overlay.clear_uv_overlay()
	uv_overlay.set_uv_data(uv_data)


func _on_export_timer_timeout():
	if websocket_client.last_state == WebSocketPeer.STATE_OPEN:
		var message = texture_exporter.export()
		if message:
			websocket_client.send(message)


func on_connect_button_pressed() -> void:
	websocket_client.connect_to_url("ws://127.0.0.1:8765")


func on_disconnect_button_pressed() -> void:
	websocket_client.close()
