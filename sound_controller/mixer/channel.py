
import asyncio
import logging

from tasks.soundfile import read_soundfile

_PLAYING = "PLAYING"
_STOPPING = "STOPPING"
_STOPPED = "STOPPED"

class Channel:
    self._state = _STOPPED
    self._queue = asyncio.Queue()
    self._play_task = None
    self._done_task = None
    self._done_event = asyncio.Event()

    def _set_state(self, state):
        logging.info(
            f"Channel state transitioning from {self._state} to {state}")
        self._state = state

    async def _wait_to_finish(self):
        await self._done_event.wait()
        self._set_state(_STOPPED)

    def play(self, filename):
        self._play_task = asyncio.create_task(read_soundfile(
            filename, self._queue, self._done_event))
        self._done_task = self.asyncio.create_task(
            self._wait_to_finish())
        self._set_state(_PLAYING)
        return self._play_task
    
    def stop(self, filename):
        self._state = _STOPPING
        return self._play_task.cancel()

    def is_playing(self):
        return self._state == _PLAYING

    def is_stopped(self):
        return self._state == _STOPPED


