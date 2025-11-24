import bpy

from . import server


class WORLD_OT_setup_grid(bpy.types.Operator):
    bl_idname = "world.setup_grid"
    bl_label = "Setup World Grid"
    bl_description = "Set up world grid with scale 0.0625 and subdivisions"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # Get subdivisions from scene property
        subdivisions = context.scene.world_grid_subdivisions

        # Set viewport grid
        for space in context.area.spaces:
            if space.type == "VIEW_3D":
                space.overlay.grid_scale = 0.0625
                space.overlay.grid_subdivisions = subdivisions
                break

        # Set scene units to None (metric)
        context.scene.unit_settings.system = "NONE"
        context.scene.unit_settings.scale_length = 0.0625

        self.report(
            {"INFO"}, f"World grid set up: scale=0.0625, subdivisions={subdivisions}"
        )
        return {"FINISHED"}


class SERVER_OT_start(bpy.types.Operator):
    bl_idname = "server.start"
    bl_label = "Start Server"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        server.start_server()
        self.report({"INFO"}, "Server started")
        return {"FINISHED"}


class SERVER_OT_stop(bpy.types.Operator):
    bl_idname = "server.stop"
    bl_label = "Stop Server"

    @classmethod
    def poll(cls, context):
        # Ensure availability in correct context
        return True  # or your condition check

    def execute(self, context):
        self.report({"INFO"}, "Server stopped")
        server.stop_server()
        return {"FINISHED"}
