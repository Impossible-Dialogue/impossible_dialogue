import asyncio
import logging
import copy
import random

from producer.head_mixer import HeadMixer
from producer.output import Output
from core.soundfile import SoundFile

_ALL_CENTERED = "ALL_CENTERED"
_SOME_CENTERED = "SOME_CENTERED"
_NONE_CENTERED = "_NONE_CENTERED"


class Producer:
    def __init__(self, state, config):
        self._state = state
        self._previous_state = copy.deepcopy(state)
        self._config = config
        self._output = Output(state, config["output"])
        self._head_mixers = []
        for i in range(state.num_heads()):
            mixer = HeadMixer(self._output.input_stream(i))
            self._head_mixers.append(mixer)
        self._effects = self._load_segments(config["effects"])
        self._monologue_segments = self._load_segment_lists(
            config["monologue_segments"])
        self._dialogue_segments = self._load_segment_lists(
            config["dialogue_segments"])

    def _load_segment_lists(self, segment_lists):
        segment_list_dict = {}
        for segment_list_config in segment_lists:
            segment_list_id = segment_list_config["id"]
            segment_list_dict[segment_list_id] = self._load_segments(
                segment_list_config["segments"])
        return segment_list_dict

    def _load_segments(self, config):
        segment_dict = {}
        for segment_config in config:
            segment_id = segment_config["id"]
            segment_dict[segment_id] = SoundFile(segment_config)
        return segment_dict

    def heads(self):
        return self._heads

    def play_chime(self):
        for mixer in self._head_mixers:
            mixer.play_effect(self._effects["chime"])

    def mix_dialogue(self):
        return

    def loop(self):
        if self._state.all_heads_centered() and not self._previous_state.all_heads_centered():
            self.play_chime()

        for mixer in self._head_mixers:
            if mixer.is_waiting_for_segments():
                id, segments = random.choice(
                    list(self._dialogue_segments.items()))
                logging.info(f"Playing {id}")
                mixer.play_segments(segments)
            mixer.loop()
        self._previous_state = copy.deepcopy(self._state)

    async def run(self):
        poll_interval = 0.1
        while (True):
            self.loop()
            await asyncio.sleep(poll_interval)
