import asyncio
import logging
import random
import time

from producer.channel_mixer import TwoChannelMixer
from producer.source import Source


_WAITING_FOR_SEGMENTS = "WAITING_FOR_SEGMENTS"
_PLAY_SEGMENT_FROM_LIST = "PLAY_SEGMENT_FROM_LIST"
_PLAY_SEGMENT = "PLAY_SEGMENT"
_PAUSE = "PAUSE"
_STOPPING = "STOPPING"
_STOPPED = "STOPPED"

_max_pause_length = 5

class HeadMixer:
    def __init__(self, head_config, output_stream):
        self._head_config = head_config
        self._output_stream = output_stream
        self._channel_mixer = TwoChannelMixer(output_stream)
        self._main_source = Source(self._channel_mixer.stream1())
        self._effect_source = Source(self._channel_mixer.stream2())
        self._state = _WAITING_FOR_SEGMENTS
        self._pause_end_time = None
        self._segment_list = None
        self._current_segment_index = -1

    def _set_state(self, state):
        logging.info(f"HeadMixer state transitioning from {self._state} to {state}")
        self._state = state

    def head_id(self):
        return self._head_config.id

    def is_waiting_for_segments(self):
        return self._state == _WAITING_FOR_SEGMENTS

    def is_stopped(self):
        return self._state == _STOPPED

    def stop(self):
        self._set_state(_STOPPING)

    def pause(self, pause_time):
        self._set_state(_PAUSE)
        self._pause_end_time = time.time() + pause_time

    def play_effect(self, filename):
        if self._effect_source.is_stopped():
            self._effect_source.play(filename)

    def play_segments(self, segment_list):    
        self._segment_list = segment_list

    def play_segment_from_list(self, segment_index):
        self._current_segment_index = segment_index
        self._main_source.play(self._segment_list.segments[segment_index].filename())
        self._set_state(_PLAY_SEGMENT_FROM_LIST)

    def play_next_segment(self):
        next_segment_index = (
            self._current_segment_index + 1) % self._segment_list.num_segments()
        self.play_segment_from_list(next_segment_index)

    def play_random_segment(self):
        self.play_segment_from_list(random.randrange(self._segment_list.num_segments()))

    def play_segment(self, segment):
        self._main_source.play(segment.filename())
        self._set_state(_PLAY_SEGMENT)


    def loop(self):
        if self._state == _WAITING_FOR_SEGMENTS:
            if self._segment_list:
                self.play_random_segment()
        elif self._state == _PLAY_SEGMENT_FROM_LIST:
            if self._main_source.is_stopped():
                self.pause(random.random() * _max_pause_length)
        elif self._state == _PAUSE:
            if time.time() > self._pause_end_time:
                self.play_random_segment()
        elif self._state == _PLAY_SEGMENT:
            if self._main_source.is_stopped():
                self.stop()
        elif self._state == _STOPPING:
            if self._main_source.is_stopped():
                self._set_state(_STOPPED)
        elif self._state == _STOPPED:
            pass





