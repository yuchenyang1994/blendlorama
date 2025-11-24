class_name WebSocketClient
extends Node

@export var handshake_headers: PackedStringArray
@export var supported_protocols: PackedStringArray
var tls_options: TLSOptions = null

var socket := WebSocketPeer.new()
var last_state := WebSocketPeer.STATE_CLOSED
var reconnect_timer: Timer
var reconnect_attempts = 0
var max_reconnect_attempts = 5
var reconnect_delay = 2.0  # seconds

signal connected_to_server
signal connection_closed
signal message_received(message: Variant)
signal connection_failed


func _ready():
	_setup_reconnect_timer()


func _setup_reconnect_timer():
	reconnect_timer = Timer.new()
	reconnect_timer.wait_time = reconnect_delay
	reconnect_timer.one_shot = true
	add_child(reconnect_timer)
	reconnect_timer.timeout.connect(_attempt_reconnect)


func connect_to_url(url: String) -> int:
	socket.supported_protocols = supported_protocols
	socket.handshake_headers = handshake_headers

	var err := socket.connect_to_url(url, tls_options)
	if err != OK:
		print("WebSocket connection error: ", err)
		connection_failed.emit()
		_schedule_reconnect()
		return err

	last_state = socket.get_ready_state()
	reconnect_attempts = 0  # Reset reconnect attempts on successful connection start
	return OK


func _schedule_reconnect():
	if reconnect_attempts < max_reconnect_attempts:
		reconnect_attempts += 1
		print("Scheduling reconnect attempt ", reconnect_attempts, "/", max_reconnect_attempts)
		reconnect_timer.start()
	else:
		print("Max reconnect attempts reached. Giving up.")


func _attempt_reconnect():
	if last_state == WebSocketPeer.STATE_CLOSED:
		print("Attempting to reconnect...")
		connect_to_url("ws://127.0.0.1:8765")


func send(message) -> int:
	# Check connection state before sending
	if socket.get_ready_state() != WebSocketPeer.STATE_OPEN:
		print("Cannot send message: WebSocket is not connected")
		return ERR_UNCONFIGURED

	if typeof(message) == TYPE_STRING:
		return socket.send_text(message)
	return socket.send(var_to_bytes(message))


func get_message() -> Variant:
	if socket.get_available_packet_count() < 1:
		return null
	var pkt := socket.get_packet()
	if socket.was_string_packet():
		return pkt.get_string_from_utf8()
	return bytes_to_var(pkt)


func close(code: int = 1000, reason: String = "") -> void:
	socket.close(code, reason)
	last_state = socket.get_ready_state()


func clear() -> void:
	socket = WebSocketPeer.new()
	last_state = socket.get_ready_state()


func get_socket() -> WebSocketPeer:
	return socket


func poll() -> void:
	if socket.get_ready_state() != socket.STATE_CLOSED:
		socket.poll()

	var state := socket.get_ready_state()

	if last_state != state:
		last_state = state
		if state == socket.STATE_OPEN:
			print("WebSocket connected successfully")
			reconnect_attempts = 0  # Reset on successful connection
			connected_to_server.emit()
		elif state == socket.STATE_CLOSED:
			print("WebSocket connection closed")
			connection_closed.emit()
			_schedule_reconnect()  # Schedule reconnect on unexpected closure

	# Process messages only when connection is fully open
	while socket.get_ready_state() == socket.STATE_OPEN and socket.get_available_packet_count():
		message_received.emit(get_message())


func _process(_delta: float) -> void:
	poll()
