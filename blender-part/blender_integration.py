"""Blender integration for WebSocket server events"""

import os

import bpy

from . import server
from .image_manager import ImageManager


def get_images():
    data = []
    for image in bpy.data.images:
        # Skip special image types that shouldn't be accessed via WebSocket
        if image.type in ["RENDER_RESULT", "COMPOSITING", "MULTILAYER"]:
            continue

        data.append(
            {
                "name": image.name,
                "path": bpy.path.abspath(image.filepath) if image.filepath else "",
                "size": [image.size[0], image.size[1]],
                "type": image.type,
                "packed": image.packed_file is not None,
            }
        )
    server.send_message({"type": "GET_IMAGES", "data": data, "requestId": -1})


def on_client_connected(client_info, websocket):
    """Called when a client connects to the WebSocket server"""
    print(f"[Blender] Client connected: {client_info}")


def on_client_disconnected(client_info):
    """Called when a client disconnects from the WebSocket server"""
    print(f"[Blender] Client disconnected: {client_info}")


def on_message_received(client_info, message_data):
    """Called when a message is received from a client"""
    print(
        f"[Blender] Message from {client_info}: {message_data.get('type', 'unknown')}"
    )

    # Example: Handle different message types
    msg_type = message_data.get("type")
    match msg_type:
        case "GET_IMAGES":
            get_images()
        case "SYNC_TEXTURE":
            handle_sync_texture(message_data)
        case _:
            print(f"[Blender] Unknown message type: {msg_type}")


def handle_sync_texture(message_data):
    """Handle SYNC_TEXTURE message - load image from file path and pack it into Blender"""
    try:
        image_name = message_data.get("image")
        file_path = message_data.get("file_path")
        project_size = message_data.get("project_size")

        if not image_name or not file_path:
            print(
                f"[Blender] SYNC_TEXTURE missing required data: image_name={image_name}, file_path={file_path}"
            )
            return

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"[Blender] Image file not found: {file_path}")
            return

        print(f"[Blender] Syncing texture '{image_name}' from {file_path}")

        # Load or create image in Blender using ImageManager
        if ImageManager.INSTANCE:
            blender_image = ImageManager.INSTANCE.load_or_create_image(
                image_name, file_path, project_size
            )

            if blender_image:
                print(f"[Blender] Successfully loaded and packed image '{image_name}'")
                # Send success response
                response = {
                    "type": "SYNC_TEXTURE_RESPONSE",
                    "success": True,
                    "image_name": image_name,
                    "size": list(blender_image.size),
                    "packed": blender_image.packed_file is not None,
                }
                server.send_message(response)
            else:
                print(f"[Blender] Failed to load image '{image_name}'")
                response = {
                    "type": "SYNC_TEXTURE_RESPONSE",
                    "success": False,
                    "image_name": image_name,
                    "error": "Failed to load image",
                }
                server.send_message(response)

    except Exception as e:
        print(f"[Blender] Error in handle_sync_texture: {e}")
        response = {
            "type": "SYNC_TEXTURE_RESPONSE",
            "success": False,
            "image_name": message_data.get("image", "unknown"),
            "error": str(e),
        }
        server.send_message(response)


def setup_blender_integration():
    """Set up the integration between server and Blender"""
    # Register callback functions
    server.set_callbacks(
        on_connected=on_client_connected,
        on_disconnected=on_client_disconnected,
        on_message=on_message_received,
    )
    print("[Blender] WebSocket-Blender integration set up")
