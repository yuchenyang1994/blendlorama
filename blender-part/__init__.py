bl_info = {
    "name": "Pixelorama Sync",
    "author": "Heisenshark (Refactored by Assistant)",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "category": "Paint",
    "description": "Companion to the Pixelorama Sync plugin. Provides a WebSocket server to sync UVs and textures.",
    "location": "Image Editor > UI Panel > Pixelorama Sync",
}
import bpy

from .blender_integration import setup_blender_integration
from .image_manager import ImageManager
from .operators import SERVER_OT_start, SERVER_OT_stop
from .server import stop_server
from .ui import WS_PT_Panel
from .watch import ImagesStateWatch, UvWatch

classes = (SERVER_OT_start, SERVER_OT_stop, WS_PT_Panel)

from . import deps

deps.install_dependencies()


def register():
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


if __name__ == "__main__":
    register()
