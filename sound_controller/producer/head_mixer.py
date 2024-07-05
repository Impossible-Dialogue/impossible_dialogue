import asyncio
import logging
import random
import time

from producer.channel_mixer import TwoChannelMixer
from producer.source import Source


_WAITING_FOR_SEGMENTS = "WAITING_FOR_SEGMENTS"
_PLAY_SEGMENT = "PLAY_SEGMENT"
_PAUSE = "PAUSE"

_max_pause_length = 5

class HeadMixer:
    def __init__(self, output_stream):
        self._output_stream = output_stream
        self._channel_mixer = TwoChannelMixer(output_stream)
        self._main_source = Source(self._channel_mixer.stream1())
        self._effect_source = Source(self._channel_mixer.stream2())
        self._state = _WAITING_FOR_SEGMENTS
        self._pause_end_time = None
        self._segments = {}
        self._current_segment_index = -1

    def _set_state(self, state):
        logging.info(f"HeadMixer state transitioning from {self._state} to {state}")
        self._state = state

    def is_waiting_for_segments(self):
        return self._state == _WAITING_FOR_SEGMENTS

    def pause(self, pause_time):
        self._set_state(_PAUSE)
        self._pause_end_time = time.time() + pause_time

    def play_effect(self, filename):
        if self._effect_source.is_stopped():
            self._effect_source.play(filename)

    def play_segments(self, segments):    
        self._segments = segments

    def play_segment(self, segment_index):
        self._current_segment_index = segment_index
        segments = list(self._segments.values())
        self._main_source.play(segments[segment_index])
        self._set_state(_PLAY_SEGMENT)

    def play_next_segment(self):
        next_segment_index = (
            self._current_segment_index + 1) % len(self._segments)
        self.play_segment(next_segment_index)

    def play_random_segment(self):
        self.play_segment(random.randrange(len(self._segments)))

    def loop(self):
        if self._state == _WAITING_FOR_SEGMENTS:
            if len(self._segments) > 0:
                self.play_random_segment()
        elif self._state == _PLAY_SEGMENT:
            if self._main_source.is_stopped():
                self.pause(random.random() * _max_pause_length)
        elif self._state == _PAUSE:
            if time.time() > self._pause_end_time:
                self.play_random_segment()





