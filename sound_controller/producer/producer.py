import asyncio
import logging
import copy
import random

from producer.head_mixer import HeadMixer
from producer.output import Output
from core.soundfile import SoundFile
from core.config import SegmentLists, SegmentList, Segment

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
        self._effects = SegmentList(config["effect_segments"])
        self._monologue_segments = SegmentLists(
            config["monologue_segments"])
        self._dialogue_segments = SegmentLists(
            config["dialogue_segments"])

    def heads(self):
        return self._heads

    def play_chime(self):
        for mixer in self._head_mixers:
            mixer.play_effect(self._effects.find_segment("chime"))

    def mix_dialogue(self):
        return

    def loop(self):
        if self._state.all_heads_centered() and not self._previous_state.all_heads_centered():
            self.play_chime()

        for mixer in self._head_mixers:
            if mixer.is_waiting_for_segments():
                id, segment_list = random.choice(
                    list(self._monologue_segments.lists.items()))
                logging.info(f"Playing {id}")
                mixer.play_segments(segment_list)
            mixer.loop() 
        self._previous_state = copy.deepcopy(self._state)

    async def run(self):
        poll_interval = 0.1
        while (True):
            self.loop()
            await asyncio.sleep(poll_interval)
