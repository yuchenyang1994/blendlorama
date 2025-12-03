bl_info = {
    "name": "Pixelorama Sync",
    "author": "yuchenyang1994",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "category": "Paint",
    "description": "Companion to the Pixelorama Sync plugin. Provides a WebSocket server to sync UVs and textures.",
    "location": "Image Editor > UI Panel > Pixelorama Sync",
}

import bpy

from . import deps

dependency_installed = False
try:
    deps.install_dependencies()
    dependency_installed = deps.are_dependencies_installed()
except Exception as e:
    print(f"Dependency installation failed: {e}")

if dependency_installed:
    from .blender_integration import setup_blender_integration
    from .image_manager import ImageManager
    from .operators import SERVER_OT_start, SERVER_OT_stop, WORLD_OT_setup_grid
    from .server import stop_server
    from .texture_processor import (
        TEXTURE_OT_check_texture,
        TEXTURE_OT_create_checker_texture,
    )
    from .ui import (
        WS_PT_ServerPanel,
        WS_PT_TextureToolsPanel,
        WS_PT_UVToolsPanel,
        WS_PT_WorldGridPanel,
    )
    from .unwrap_tools import UV_OT_unwrap_pixel_perfect, UV_OT_unwrap_to_grid
    from .watch import ImagesStateWatch, UvWatch

    classes = (
        SERVER_OT_start,
        SERVER_OT_stop,
        WORLD_OT_setup_grid,
        WS_PT_ServerPanel,
        WS_PT_UVToolsPanel,
        WS_PT_TextureToolsPanel,
        WS_PT_WorldGridPanel,
        UV_OT_unwrap_pixel_perfect,
        UV_OT_unwrap_to_grid,
        TEXTURE_OT_check_texture,
        TEXTURE_OT_create_checker_texture,
    )
else:
    # 如果依赖缺失，定义一个空的 classes 列表或仅定义一个警告操作符
    classes = ()
    print(
        "Pixelorama Sync: Dependencies missing. Please check console or restart Blender."
    )


def register_scene_properties():
    """Register scene properties"""
    bpy.types.Scene.pixel_checker_texture_size = bpy.props.IntProperty(
        name="Checker Texture Size",
        description="Size of the checker texture to create",
        default=64,
        min=8,
        max=2048,
    )
    bpy.types.Scene.world_grid_subdivisions = bpy.props.IntProperty(
        name="Grid Subdivisions",
        description="Number of subdivisions for the world grid",
        default=16,
        min=1,
        max=64,
        step=1,
    )


def unregister_scene_properties():
    """Unregister scene properties"""
    del bpy.types.Scene.pixel_checker_texture_size
    del bpy.types.Scene.world_grid_subdivisions


def register():
    global dependency_installed

    # 再次检查，防止第一次导入失败但后续手动安装的情况
    if not dependency_installed:
        if deps.are_dependencies_installed():
            # 如果用户在报错后手动修好了，提示重启
            print(
                "Dependencies found. Please restart Blender to load the plugin fully."
            )
            return

    if not dependency_installed:
        print("Pixelorama Sync: Aborting registration due to missing dependencies.")
        return

    # 正常的注册流程
    register_scene_properties()
    setup_blender_integration()
    ImageManager()
    UvWatch()
    ImagesStateWatch()

    # 注册 Timer
    bpy.app.timers.register(
        UvWatch.instance.check_for_changes, first_interval=0.5, persistent=True
    )
    bpy.app.timers.register(
        function=ImagesStateWatch.instance.check_for_changes,
        first_interval=0.5,
        persistent=True,
    )
    bpy.app.timers.register(
        function=ImageManager.INSTANCE.process_pending_updates,
        first_interval=0.1,
        persistent=True,
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global dependency_installed

    if dependency_installed:
        stop_server()
        for cls in reversed(classes):  # 建议反向注销
            bpy.utils.unregister_class(cls)

        if bpy.app.timers.is_registered(UvWatch.instance.check_for_changes):
            bpy.app.timers.unregister(UvWatch.instance.check_for_changes)
        if bpy.app.timers.is_registered(ImagesStateWatch.instance.check_for_changes):
            bpy.app.timers.unregister(ImagesStateWatch.instance.check_for_changes)
        if ImageManager.INSTANCE and hasattr(
            ImageManager.INSTANCE, "process_pending_updates"
        ):
            try:
                bpy.app.timers.unregister(ImageManager.INSTANCE.process_pending_updates)
            except:
                pass

        unregister_scene_properties()


if __name__ == "__main__":
    register()
