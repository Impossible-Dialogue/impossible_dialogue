import asyncio
import logging
import numpy as np


class Stream:
    def __init__(self, queue_size=10, channels=2, blocksize=512, dtype='float32'):
        self._channels = channels
        self._blocksize = blocksize
        self._dtype = dtype
        self._queue = asyncio.Queue(queue_size)

    def channels(self):
        return self._channels

    def blocksize(self):
        return self._blocksize

    def dtype(self):
        return self._dtype

    async def put(self, item):
        return await self._queue.put(item)

    async def get(self):
        return await self._queue.get()
    
    def get_nowait(self):
        return self._queue.get_nowait()


