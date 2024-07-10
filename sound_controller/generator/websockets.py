import asyncio
import websockets
import json


class SoundControllerWebSocketsServer:
    def __init__(self, producer, host, port):
        self._producer = producer
        self._host = host
        self._port = port

    async def _ws_consumer_handler(self, ws, path):
        while True:
            res = await ws.recv()

    async def _ws_producer_handler(self, ws, path):
        while True:
            await self._producer.event().wait()
            try:
                await ws.send(self._producer.to_json())
            except Exception as exc:
                print(f'Websocket Error: {exc}')
            finally:
                self._producer.event().clear()

    async def _ws_handler(self, ws, path):
        consumer_task = asyncio.create_task(self._ws_consumer_handler(ws, path))
        producer_task = asyncio.create_task(self._ws_producer_handler(ws, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
                
    async def run(self):
        server = await websockets.serve(self._ws_handler, self._host, self._port)
        await server.serve_forever()



