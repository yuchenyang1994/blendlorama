import bpy


class WS_PT_Panel(bpy.types.Panel):
    bl_label = "PixeloramaSync"
    bl_category = "PixeloramaSync"  # 右侧标签栏名字
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        if layout:
            layout.operator("server.start", text="Start Server")
            layout.operator("server.stop", text="Stop Server")
