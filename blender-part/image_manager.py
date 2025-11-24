import os
import queue
import threading
from multiprocessing import Lock

import bpy


class ImageManager:
    INSTANCE = None
    UPDATING_IMAGE = Lock()

    def __init__(self) -> None:
        if not ImageManager.INSTANCE:
            self.IMAGE_NAME = None
            self._update_queue = queue.Queue()
            self._main_thread_id = threading.get_ident()
            ImageManager.INSTANCE = self

    def get_image(self, name=None):
        if name is not None:
            return bpy.data.images[name]
        if not self.IMAGE_NAME:
            return None
        return bpy.data.images[self.IMAGE_NAME]

    def get_image_from_name(self, name):
        return bpy.data.images[name]

    def set_image_name(self, name: str | None):
        self.IMAGE_NAME = name

    def get_image_size(self, name=None):
        image = self.get_image(name)
        if image:
            return image.size
        else:
            return None

    def load_or_create_image(self, image_name, file_path, project_size=None):
        """Thread-safe image update using queue and main thread processing"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"[ImageManager] File not found: {file_path}")
                return None

            # If called from main thread, process directly
            if threading.get_ident() == self._main_thread_id:
                return self._process_image_update(image_name, file_path, project_size)

            # If called from background thread, queue for main thread processing
            update_request = {
                "image_name": image_name,
                "file_path": file_path,
                "project_size": project_size,
                "timestamp": os.path.getmtime(file_path)
                if os.path.exists(file_path)
                else 0,
            }

            self._update_queue.put(update_request)
            print(
                f"[ImageManager] Queued image update for '{image_name}' from background thread"
            )

            # Return existing image if available, or create placeholder
            if image_name in bpy.data.images:
                return bpy.data.images[image_name]
            else:
                # Create a placeholder image that will be updated in main thread
                placeholder = bpy.data.images.new(
                    name=image_name, width=1, height=1, alpha=True
                )
                return placeholder

        except Exception as e:
            print(f"[ImageManager] Error queuing image update '{image_name}': {e}")
            return None

    def _process_image_update(self, image_name, file_path, project_size=None):
        """Process image update in main thread - thread safe"""
        try:
            with ImageManager.UPDATING_IMAGE:
                print(
                    f"[ImageManager] Processing image update for '{image_name}' in main thread"
                )

                # Load image from file to get pixel data
                temp_image = bpy.data.images.load(file_path)

                # Check if target image exists
                if image_name in bpy.data.images:
                    target_image = bpy.data.images[image_name]

                    # Skip special image types
                    if target_image.type in [
                        "RENDER_RESULT",
                        "COMPOSITING",
                        "MULTILAYER",
                    ]:
                        print(
                            f"[ImageManager] Skipping protected image type: {target_image.type}"
                        )
                        bpy.data.images.remove(temp_image)
                        return None

                    # Resize target if needed
                    if target_image.size != temp_image.size:
                        target_image.scale(temp_image.size[0], temp_image.size[1])

                    # Copy pixels (thread safe pixel-level update)
                    target_image.pixels = temp_image.pixels[:]

                else:
                    # Create new image
                    target_image = temp_image
                    target_image.name = image_name

                # Clean up temp image if it's different from target
                if temp_image != target_image:
                    bpy.data.images.remove(temp_image)

                # Pack and set transparency
                target_image.pack()
                if target_image.channels == 4:
                    target_image.alpha_mode = "STRAIGHT"

                # Update display
                target_image.update()
                target_image.update_tag()

                print(
                    f"[ImageManager] Successfully updated '{image_name}' ({target_image.size[0]}x{target_image.size[1]})"
                )
                return target_image

        except Exception as e:
            print(f"[ImageManager] Error processing image update '{image_name}': {e}")
            return None

    def process_pending_updates(self):
        """Process pending image updates - call from main thread timer"""
        if threading.get_ident() != self._main_thread_id:
            print(
                f"[ImageManager] Warning: process_pending_updates called from wrong thread"
            )
            return 0.1

        processed_count = 0
        update_requests = {}

        # Collect all unique requests (latest version for each image)
        try:
            while True:
                request = self._update_queue.get_nowait()
                image_name = request["image_name"]
                # Keep only the latest request for each image
                update_requests[image_name] = request
        except queue.Empty:
            pass

        # Process collected requests
        for image_name, request in update_requests.items():
            try:
                self._process_image_update(
                    request["image_name"], request["file_path"], request["project_size"]
                )
                processed_count += 1
            except Exception as e:
                print(
                    f"[ImageManager] Error processing queued update for '{image_name}': {e}"
                )

        if processed_count > 0:
            print(f"[ImageManager] Processed {processed_count} pending image updates")

        return 0.1  # Return timer interval
