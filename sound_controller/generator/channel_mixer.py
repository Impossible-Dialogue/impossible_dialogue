import asyncio
import logging
import numpy as np

from generator.stream import Stream


class TwoChannelMixer:
    def __init__(self, output_stream, channels=2, blocksize=512, dtype='float32'):
        self._stream1 = Stream(
            channels=channels, blocksize=blocksize, dtype=dtype)
        self._stream2 = Stream(
            channels=channels, blocksize=blocksize, dtype=dtype)
        self._volume1 = 1.0
        self._volume2 = 1.0
        self._output_stream = output_stream
        self._task = asyncio.create_task(self.run())

    def stream1(self):
        return self._stream1
    
    def stream2(self):
        return self._stream2

    def set_volume1(self, value):
        self._volume1 = value

    def set_volume2(self, value):
        self._volume2 = value

    async def run(self):
        try:
            while True:
                data1 = await self._stream1.get()
                data2 = await self._stream2.get()
                await self._output_stream.put(data1 * self._volume1 + 
                                              data2 * self._volume2)
        except asyncio.CancelledError:
            logging.info('Received a request to cancel')


class MultiChannelMixer:
    def __init__(self, num_input_streams, output_stream, channels=2, blocksize=512, dtype='float32'):
        self._num_input_streams = num_input_streams
        self._input_streams = [Stream(channels=channels, blocksize=blocksize, dtype=dtype)
                         for i in range(num_input_streams)]
        self._output_stream = output_stream
        self._channels = channels
        self._blocksize = blocksize
        self._dtype = dtype
        self._task = asyncio.create_task(self.run())

    def input_stream(self, index):
        return self._input_streams[index]

    async def run(self):
        try:
            data = np.ndarray(
                (self._num_input_streams, self._blocksize, self._channels), dtype=self._dtype)
            while True:
                for (i, stream) in enumerate(self._input_streams):
                    data[i, :] = await stream.get()
                out = data.sum(axis=0)
                await self._output_stream.put(out)
        except asyncio.CancelledError:
            logging.info('Received a request to cancel')

    
