import bpy

from .server import get_server_status


class WS_PT_Panel(bpy.types.Panel):
    bl_label = "SyncServer"
    bl_category = "PixeloramaSync"  # 右侧标签栏名字
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
