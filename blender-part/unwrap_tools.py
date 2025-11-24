"""
UV unwrap tools adapted from Pixel-Unwrapper.
Provides advanced UV unwrapping functionality with pixel-perfect alignment.
"""

import bpy
import bmesh
from math import radians, floor, ceil
from mathutils import Vector, Matrix
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from itertools import accumulate
from enum import Enum

from .texture_processor import Vector2Int, RectInt


class Direction(Enum):
    """Cardinal directions for grid operations."""
    EAST = 0
    NORTH = 1
    WEST = 2
    SOUTH = 3

    def opposite(self) -> 'Direction':
        if self == Direction.NORTH:
            return Direction.SOUTH
        elif self == Direction.SOUTH:
            return Direction.NORTH
        elif self == Direction.EAST:
            return Direction.WEST
        elif self == Direction.WEST:
            return Direction.EAST

    def vector(self) -> Vector2Int:
        return [
            Vector2Int(1, 0),   # EAST
            Vector2Int(0, 1),   # NORTH
            Vector2Int(-1, 0),  # WEST
            Vector2Int(0, -1),  # SOUTH
        ][self.value]


class UVFace:
    """Represents a face in UV space."""

    def __init__(self, face: 'bmesh.types.BMFace', uv_layer):
        self.face = face
        self.uv_layer = uv_layer
        self.min = Vector((10000000.0, 10000000.0))
        self.max = Vector((-10000000.0, -10000000.0))
        self.center = Vector((0, 0))

    def calc_info(self):
        """Calculate bounding box and center of the face in UV space."""
        ma = Vector((-10000000.0, -10000000.0))
        mi = Vector((10000000.0, 10000000.0))
        center = Vector((0, 0))

        for l in self.face.loops:
            uv = l[self.uv_layer].uv
            ma.x = max(uv.x, ma.x)
            ma.y = max(uv.y, ma.y)
            mi.x = min(uv.x, mi.x)
            mi.y = min(uv.y, mi.y)
            center += uv

        if len(self.face.loops) > 0:
            center /= len(self.face.loops)

        self.min = mi
        self.max = ma


class UVIsland:
    """Represents a UV island (connected group of faces)."""

    def __init__(self, faces: List['bmesh.types.BMFace'], mesh: 'bmesh.types.BMesh', uv_layer):
        self.mesh = mesh
        self.uv_faces = [UVFace(f, uv_layer) for f in faces]
        self.uv_layer = uv_layer
        self.update_min_max()

    def update_min_max(self):
        """Update the min/max values of this island."""
        self.max = Vector((-10000000.0, -10000000.0))
        self.min = Vector((10000000.0, 10000000.0))
        self.average_uv = Vector((0.0, 0.0))
        self.num_uv = 0

        for face in self.uv_faces:
            face.calc_info()

            for l in face.face.loops:
                self.average_uv += l[self.uv_layer].uv
                self.num_uv += 1

            self.max.x = max(face.max.x, self.max.x)
            self.max.y = max(face.max.y, self.max.y)
            self.min.x = min(face.min.x, self.min.x)
            self.min.y = min(face.min.y, self.min.y)

        if self.num_uv > 0:
            self.average_uv /= self.num_uv

    def calc_pixel_bounds(self, texture_size: int, min_padding: float = 0.3) -> RectInt:
        """Calculate integer pixel bounds for this island."""
        xmin = floor(self.min.x * texture_size - min_padding)
        ymin = floor(self.min.y * texture_size - min_padding)
        xmax = ceil(self.max.x * texture_size + min_padding)
        ymax = ceil(self.max.y * texture_size + min_padding)

        mi = Vector2Int(xmin, ymin)
        ma = Vector2Int(xmax, ymax)

        return RectInt(mi, ma)

    def get_faces(self):
        """Get all faces in this island."""
        return (uv_face.face for uv_face in self.uv_faces)


