import asyncio
import base64
from functools import reduce
import json
import numpy as np
from operator import add
import websockets


class LightControllerWebSocketsServer:
    def __init__(self, pattern_generator, host, port):
        self._pattern_generator = pattern_generator
        self._host = host
        self._port = port
        self._TEXTURE_WIDTH = 128
        self._TEXTURE_HEIGHT = 128
        self._TEXTURE_SIZE = self._TEXTURE_WIDTH * self._TEXTURE_HEIGHT * 4

    def _create_texture_message(self, segments):
        out = np.zeros(self._TEXTURE_SIZE, dtype=np.uint8)
        r = np.concatenate([segment.colors[:, 0] for segment in segments], axis=None)
        g = np.concatenate([segment.colors[:, 1] for segment in segments], axis=None)
        b = np.concatenate([segment.colors[:, 2] for segment in segments], axis=None)
        color_bytes = reduce(add, [segment.num_leds for segment in segments]) * 4
        out[:color_bytes:4] = r
        out[1:color_bytes:4] = g
        out[2:color_bytes:4] = b
        return bytearray(out)

    async def _ws_consumer_handler(self, ws, path):
        while True:
            res = await ws.recv()

    async def _ws_producer_handler(self, ws, path):
        while True:
            results = await asyncio.shield(self._pattern_generator.results())
            event = []
            for object_id, result in results.items():
                object_data = {}
                object_data['object_id'] = object_id
                texture_bytes = self._create_texture_message(result.led_segments)
                encoded_data = base64.b64encode(texture_bytes)
                object_data['texture_data'] = encoded_data.decode("utf-8")
                event.append(object_data)
            try:
                await ws.send(json.dumps(event))
            except Exception as exc:
                print(f'Websocket Error: {exc}')
                break

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
