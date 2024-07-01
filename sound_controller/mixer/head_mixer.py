import asyncio
import logging
import random
import time

from channel import Channel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

_INITIALIZING = "INITIALIZE"
_PLAY_SEGMENT = "PLAY_SEGMENT"
_PAUSE = "PAUSE"

_max_pause_length = 5

class HeadMixer:
    def __init__(self, head):
        self._head = head
        self._main_channel = Channel()
        self._effect_channel = Channel()
        self._channel_state = channel.state()
        self.set_state(_INITIALIZING)
        self._pause_end_time = None
        self._segments = []
        self._current_segment_index = -1

    def set_state(self, state):
        logging.info(f"HeadMixer state transitioning from {self._state} to {state}")
        self._state = state

    def pause(self, pause_time):
        self.set_state(_PAUSE)
        self._pause_end_time = time.time() + pause_time

    def play_effect(self, filename):
        if self._effect_channel.is_stopped():
            self._effect_channel.play(filename)

    def play_segments(self, segments):
        self._segments = segments

    def play_segment(self, segment_index):
        segment = self._segments[segment_index]
        self._channel.play(segment.file)
        self.set_state(_PLAY_SEGMENT)
        self._current_segment_index = segment_index

    def play_next_segment(self, segment):
        next_segment = self._current_segment % len(self._segments)
        self.play_segment(next_segment_index)

    def loop(self):
        if self._state == _INITIALIZING:
            self.pause(random.random() * self._max_pause_length)
        elif self._state == _PAUSE:
            if time.time() > self._pause_end_time and len(self._segments) > 0:
                self.play_next_segment()
        elif self._state == _PLAY_SEGMENT:
            if self._channel.is_stopped():
                self.pause(random.random() * self._max_pause_length)





