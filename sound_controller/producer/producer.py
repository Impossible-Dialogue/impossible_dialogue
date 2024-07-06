import asyncio
import logging
import copy
import random

from producer.head_mixer import HeadMixer
from producer.output import Output
from core.soundfile import SoundFile
from core.config import HeadConfigs, SegmentLists, SegmentList, Segment

_INITIALIZING = "INITIALIZING"
_START_MONOLOGUE = "START_MONOLOGUE"
_PLAY_MONOLOGUE = "PLAY_MONOLOGUE"
_START_DIALOGUE = "START_DIALOGUE"
_PLAY_DIALOGUE = "PLAY_DIALOGUE"

class Producer:
    def __init__(self, state, config):
        self._state = _INITIALIZING
        self._installation_state = state
        self._previous_installation_state = copy.deepcopy(state)
        self._head_configs = HeadConfigs(config["heads"])
        self._output = Output(state, config["output"])
        self._head_mixers = []
        for i, head_config in enumerate(self._head_configs.heads.values()):
            mixer = HeadMixer(head_config, self._output.input_stream(i))
            self._head_mixers.append(mixer)
        self._effects = SegmentList(config["effect_segments"])
        self._monologue_segments = SegmentLists(
            config["monologue_segments"])
        self._dialogue_segments = SegmentLists(
            config["dialogue_segments"])

    def _set_state(self, state):
        logging.info(f"State transitioning from {self._state} to {state}")
        self._state = state

    def heads(self):
        return self._heads

    def play_chime(self):
        for mixer in self._head_mixers:
            mixer.play_effect(self._effects.find_segment("chime"))

    def play_dialogue(self):
        self._set_state(_PLAY_DIALOGUE)

    def play_monologue(self):
        self._set_state(_PLAY_MONOLOGUE)

    def stop_all_heads(self):
        for mixer in self._head_mixers:
            mixer.stop()

    def are_all_heads_stopped(self):
        for mixer in self._head_mixers:
            if not mixer.is_stopped():
                return False
        return True

    def find_head_mixer(self, head_id):
        for mixer in self._head_mixers:
            if mixer.head_id() == head_id:
                return mixer

    def play_next_dialogue_segment(self):
        self._current_dialogue_index = (self._current_dialogue_index + 1) % self._current_dialogue.num_segments()
        self._current_dialogue_segment = self._current_dialogue.segments[self._current_dialogue_index]
        self._current_dialogue_mixer = self.find_head_mixer(self._current_dialogue_segment.head_id())
        self._current_dialogue_mixer.play_segment(self._current_dialogue_segment)

    def play_dialogue(self, segment_list):
        self._current_dialogue = segment_list
        self._current_dialogue_index = -1
        self.play_next_dialogue_segment()

    def play_random_dialogue(self):
        self.play_dialogue(random.choice(list(self._dialogue_segments.lists.values())))

    def loop(self):
        if self._state == _INITIALIZING:
            if self._installation_state.last_update():
                if self._installation_state.all_heads_centered():
                    self.stop_all_heads()
                    self._set_state(_START_DIALOGUE)
                else:
                    self._set_state(_START_MONOLOGUE)
        elif self._state == _START_DIALOGUE:
            if self.are_all_heads_stopped():
                self.play_random_dialogue()
                self._set_state(_PLAY_DIALOGUE)
        elif self._state == _PLAY_DIALOGUE:
            if self._current_dialogue_mixer.is_stopped():
                self.play_next_dialogue_segment()

        for mixer in self._head_mixers:
            mixer.loop() 

        if self._installation_state.all_heads_centered() and not self._previous_installation_state.all_heads_centered():
            self.play_chime()

        self._previous_installation_state = copy.deepcopy(self._installation_state)

    async def run(self):
        poll_interval = 0.1
        while (True):
            self.loop()
            await asyncio.sleep(poll_interval)
