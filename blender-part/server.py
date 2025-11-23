import asyncio
import threading

import websockets

connected_clients = set()
server_thread = None
server_loop = None
server_running = False
stop_event = None
websocket_server = None


async def ws_handler(websocket):
    # 添加客户端到连接列表
    connected_clients.add(websocket)
    print(f"Client connected. Total clients: {len(connected_clients)}")

    try:
        async for message in websocket:
            print(f"Received from client: {message}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        # 从连接列表中移除客户端
        connected_clients.discard(websocket)
        print(f"Client removed. Total clients: {len(connected_clients)}")


def start_server_async():
    global server_loop, stop_event, websocket_server
    server_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(server_loop)
    stop_event = asyncio.Event()

    async def run_server():
        global websocket_server
        websocket_server = await websockets.serve(ws_handler, "0.0.0.0", 8765)
        print("Server started on ws://0.0.0.0:8765")

        # 等待停止信号
        await stop_event.wait()
        print("Server stopping...")

        # 关闭websocket服务器
        if websocket_server:
            websocket_server.close()
            await websocket_server.wait_closed()
            websocket_server = None

    server_loop.run_until_complete(run_server())


def start_server():
    global server_thread, server_running
    if server_running:
        return
    server_thread = threading.Thread(target=start_server_async, daemon=True)
    server_thread.start()
    server_running = True


def stop_server():
    global server_loop, server_running, stop_event
    if not server_running:
        return
    if server_loop and stop_event:
        # 发送停止信号
        server_loop.call_soon_threadsafe(stop_event.set)
        # 等待线程结束
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=5)
        server_loop = None
        stop_event = None
    server_running = False
    print("Server stopped")


def get_server_status():
    """获取服务器状态信息"""
    return {
        "running": server_running,
        "clients_count": len(connected_clients),
        "loop_active": server_loop is not None,
    }


def send_message(msg):
    import asyncio
    import json

    if server_loop is None or not connected_clients:
        print("No server or no clients connected")
        return False

    async def _send():
        # 广播给所有客户端
        dead_clients = set()
        for ws in connected_clients:
            try:
                await ws.send(json.dumps(msg))
            except:
                dead_clients.add(ws)
        for ws in dead_clients:
            connected_clients.remove(ws)

    # 在服务器线程安全调用
    server_loop.call_soon_threadsafe(asyncio.create_task, _send())
    return True
