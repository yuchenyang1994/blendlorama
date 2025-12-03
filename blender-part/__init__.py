bl_info = {
    "name": "Pixelorama Sync",
    "author": "yuchenyang1994",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "category": "Paint",
    "description": "Companion to the Pixelorama Sync plugin. Provides a WebSocket server to sync UVs and textures.",
    "location": "Image Editor > UI Panel > Pixelorama Sync",
}

import sys

import bpy

from . import deps

dependencies_loaded = False

try:
    deps.install_dependencies()

    if deps.are_dependencies_installed():
        dependencies_loaded = True
    else:
        print("Pixelorama Sync: Dependencies failed to install.")

except Exception as e:
    print(f"Pixelorama Sync Error: Dependency check failed: {e}")


if dependencies_loaded:
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
    classes = ()


def register_scene_properties():
    bpy.types.Scene.pixel_checker_texture_size = bpy.props.IntProperty(
        name="Checker Texture Size",
        default=64,
        min=8,
        max=2048,
    )
    bpy.types.Scene.world_grid_subdivisions = bpy.props.IntProperty(
        name="Grid Subdivisions",
        default=16,
        min=1,
        max=64,
    )


def unregister_scene_properties():
    del bpy.types.Scene.pixel_checker_texture_size
    del bpy.types.Scene.world_grid_subdivisions


def register():
    if not dependencies_loaded:
        print(
            "Pixelorama Sync: Dependencies missing. Plugin functionality disabled. Check console."
        )
        return

    register_scene_properties()
    setup_blender_integration()
    ImageManager()
    UvWatch()
    ImagesStateWatch()

    if not bpy.app.timers.is_registered(UvWatch.instance.check_for_changes):
        bpy.app.timers.register(
            UvWatch.instance.check_for_changes, first_interval=0.5, persistent=True
        )

    if not bpy.app.timers.is_registered(ImagesStateWatch.instance.check_for_changes):
        bpy.app.timers.register(
            ImagesStateWatch.instance.check_for_changes,
            first_interval=0.5,
            persistent=True,
        )

    if not bpy.app.timers.is_registered(ImageManager.INSTANCE.process_pending_updates):
        bpy.app.timers.register(
            ImageManager.INSTANCE.process_pending_updates,
            first_interval=0.1,
            persistent=True,
        )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    if not dependencies_loaded:
        return

    stop_server()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    if bpy.app.timers.is_registered(UvWatch.instance.check_for_changes):
        bpy.app.timers.unregister(UvWatch.instance.check_for_changes)
    if bpy.app.timers.is_registered(ImagesStateWatch.instance.check_for_changes):
        bpy.app.timers.unregister(ImagesStateWatch.instance.check_for_changes)

    try:
        if bpy.app.timers.is_registered(ImageManager.INSTANCE.process_pending_updates):
            bpy.app.timers.unregister(ImageManager.INSTANCE.process_pending_updates)
    except:
        pass

    unregister_scene_properties()


if __name__ == "__main__":
    register()