class UnwrapTools:
    """Main class for UV unwrapping operations."""

    @staticmethod
    def get_islands_from_obj(obj, only_selected: bool = True) -> List[UVIsland]:
        """Extract UV islands from an object."""
        if obj.data.is_editmode:
            mesh = bmesh.from_edit_mesh(obj.data)
        else:
            mesh = bmesh.new()
            mesh.from_mesh(obj.data)

        return UnwrapTools.get_islands_from_mesh(mesh, only_selected)

    @staticmethod
    def get_islands_from_mesh(mesh: 'bmesh.types.BMesh', only_selected: bool = True) -> List[UVIsland]:
        """Extract UV islands from a bmesh."""
        if not mesh.loops.layers.uv:
            return []

        uv_layer = mesh.loops.layers.uv.verify()

        if only_selected:
            selected_faces = [f for f in mesh.faces if f.select]
        else:
            selected_faces = [f for f in mesh.faces]

        return UnwrapTools.get_islands_for_faces(mesh, selected_faces, uv_layer)

    @staticmethod
    def get_islands_for_faces(mesh: 'bmesh.types.BMesh', faces: List['bmesh.types.BMFace'], uv_layer) -> List[UVIsland]:
        """Get UV islands for a specific set of faces."""
        # Build lookups for connected components
        mesh.faces.ensure_lookup_table()
        face_to_verts = defaultdict(set)
        vert_to_faces = defaultdict(set)

        for f in faces:
            for l in f.loops:
                id_ = l[uv_layer].uv.to_tuple(5), l.vert.index
                face_to_verts[f.index].add(id_)
                vert_to_faces[id_].add(f.index)

        all_face_indices = face_to_verts.keys()

        def connected_faces(face_idx):
            for vid in face_to_verts[face_idx]:
                for conn_face_idx in vert_to_faces[vid]:
                    yield conn_face_idx

        def get_connected_components(nodes, get_connections_for_node):
            """Get connected components in the graph."""
            remaining = set(nodes)
            connected_components = []

            while remaining:
                node = next(iter(remaining))
                current_component = []
                nodes_to_add = [node]

                while nodes_to_add:
                    node_to_add = nodes_to_add.pop()
                    if node_to_add in remaining:
                        remaining.remove(node_to_add)
                        current_component.append(node_to_add)
                        nodes_to_add.extend(get_connections_for_node(node_to_add))

                connected_components.append(current_component)
            return connected_components

        face_idx_islands = get_connected_components(all_face_indices, connected_faces)
        islands = []

        for face_idx_island in face_idx_islands:
            islands.append(
                UVIsland(
                    [mesh.faces[face_idx] for face_idx in face_idx_island],
                    mesh,
                    uv_layer,
                )
            )

        return islands

    @staticmethod
    def uv_transform(faces, uv_layer, transformation=Matrix.Identity(3)):
        """Transform UV coordinates using the given matrix."""
        for face in faces:
            for loop_uv in face.loops:
                uv = loop_uv[uv_layer].uv
                uv = uv.to_3d()
                uv.z = 1
                transformed = transformation @ uv
                transformed /= transformed.z
                loop_uv[uv_layer].uv = transformed.xy

    @staticmethod
    def uv_snap_to_texel_corner(faces, uv_layer, texture_size: int, skip_pinned: bool = False):
        """Snap UV coordinates to texture pixel corners."""
        for face in faces:
            for loop_uv in face.loops:
                if not (skip_pinned and loop_uv[uv_layer].pin_uv):
                    uv = loop_uv[uv_layer].uv
                    uv.x = round(uv.x * texture_size) / texture_size
                    uv.y = round(uv.y * texture_size) / texture_size

    @staticmethod
    def uv_pin(faces, uv_layer, pin: bool = True):
        """Pin or unpin UV coordinates."""
        for face in faces:
            for loop_uv in face.loops:
                loop_uv[uv_layer].pin_uv = pin

    @staticmethod
    def uv_scale_texel_density(bm, faces, uv_layer, texture_size: int, target_density: float) -> Tuple[float, float]:
        """Scale UVs to match target texel density."""
        # Calculate mesh area
        mesh_face_area = sum(face.calc_area() for face in faces)

        # Calculate UV area using existing function
        def measure_all_faces_uv_area(bm, uv_layer):
            triangle_loops = bm.calc_loop_triangles()
            areas = {face: 0.0 for face in bm.faces}

            for loops in triangle_loops:
                face = loops[0].face
                area = areas[face]
                # Calculate triangle area in 2D
                points = [l[uv_layer].uv for l in loops]
                triangle_area = 0.0
                for i, p1 in enumerate(points):
                    p2 = points[(i + 1) % len(points)]
                    v1 = p1 - points[0]
                    v2 = p2 - points[0]
                    a = v1.x * v2.y - v1.y * v2.x
                    triangle_area += a
                area += abs(0.5 * triangle_area)
                areas[face] = area

            return areas

        uv_face_areas = measure_all_faces_uv_area(bm, uv_layer)
        uv_face_area = sum(uv_face_areas[face] for face in faces)
        uv_face_area *= texture_size * texture_size

        current_density = (uv_face_area ** 0.5) / (mesh_face_area ** 0.5) if mesh_face_area > 0 else 1.0
        scale = target_density / current_density if current_density > 0 else 1.0

        # Apply scaling
        for face in faces:
            for loop_uv in face.loops:
                loop_uv[uv_layer].uv *= scale

        return (current_density, scale)


