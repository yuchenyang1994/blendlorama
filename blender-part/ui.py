import bpy

from .server import get_server_status


class WS_PT_ServerPanel(bpy.types.Panel):
    bl_label = "Sync Server"
    bl_category = "PixeloramaSync"  # Right sidebar tab name
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if layout:
            # Server status section
            box = layout.box()
            box.label(text="SyncServer Status", icon="SETTINGS")

            status = get_server_status()
            if status["running"]:
                status_text = f"Status: Running"
                status_icon = "PLAY"
            else:
                status_text = "Status: Stopped"
                status_icon = "PAUSE"

            box.label(text=status_text, icon=status_icon)
            # Control buttons
            layout.separator()
            layout.operator("server.start", text="Start Server")
            layout.operator("server.stop", text="Stop Server")


class WS_PT_UVToolsPanel(bpy.types.Panel):
    bl_label = "UV Tools"
    bl_category = "PixeloramaSync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if layout:
            box = layout.box()
            box.label(text="UV Unwrapping", icon="GROUP_UVS")

            layout.separator()
            layout.operator("uv.unwrap_pixel_perfect", text="Pixel Perfect Unwrap")
            layout.operator("uv.unwrap_to_grid", text="Unwrap to Grid")

            # Info text
            layout.separator()
            box = layout.box()
            box.label(text="Select faces in Edit Mode", icon="INFO")
            box.label(text="before using UV tools.")


class WS_PT_TextureToolsPanel(bpy.types.Panel):
    bl_label = "Texture Tools"
    bl_category = "PixeloramaSync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if layout:
            box = layout.box()
            box.label(text="Create Checker Texture", icon="IMAGE_DATA")

            # Texture size slider
            row = layout.row()
            row.prop(context.scene, "pixel_checker_texture_size", text="Size")

            # Create button
            layout.operator(
                "texture.create_checker_texture", text="Create & Apply Checker"
            )

            # Info text
            layout.separator()
            box = layout.box()
            box.label(text="Select object to apply texture", icon="INFO")


class WS_PT_WorldGridPanel(bpy.types.Panel):
    bl_label = "World Grid"
    bl_category = "PixeloramaSync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if layout:
            box = layout.box()
            box.label(text="World Grid Settings", icon="GRID")

            # Subdivisions slider
            row = layout.row()
            row.prop(context.scene, "world_grid_subdivisions", text="Subdivisions")

            # Setup button
            layout.operator("world.setup_grid", text="Setup World Grid")

            # Info text
            layout.separator()
            box = layout.box()
            box.label(text="Sets grid scale to 0.0625", icon="INFO")
            box.label(text="and units to NONE")


# Keep the old panel name for backward compatibility
WS_PT_Panel = WS_PT_ServerPanel
