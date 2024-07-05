
import asyncio
import logging
import numpy as np

from tasks.soundfile import read_soundfile

_PLAYING = "PLAYING"
_STOPPED = "STOPPED"


class Source:
    def __init__(self, stream, channels=2, blocksize=512, dtype='float32'):
        self._stream = stream
        self._channels = channels
        self._blocksize = blocksize
        self._dtype = dtype
        self._soundfile_task = None
        self._state = _STOPPED
        self._idle_task = asyncio.create_task(self._idle())

    async def _idle(self):
        try:
            while True:
                block = np.zeros(
                    (self._blocksize, self._channels), dtype=self._dtype)
                await self._stream.put(block)
        except asyncio.CancelledError:
            logging.info('Canceling _idle')

    def _done(self, task):
        result = task.result()
        logging.info(f'result: {result}')
        self.stop()

    def _set_state(self, state):
        logging.info(
            f"Source state transitioning from {self._state} to {state}")
        self._state = state

    def play(self, soundfile):
        logging.info(f"Playing {soundfile.filename()}")
        if self.is_playing():
            self.stop()
        self._idle_task.cancel()
        self._soundfile_task = asyncio.create_task(
            read_soundfile(soundfile.filename(), self._stream))
        self._soundfile_task.add_done_callback(self._done)
        self._set_state(_PLAYING)

    def stop(self):
        if self.is_stopped():
            return
        self._soundfile_task.cancel()
        self._idle_task = asyncio.create_task(self._idle())
        self._set_state(_STOPPED)

    def is_playing(self):
        return self._state == _PLAYING

    def is_stopped(self):
        return self._state == _STOPPED
