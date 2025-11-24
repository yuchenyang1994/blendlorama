import os
from multiprocessing import Lock

import bpy


class ImageManager:
    INSTANCE = None
    UPDATING_IMAGE = Lock()

    def __init__(self) -> None:
        if not ImageManager.INSTANCE:
            self.IMAGE_NAME = None
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
        """Replace image content directly"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"[ImageManager] File not found: {file_path}")
                return None

            # Check if image already exists
            if image_name in bpy.data.images:
                target_image = bpy.data.images[image_name]

                # Skip special image types
                if target_image.type in ["RENDER_RESULT", "COMPOSITING", "MULTILAYER"]:
                    print(
                        f"[ImageManager] Skipping protected image type: {target_image.type}"
                    )
                    return None

                print(f"[ImageManager] Replacing entire image object: {image_name}")

                # Save material references
                material_refs = []
                for material in bpy.data.materials:
                    if material.use_nodes:
                        for node in material.node_tree.nodes:
                            if node.type == "TEX_IMAGE" and node.image == target_image:
                                material_refs.append((material, node))

                # Delete old image
                bpy.data.images.remove(target_image)

                # Create new image
                target_image = bpy.data.images.load(file_path)
                target_image.name = image_name

                # Restore material references
                for material, node in material_refs:
                    node.image = target_image

            else:
                # Load new image
                target_image = bpy.data.images.load(file_path)
                target_image.name = image_name
                print(f"[ImageManager] Loaded new image: {image_name}")

            # Pack into blend file
            target_image.pack()

            # Set transparency mode
            if target_image.channels == 4:
                target_image.alpha_mode = "STRAIGHT"

            # Update display
            target_image.update()
            target_image.update_tag()

            print(
                f"[ImageManager] Successfully processed image '{image_name}' ({target_image.size[0]}x{target_image.size[1]})"
            )
            return target_image

        except Exception as e:
            print(f"[ImageManager] Error processing image '{image_name}': {e}")
            return None