# Blender operators for unwrap functionality
class UV_OT_unwrap_pixel_perfect(bpy.types.Operator):
    """Unwrap selected faces with pixel-perfect alignment"""
    bl_idname = "uv.unwrap_pixel_perfect"
    bl_label = "Pixel Perfect Unwrap"
    bl_options = {'REGISTER', 'UNDO'}

    target_density: bpy.props.FloatProperty(
        name="Target Density",
        description="Pixels per unit",
        default=32.0,
        min=1.0,
        max=256.0
    )

    snap_to_pixels: bpy.props.BoolProperty(
        name="Snap to Pixels",
        description="Snap UV vertices to pixel corners",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and
                context.active_object and
                context.active_object.type == 'MESH')

    def execute(self, context):
        obj = context.active_object

        # Get texture size
        texture_size = 64  # Default fallback
        from .image_manager import ImageManager
        img_manager = ImageManager()
        if img_manager.IMAGE_NAME:
            image = img_manager.get_image()
            if image:
                texture_size = max(image.size)

        bm = bmesh.from_edit_mesh(obj.data)
        if not bm.loops.layers.uv:
            self.report({'ERROR'}, "No UV layers found")
            return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.verify()
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, "No faces selected")
            return {'CANCELLED'}

        # Standard unwrap first
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, margin=0.01)

        # Scale to target texel density
        current_density, scale = UnwrapTools.uv_scale_texel_density(
            bm, selected_faces, uv_layer, texture_size, self.target_density
        )

        # Snap to pixels if requested
        if self.snap_to_pixels:
            UnwrapTools.uv_snap_to_texel_corner(selected_faces, uv_layer, texture_size)

        # Update mesh
        bmesh.update_edit_mesh(obj.data)

        self.report({'INFO'},
                   f"Unwrapped {len(selected_faces)} faces. "
                   f"Density: {current_density:.1f} → {self.target_density:.1f} PPU")

        return {'FINISHED'}


class UV_OT_unwrap_to_grid(bpy.types.Operator):
    """Unwrap selected faces to a perfect pixel grid"""
    bl_idname = "uv.unwrap_to_grid"
    bl_label = "Unwrap to Grid"
    bl_options = {'REGISTER', 'UNDO'}

    grid_size: bpy.props.IntProperty(
        name="Grid Size",
        description="Size of the grid in pixels",
        default=8,
        min=1,
        max=128
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and
                context.active_object and
                context.active_object.type == 'MESH')

    def execute(self, context):
        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        if not bm.loops.layers.uv:
            self.report({'ERROR'}, "No UV layers found")
            return {'CANCELLED'}

        uv_layer = bm.loops.layers.uv.verify()
        selected_faces = [f for f in bm.faces if f.select]

        if not selected_faces:
            self.report({'ERROR'}, "No faces selected")
            return {'CANCELLED'}

        # Create a simple grid layout
        # This is a simplified version - full implementation would include
        # the complex grid logic from the original Pixel-Unwrapper
        grid_cols = int((len(selected_faces) ** 0.5) + 1)
        grid_rows = (len(selected_faces) + grid_cols - 1) // grid_cols

        uv_step = 1.0 / max(grid_cols, grid_rows)

        for i, face in enumerate(selected_faces):
            col = i % grid_cols
            row = i // grid_cols

            # Create simple UV layout for this face
            u_min = col * uv_step
            v_min = row * uv_step
            u_max = u_min + uv_step * 0.9  # Small padding
            v_max = v_min + uv_step * 0.9

            # Apply UV coordinates based on face vertex count
            if len(face.loops) == 4:  # Quad
                face.loops[0][uv_layer].uv = (u_min, v_min)
                face.loops[1][uv_layer].uv = (u_max, v_min)
                face.loops[2][uv_layer].uv = (u_max, v_max)
                face.loops[3][uv_layer].uv = (u_min, v_max)
            else:  # Triangle or other
                center_u = (u_min + u_max) / 2
                center_v = (v_min + v_max) / 2
                for j, loop in enumerate(face.loops):
                    angle = (j / len(face.loops)) * 2 * 3.14159
                    loop[uv_layer].uv = (
                        center_u + (u_max - u_min) * 0.4 * (angle / 3.14159 - 1),
                        center_v + (v_max - v_min) * 0.4 * (angle % 1)
                    )

        bmesh.update_edit_mesh(obj.data)

        self.report({'INFO'}, f"Unwrapped {len(selected_faces)} faces to {grid_cols}x{grid_rows} grid")

        return {'FINISHED'}


# Registration is now handled by __init__.py
# def register():
#     bpy.utils.register_class(UV_OT_unwrap_pixel_perfect)
#     bpy.utils.register_class(UV_OT_unwrap_to_grid)


# def unregister():
#     bpy.utils.unregister_class(UV_OT_unwrap_pixel_perfect)
#     bpy.utils.unregister_class(UV_OT_unwrap_to_grid)