"""
Texture processing utilities adapted from Pixel-Unwrapper.
Provides pixel-level texture operations and check functionality.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import bpy
from mathutils import Matrix, Vector


@dataclass(frozen=True)
class Vector2Int:
    """Integer 2D vector for pixel coordinates."""

    x: int
    y: int

    def offset(self, x: int, y: int) -> "Vector2Int":
        return Vector2Int(self.x + x, self.y + y)

    def copy(self) -> "Vector2Int":
        return Vector2Int(self.x, self.y)

    def __getitem__(self, key: int) -> int:
        if key == 0:
            return self.x
        if key == 1:
            return self.y
        raise IndexError(f"{key} is not a valid subscript for Vector2Int")

    def __add__(self, other: "Vector2Int") -> "Vector2Int":
        return Vector2Int(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2Int") -> "Vector2Int":
        return Vector2Int(self.x - other.x, self.y - other.y)

    def __neg__(self) -> "Vector2Int":
        return Vector2Int(-self.x, -self.y)

    def __truediv__(self, other: float) -> Vector:
        return Vector((self.x / other, self.y / other))

    def __mul__(self, other: float) -> Vector:
        return Vector((self.x * other, self.y * other))

    def __rmul__(self, other: float) -> Vector:
        return Vector((other * self.x, other * self.y))

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other: "Vector2Int") -> bool:
        return self.x == other.x and self.y == other.y


@dataclass
class RectInt:
    """Integer rectangle for pixel regions."""

    min: Vector2Int
    max: Vector2Int

    @property
    def size(self) -> Vector2Int:
        return self.max - self.min

    def overlaps(self, other_min: Vector2Int, other_size: Vector2Int) -> bool:
        other_max = other_min + other_size
        return not (
            other_min.x >= self.max.x
            or self.min.x >= other_max.x
            or other_min.y >= self.max.y
            or self.min.y >= other_max.y
        )

    def contains(self, other_min: Vector2Int, other_size: Vector2Int) -> bool:
        other_max = other_min + other_size
        return (
            other_min.x >= self.min.x
            and other_max.x <= self.max.x
            and other_min.y >= self.min.y
            and other_max.y <= self.max.y
        )


class PixelArray:
    """Pixel-level texture manipulation class adapted from Pixel-Unwrapper."""

    def __init__(self, blender_image=None, size: int = None):
        if blender_image is not None:
            self.width = blender_image.size[0]
            self.height = blender_image.size[1]
            self.pixels = list(blender_image.pixels[:])
            assert len(self.pixels) == self.width * self.height * 4, (
                "Pixels array is not the right size"
            )
        elif size is not None:
            # Create a default checkerboard pattern
            self.width = self.height = size
            pixels = list()
            for i in range(size * size):
                row = i // size
                col = i % size
                # Simple checkerboard pattern
                if (row + col) % 2 == 0:
                    col_val = [0.8, 0.8, 0.8, 1.0]  # Light gray
                else:
                    col_val = [0.4, 0.4, 0.4, 1.0]  # Dark gray
                pixels.extend(col_val)
            self.pixels = pixels

    def get_pixel(self, x: int, y: int) -> Tuple[float, float, float, float]:
        """Get pixel RGBA values with wrap mode."""
        x = x % self.width
        y = y % self.height
        idx = (y * self.width + x) * 4
        return tuple(self.pixels[idx : idx + 4])

    def set_pixel(self, x: int, y: int, pix: Tuple[float, float, float, float]) -> None:
        """Set pixel RGBA values with wrap mode."""
        x = x % self.width
        y = y % self.height
        idx = (y * self.width + x) * 4
        assert len(pix) == 4
        self.pixels[idx : idx + 4] = pix

    def copy_region(
        self,
        source: "PixelArray",
        src_pos: Vector2Int,
        size: Vector2Int,
        dst_pos: Vector2Int,
    ) -> None:
        """
        Copy a region of the source texture to this one.
        The source texture uses wrap mode repeat.
        """
        matrix = Matrix.Identity(3)
        offset = dst_pos - src_pos
        src_rect = RectInt(src_pos, src_pos + size)
        matrix[0][2] = offset.x
        matrix[1][2] = offset.y
        self.copy_region_transformed(source, src_rect, matrix)

    def copy_region_transformed(
        self,
        source: "PixelArray",
        src_rect: RectInt,
        transform: Matrix,
    ) -> None:
        """Copy and transform a region from source to this pixel array."""
        original_pixels_len = len(self.pixels)

        # Determine bounds of the destination area
        half = Vector((0.5, 0.5, 0))
        bl = Vector(src_rect.min).to_3d() + half
        bl.z = 1
        tr = Vector(src_rect.max).to_3d() - half
        tr.z = 1
        tl = Vector((bl.x, tr.y)).to_3d()
        tl.z = 1
        br = Vector((tr.x, bl.y)).to_3d()
        br.z = 1

        # Transform source corners to destination corners
        bl = transform @ bl
        tr = transform @ tr
        tl = transform @ tl
        br = transform @ br

        # Find the destination bounds and clamp to image size
        from math import ceil, floor

        dst_min_x = max(0, floor(min(bl.x, br.x, tl.x, tr.x)))
        dst_min_y = max(0, floor(min(bl.y, br.y, tl.y, tr.y)))
        dst_max_x = min(self.width, ceil(max(bl.x, br.x, tl.x, tr.x)))
        dst_max_y = min(self.height, ceil(max(bl.y, br.y, tl.y, tr.y)))

        # Get inverse transform for sampling
        inv_transform = transform.inverted()

        for y in range(dst_min_y, dst_max_y):
            for x in range(dst_min_x, dst_max_x):
                src_point = inv_transform @ Vector((x + 0.5, y + 0.5, 1))
                # Nearest neighbor interpolation
                pix = source.get_pixel(floor(src_point.x), floor(src_point.y))
                self.set_pixel(x, y, pix)

        assert len(self.pixels) == original_pixels_len, (
            f"Pixel Array was resized (from {original_pixels_len} to {len(self.pixels)})"
        )


class TextureProcessor:
    """Main texture processing class with checktexture functionality."""

    @staticmethod
    def check_texture_integrity(image: bpy.types.Image) -> dict:
        """
        Check texture for common issues and return a report.
        """
        if not image:
            return {"status": "error", "message": "No image provided"}

        report = {
            "status": "success",
            "image_name": image.name,
            "size": image.size,
            "channels": image.channels,
            "is_dirty": image.is_dirty,
            "issues": [],
        }

        # Check for common issues
        if image.size[0] == 0 or image.size[1] == 0:
            report["issues"].append("Image has zero dimension")

        if image.channels < 4:
            report["issues"].append("Image doesn't have alpha channel")

        if not image.pixels:
            report["issues"].append("Image has no pixel data")

        # Check for solid transparent areas
        try:
            pixel_array = PixelArray(image)
            transparent_pixels = 0
            total_pixels = pixel_array.width * pixel_array.height

            for y in range(pixel_array.height):
                for x in range(pixel_array.width):
                    _, _, _, a = pixel_array.get_pixel(x, y)
                    if a < 0.01:
                        transparent_pixels += 1

            transparency_ratio = transparent_pixels / total_pixels
            if transparency_ratio > 0.95:
                report["issues"].append(
                    f"Image is almost entirely transparent ({transparency_ratio:.1%})"
                )
            elif transparency_ratio < 0.01:
                report["issues"].append(
                    f"Image has almost no transparency ({transparency_ratio:.1%})"
                )

        except Exception as e:
            report["issues"].append(f"Failed to analyze pixels: {str(e)}")

        return report

    @staticmethod
    def create_checkerboard_texture(
        size: int = 64, name: str = "CheckTexture"
    ) -> bpy.types.Image:
        """
        Create a pixel-perfect checkerboard texture based on Pixel-Unwrapper with real colors.
        """
        # Create the pixel-perfect pattern with Pixel-Unwrapper colors
        pixels = []
        for i in range(size * size):
            row = i // size
            col = i % size
            # 16x16 grid with 4-color pattern like Pixel-Unwrapper
            left = (col % 16) < 8
            top = (row % 16) < 8
            light = (row + col) % 2 == 0

            # Define 4 corner colors with much lower brightness for better UV editor visibility
            col_tl = [0.35, 0.28, 0.2, 1.0]  # Dark orange-brown top-left
            col_tr = [0.2, 0.28, 0.35, 1.0]  # Dark blue-gray top-right
            col_bl = [0.25, 0.32, 0.2, 1.0]  # Dark olive green bottom-left
            col_br = [0.35, 0.2, 0.28, 1.0]  # Dark dusty rose bottom-right

            if left:
                if top:
                    col_val = col_tl
                else:
                    col_val = col_bl
            else:
                if top:
                    col_val = col_tr
                else:
                    col_val = col_br

            # Create subtle variation for pixel-level distinction with minimal contrast
            if not light:
                col_val = [
                    c * 0.85 for c in col_val
                ]  # Further reduced for even lower contrast
                col_val[3] = 1.0  # Keep alpha at 1.0

            pixels.extend(col_val)

        new_texture = bpy.data.images.new(
            name=name,
            width=size,
            height=size,
            alpha=True,
        )

        new_texture.pixels = pixels
        new_texture.update()

        return new_texture

    @staticmethod
    def copy_texture_region(
        texture: bpy.types.Image,
        src_pos: Tuple[int, int],
        size: Tuple[int, int],
        dst_pos: Tuple[int, int],
    ) -> bool:
        """
        Copy a region within the texture.
        Returns True on success, False on failure.
        """
        try:
            src_pixels = PixelArray(blender_image=texture)
            dst_pixels = PixelArray(blender_image=texture)

            src_pos_vec = Vector2Int(src_pos[0], src_pos[1])
            size_vec = Vector2Int(size[0], size[1])
            dst_pos_vec = Vector2Int(dst_pos[0], dst_pos[1])

            dst_pixels.copy_region(src_pixels, src_pos_vec, size_vec, dst_pos_vec)
            texture.pixels = dst_pixels.pixels
            texture.update()

            return True
        except Exception as e:
            print(f"Error copying texture region: {e}")
            return False

    @staticmethod
    def validate_texture_coordinates(
        uv_coords: List[Tuple[float, float]], texture_size: Tuple[int, int]
    ) -> dict:
        """
        Validate UV coordinates against texture dimensions.
        """
        if not uv_coords:
            return {"status": "error", "message": "No UV coordinates provided"}

        issues = []
        tex_width, tex_height = texture_size

        for i, (u, v) in enumerate(uv_coords):
            if u < 0 or u > 1:
                issues.append(f"UV {i}: U coordinate {u} is outside [0, 1] range")
            if v < 0 or v > 1:
                issues.append(f"UV {i}: V coordinate {v} is outside [0, 1] range")

        # Check for UVs that would sample outside texture bounds
        pixel_coords = []
        for u, v in uv_coords:
            px = int(u * tex_width)
            py = int(v * tex_height)
            pixel_coords.append((px, py))

            if px < 0 or px >= tex_width:
                issues.append(
                    f"UV {i}: Pixel X coordinate {px} is outside texture bounds"
                )
            if py < 0 or py >= tex_height:
                issues.append(
                    f"UV {i}: Pixel Y coordinate {py} is outside texture bounds"
                )

        return {
            "status": "success" if not issues else "warning",
            "issues": issues,
            "pixel_coordinates": pixel_coords,
        }


# Blender operator for texture checking
class TEXTURE_OT_check_texture(bpy.types.Operator):
    """Check texture for issues and integrity"""

    bl_idname = "texture.check_texture"
    bl_label = "Check Texture"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # Get active image from image editor or material
        image = None

        # Try to get image from active image editor
        for area in context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                if area.spaces.active.image:
                    image = area.spaces.active.image
                    break

        # If no image in editor, try to get from material
        if (
            not image
            and context.active_object
            and context.active_object.active_material
        ):
            material = context.active_object.active_material
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        image = node.image
                        break

        if not image:
            self.report({"ERROR"}, "No image found to check")
            return {"CANCELLED"}

        # Perform texture check
        report = TextureProcessor.check_texture_integrity(image)

        # Display results
        if report["status"] == "error":
            self.report({"ERROR"}, report.get("message", "Unknown error"))
        else:
            message = f"Texture '{report['image_name']}' ({report['size'][0]}x{report['size'][1]})"
            if report["issues"]:
                message += f" - {len(report['issues'])} issues found"
                for issue in report["issues"]:
                    print(f"Texture Issue: {issue}")
            else:
                message += " - No issues found"

            self.report({"INFO"}, message)

        return {"FINISHED"}


class TEXTURE_OT_create_checker_texture(bpy.types.Operator):
    """Create and apply pixel-perfect checker texture to selected object"""

    bl_idname = "texture.create_checker_texture"
    bl_label = "Create Checker Texture"
    bl_options = {"REGISTER", "UNDO"}

    texture_size: bpy.props.IntProperty(default=64, min=8, max=2048)

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "MESH":
            self.report({"ERROR"}, "Please select a mesh object")
            return {"CANCELLED"}

        # Get texture size from scene property
        texture_size = context.scene.pixel_checker_texture_size

        # Create checker texture
        checker_texture = TextureProcessor.create_checkerboard_texture(
            size=texture_size, name=f"CheckerTexture_{obj.name}"
        )

        # Get or create material
        mat = obj.active_material
        if mat is None:
            mat = bpy.data.materials.new(name=f"Material_{obj.name}")
            obj.data.materials.append(mat)

        # Set up shader nodes
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        # Clear existing nodes (optional, or find existing image node)
        nodes.clear()

        # Create nodes
        output_node = nodes.new("ShaderNodeOutputMaterial")
        bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
        image_node = nodes.new("ShaderNodeTexImage")

        # Set texture
        image_node.image = checker_texture
        image_node.interpolation = "Closest"  # Pixel perfect

        # Connect nodes
        links = mat.node_tree.links
        links.new(image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
        links.new(image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
        links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Layout nodes
        output_node.location = (300, 0)
        bsdf_node.location = (0, 0)
        image_node.location = (-300, 0)

        # Set UV editor to show the new texture
        for area in context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                area.spaces.active.image = checker_texture
                break

        self.report({"INFO"}, f"Created {texture_size}x{texture_size} checker texture")
        return {"FINISHED"}


# Registration is now handled by __init__.py
# def register():
#     bpy.utils.register_class(TEXTURE_OT_check_texture)


# def unregister():
#     bpy.utils.unregister_class(TEXTURE_OT_check_texture)
