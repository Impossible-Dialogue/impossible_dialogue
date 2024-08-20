import asyncio
import logging
import random
import time

from generator.channel_mixer import TwoChannelMixer
from generator.source import Source


_WAITING_FOR_SEGMENTS = "WAITING_FOR_SEGMENTS"
_PLAY_SEGMENT_FROM_LIST = "PLAY_SEGMENT_FROM_LIST"
_PLAY_SEGMENT = "PLAY_SEGMENT"
_PAUSE = "PAUSE"
_STOPPING = "STOPPING"
_STOPPED = "STOPPED"

_max_pause_length = 5

class HeadSoundGenerator:
    def __init__(self, head_config, output_stream):
        if not output_stream: 
            logging.error("output_stream invalid")
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

    def _get_next_index(self, segment_list, current_index):
        next_segment_index = current_index
        while True:
            next_segment_index = next_segment_index + 1
            if next_segment_index >= self._segment_list.num_segments():
                return
            if self._segment_list.segments[next_segment_index].head_id() == self.head_id():
                return next_segment_index

    def set_volume_main(self, value):
        logging.debug(f"Setting main volume of {self.head_id()} to {value}")
        self._channel_mixer.set_volume1(value)
    
    def set_volume_effect(self, value):
        logging.debug(f"Setting effect volume of {self.head_id()} to {value}")
        self._channel_mixer.set_volume2(value)

    def to_dict(self):
        data = {}
        data["head_id"] = self.head_id()
        data["state"] = self._state
        data["main_source"] = self._main_source.to_dict()
        data["effect_source"] = self._effect_source.to_dict()
        return data
    
    def head_id(self):
        return self._head_config.id

    def is_waiting_for_segments(self):
        return self._state == _WAITING_FOR_SEGMENTS

    def is_stopped(self):
        return self._state == _STOPPED

    def stop(self):
        if self._state not in [_STOPPING, _STOPPED]:
            self._set_state(_STOPPING)

    def pause(self, pause_time):
        self._set_state(_PAUSE)
        self._pause_end_time = time.time() + pause_time

    def play_effect(self, segment):
        if self._effect_source.is_stopped():
            self._effect_source.play(segment.filename())

    def play_segment_list(self, segment_list, loop_segments=False): 
        logging.info(
            f"Playing {segment_list.id} on {self._head_config.id}")
        self._segment_list = segment_list
        segment_index = self._get_next_index(segment_list, -1)
        if segment_index != None:
            self.play_segment_from_list(segment_index=segment_index, loop_segment=loop_segments)
        else:
            self.stop()

    def play_segment_from_list(self, segment_index, loop_segment=False):
        self._current_segment_index = segment_index
        self._main_source.play(
            self._segment_list.segments[segment_index].filename(), loop=loop_segment)
        self._set_state(_PLAY_SEGMENT_FROM_LIST)

    def play_next_segment(self):
        segment_index = self._get_next_index(self._segment_list, self._current_segment_index)
        if segment_index:
            self.play_segment_from_list(segment_index=segment_index)
        else:
            self.stop()

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
                if self._current_segment_index == self._segment_list.num_segments() - 1:
                    self.stop()
                else:
                    self.pause(random.random() * _max_pause_length)
        elif self._state == _PAUSE:
            if time.time() > self._pause_end_time:
                self.play_next_segment()
        elif self._state == _PLAY_SEGMENT:
            if self._main_source.is_stopped():
                self.stop()
        elif self._state == _STOPPING:
            if self._main_source.is_stopped():
                self._set_state(_STOPPED)
        elif self._state == _STOPPED:
            pass





