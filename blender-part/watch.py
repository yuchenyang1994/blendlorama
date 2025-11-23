from time import time

import bpy

from .image_manager import ImageManager
from .server import get_server_status, send_message
from .uv_extractor import get_fast_hash, getUvOverlay


class UvWatch:
    last_hash = None
    instance = None

    def __init__(self) -> None:
        UvWatch.instance = self

    def check_for_changes(self):
        interval = 0.5
        t = time()
        try:
            ImageManager.UPDATING_IMAGE.acquire()
            print(
                f"hello, perfcheck{time() - t}",
            )
            new_hash = get_fast_hash()
            print(f"hello, perfcheck{time() - t}")
            print("hashing func", new_hash, self.last_hash)
            # 获取服务器状态
            status = get_server_status()
            print(new_hash, self.last_hash)
            print(new_hash != self.last_hash)
            if (
                new_hash != self.last_hash
                and status["running"]
                and status["clients_count"] > 0
            ):
                dd = getUvOverlay()
                print("uv data changed, sending overlay")
                send_message(
                    {
                        "type": "GET_UV_OVERLAY",
                        "data": dd,
                        "noshow": True,
                        "requestId": -1,
                    }
                )
            self.last_hash = new_hash
        finally:
            ImageManager.UPDATING_IMAGE.release()
            print(interval)
            return interval


class ImagesStateWatch:
    instance = None
    last_hash = None

    def __init__(self) -> None:
        ImagesStateWatch.instance = self

    def check_for_changes(self):
        data = set()
        for image in bpy.data.images:
            data.add(
                frozenset(
                    {
                        image.name,
                        bpy.path.abspath(image.filepath),
                        image.size[0],
                        image.size[1],
                        ImageManager.INSTANCE.IMAGE_NAME == image.name,
                    }
                )
            )

        new_hash = hash(frozenset(data))

        # 获取服务器状态
        status = get_server_status()
        if (
            new_hash != self.last_hash
            and status["running"]
            and status["clients_count"] > 0
        ):
            data = []
            for image in bpy.data.images:
                data.append(
                    {
                        "name": image.name,
                        "path": bpy.path.abspath(image.filepath),
                        "size": [image.size[0], image.size[1]],
                    }
                )
            self.last_hash = new_hash
            send_message(
                {
                    "type": "GET_IMAGES",
                    "data": data,
                    "requestId": -1,
                }
            )
        return 0.5
