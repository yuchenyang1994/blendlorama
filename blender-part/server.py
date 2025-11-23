import asyncio
import json
import threading
import traceback

import websockets

connected_clients = set()
server_thread = None
server_loop = None
server_running = False
stop_event = None
websocket_server = None


async def ws_handler(websocket):
    # Add client to connection list
    connected_clients.add(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    print(f"Client {client_info} connected. Total clients: {len(connected_clients)}")

    try:
        # Set up ping/pong heartbeat to keep connection alive
        await websocket.ping()

        async for message in websocket:
            print(f"Received from client {client_info}: {message}")
            try:
                # Parse message to see if it's a specific request
                msg_data = json.loads(message)
                print(f"Parsed message type: {msg_data.get('type', 'unknown')}")

                # Specific message handling logic can be added here
                # For now, keep simple echo
                await websocket.send(json.dumps({"type": "echo", "original": message}))

            except json.JSONDecodeError:
                # If not JSON, echo directly
                await websocket.send(f"Echo: {message}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client {client_info} disconnected - Code: {e.code}, Reason: {e.reason}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(
            f"Client {client_info} connection error - Code: {e.code}, Reason: {e.reason}"
        )
    except Exception as e:
        print(f"Unexpected error with client {client_info}: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
    finally:
        # Remove client from connection list
        connected_clients.discard(websocket)
        print(f"Client {client_info} removed. Total clients: {len(connected_clients)}")


def start_server_async():
    global server_loop, stop_event, websocket_server
    server_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(server_loop)
    stop_event = asyncio.Event()

    async def run_server():
        global websocket_server

        # Configure websocket server parameters for improved connection stability
        websocket_server = await websockets.serve(
            ws_handler,
            "0.0.0.0",
            8765,
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=10,  # Ping timeout 10 seconds
            close_timeout=1,  # Close timeout 1 second
            max_size=10**7,  # Max message size 10MB
            max_queue=32,  # Max queue 32
            compression=None,  # Disable compression for stability
        )
        print("Server started on ws://0.0.0.0:8765 with improved stability settings")

        # Wait for stop signal
        await stop_event.wait()
        print("Server stopping...")

        # Close all client connections
        for client in list(connected_clients):
            try:
                await client.close()
            except:
                pass

        # Close websocket server
        if websocket_server:
            websocket_server.close()
            await websocket_server.wait_closed()
            websocket_server = None

    server_loop.run_until_complete(run_server())


def start_server():
    global server_thread, server_running
    if server_running:
        return
    server_thread = threading.Thread(target=start_server_async, daemon=True)
    server_thread.start()
    server_running = True


def stop_server():
    global server_loop, server_running, stop_event
    if not server_running:
        return
    if server_loop and stop_event:
        # Send stop signal
        server_loop.call_soon_threadsafe(stop_event.set)
        # Wait for thread to end
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=5)
        server_loop = None
        stop_event = None
    server_running = False
    print("Server stopped")


def get_server_status():
    """Get server status information"""
    return {
        "running": server_running,
        "clients_count": len(connected_clients),
        "loop_active": server_loop is not None,
    }


def send_message(msg):
    if server_loop is None:
        print("Server not running - cannot send message")
        return False

    if not connected_clients:
        print("No clients connected - cannot send message")
        return False

    async def _send():
        # Broadcast to all clients
        dead_clients = set()
        message_data = json.dumps(msg)

        for ws in connected_clients:
            try:
                await ws.send(message_data)
                print(f"Message sent to {ws.remote_address[0]}:{ws.remote_address[1]}")
            except websockets.exceptions.ConnectionClosed as e:
                print(
                    f"Client {ws.remote_address[0]}:{ws.remote_address[1]} connection closed during send - Code: {e.code}"
                )
                dead_clients.add(ws)
            except websockets.exceptions.ConnectionClosedError as e:
                print(
                    f"Client {ws.remote_address[0]}:{ws.remote_address[1]} connection error during send - Code: {e.code}"
                )
                dead_clients.add(ws)
            except Exception as e:
                print(
                    f"Error sending to client {ws.remote_address[0]}:{ws.remote_address[1]}: {e}"
                )
                dead_clients.add(ws)

        # Clean up disconnected clients
        for ws in dead_clients:
            connected_clients.discard(ws)
            print(f"Removed dead client {ws.remote_address[0]}:{ws.remote_address[1]}")

        if dead_clients:
            print(
                f"Cleaned up {len(dead_clients)} dead connections. Active clients: {len(connected_clients)}"
            )

    try:
        # Safe call in server thread
        server_loop.call_soon_threadsafe(asyncio.create_task, _send())
        return True
    except Exception as e:
        print(f"Failed to queue message for sending: {e}")
        return False
