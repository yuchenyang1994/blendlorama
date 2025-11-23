class_name BlenderSyncDock
extends PanelContainer

# This script manages the UI and logic for the Blender-Pixelorama Sync dock.

var extensions_api
var websocket_client = WebSocketPeer.new()

@onready var status_label = $MarginContainer/VBoxContainer/StatusLabel
@onready var connect_button = $MarginContainer/VBoxContainer/HBoxContainer/ConnectButton
@onready var disconnect_button = $MarginContainer/VBoxContainer/HBoxContainer/DisconnectButton
@onready var get_uv_button = $MarginContainer/VBoxContainer/HBoxContainer/GetUVButton


func _ready():
	# Get the ExtensionsApi singleton
	extensions_api = get_node_or_null("/root/ExtensionsApi")
	if not extensions_api:
		print("Blender Sync: Couldn't find ExtensionsApi.")
		return

	# Connect button signals
	connect_button.pressed.connect(self._on_connect_button_pressed)
	disconnect_button.pressed.connect(self._on_disconnect_button_pressed)
	get_uv_button.pressed.connect(self._on_get_uv_button_pressed)

	# Connect WebSocket signals
	websocket_client.connection_closed.connect(self._on_connection_closed)
	websocket_client.connection_error.connect(self._on_connection_error)
	websocket_client.connection_established.connect(self._on_connection_established)
	websocket_client.data_received.connect(self._on_data_received)

	# Connect Pixelorama signals
	extensions_api.signals.signal_current_cel_texture_changed.connect(self._on_cel_texture_changed)


func _on_connect_button_pressed():
	# Logic to connect to the WebSocket server will go here
	status_label.text = "Status: Connecting..."
	var err = websocket_client.connect_to_url("ws://localhost:8765")
	if err != OK:
		status_label.text = "Status: Error"
		print("Error connecting to Blender.")


func _on_disconnect_button_pressed():
	# Logic to disconnect from the WebSocket server will go here
	websocket_client.close()
	status_label.text = "Status: Disconnected"
	print("Disconnecting from Blender...")


func _on_get_uv_button_pressed():
	if websocket_client.get_ready_state() != WebSocketPeer.STATE_OPEN:
		print("Not connected to Blender.")
		return

	var message = JSON.stringify({"type": "uv_request"})
	websocket_client.get_peer(1).send_text(message)
	print("Requested UV data from Blender.")


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

	var peer = websocket_client.get_peer(1)
	if peer and peer.is_open():
		peer.send_text(message)
		# print("Sent texture update to Blender.") # Optional: can be noisy


func _on_connection_established(protocol):
	status_label.text = "Status: Connected"
	print("Connection established with protocol: ", protocol)


func _on_connection_closed(was_clean_close):
	status_label.text = "Status: Disconnected"
	print("Connection closed. Clean close: ", was_clean_close)


func _on_connection_error():
	status_label.text = "Status: Error"
	print("Connection error.")


func _on_data_received():
	# Logic to handle incoming data from Blender will go here
	var packet = websocket_client.get_peer(1).get_packet()
	var message = packet.get_string_from_utf8()

	var json = JSON.new()
	var error = json.parse(message)
	if error != OK:
		print("Error parsing JSON from server: ", error)
		return

	var data = json.get_data()

	if data.has("type"):
		match data.type:
			"welcome":
				print("Server says: ", data.message)
			"uv_data_response":
				_handle_uv_data(data.data)
			"error":
				print("Server error: ", data.message)
			_:
				print("Received unknown message type: ", data.type)


func _handle_uv_data(uv_data):
	if uv_data.has("error"):
		print("Error receiving UV data: ", uv_data.error)
		return

	print("Received UV data. Generating UV Map...")
	if not uv_data.has("vertices") or not uv_data.has("edges"):
		print("Incomplete UV data received.")
		return

	var texture_size = Vector2i(1024, 1024)
	var uv_image = Image.create(texture_size.x, texture_size.y, false, Image.FORMAT_RGBA8)
	uv_image.fill(Color(0, 0, 0, 0))  # Transparent background

	var line_color = Color.WHITE

	# Create a dictionary to easily look up vertex UVs by their ID
	var vertex_map = {}
	for v in uv_data.vertices:
		vertex_map[v.id] = Vector2(v.u, v.v)

	uv_image.lock()
	for edge in uv_data.edges:
		if vertex_map.has(edge.v1) and vertex_map.has(edge.v2):
			var from_uv = vertex_map[edge.v1]
			var to_uv = vertex_map[edge.v2]

			# Scale UVs to image dimensions (and flip V coordinate)
			var from_point = Vector2i(
				int(from_uv.x * texture_size.x), int((1.0 - from_uv.y) * texture_size.y)
			)
			var to_point = Vector2i(
				int(to_uv.x * texture_size.x), int((1.0 - to_uv.y) * texture_size.y)
			)

			_draw_line(uv_image, from_point, to_point, line_color)

	uv_image.unlock()

	if extensions_api:
		# Create a new project with the UV map as the first cel.
		extensions_api.project.new_project(texture_size, false, uv_image)
		print("Successfully created new project with UV map.")
	else:
		print("ExtensionsApi not available. Cannot create project.")


func _draw_line(image: Image, from: Vector2i, to: Vector2i, color: Color):
	# Basic Bresenham's line algorithm
	var x1 = from.x
	var y1 = from.y
	var x2 = to.x
	var y2 = to.y

	var dx = abs(x2 - x1)
	var dy = abs(y2 - y1)

	var sx = 1 if x1 < x2 else -1
	var sy = 1 if y1 < y2 else -1

	var err = dx - dy

	while true:
		if x1 >= 0 and x1 < image.get_width() and y1 >= 0 and y1 < image.get_height():
			image.set_pixel(x1, y1, color)

		if x1 == x2 and y1 == y2:
			break

		var e2 = 2 * err
		if e2 > -dy:
			err -= dy
			x1 += sx
		if e2 < dx:
			err += dx
			y1 += sy


func _process(_delta):
	if websocket_client.get_ready_state() in [WebSocketPeer.STATE_OPEN]:
		websocket_client.poll()
	elif websocket_client.get_ready_state() == WebSocketPeer.STATE_OPEN:
		websocket_client.poll()
