import bpy

from . import server


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
