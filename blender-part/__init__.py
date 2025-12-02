bl_info = {
    "name": "Pixelorama Sync",
    "author": "Heisenshark (Refactored by Assistant)",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "category": "Paint",
    "description": "Companion to the Pixelorama Sync plugin. Provides a WebSocket server to sync UVs and textures.",
    "location": "Image Editor > UI Panel > Pixelorama Sync",
}

from . import deps
deps.install_dependencies()

import bpy
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
    # Register scene properties
    register_scene_properties()

    # Set up Blender-WebSocket integration
    setup_blender_integration()
    ImageManager()
    UvWatch()
    ImagesStateWatch()
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
    stop_server()
    for cls in classes:
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

    # Unregister scene properties
    unregister_scene_properties()


if __name__ == "__main__":
    register()
