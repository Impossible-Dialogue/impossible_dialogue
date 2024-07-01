import asyncio
import websockets
import json


async def visualization_server(port, topic, orientations, poll_interval=0.1):
    """Starts a websocket server and communicates with visualization."""
    while True:
        
        async def serve(ws):
            """Handler for receiving head_state updates from an active WebSocket connection."""
            while True:
                try:
                    await ws.send(topic)
                    res = await ws.recv()
                    head_state = json.loads(res)
                    for head in head_state["heads"]:
                        orientations[head["id"]] = head["orientation"]
                except Exception as exc:
                    print(f'Websocket Error: {exc}')
                await asyncio.sleep(poll_interval)

        async with websockets.serve(serve, '0.0.0.0', port) as ws:
            await asyncio.Future()

