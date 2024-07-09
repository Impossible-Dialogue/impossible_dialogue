import asyncio
import json
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
        self._event= asyncio.Event()
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
            config["monologue_segments"], self._head_configs)
        self._dialogue_segments = SegmentLists(
            config["dialogue_segments"], self._head_configs)

    def _set_state(self, state):
        logging.info(f"State transitioning from {self._state} to {state}")
        self._state = state

    def to_dict(self):
        data = {}
        data["state"] = self._state
        data["head_producers"] = [mixer.to_dict() for mixer in self._head_mixers]
        return data

    def to_json(self):
        return json.dumps(self.to_dict())

    def event(self):
        return self._event

    def heads(self):
        return self._heads

    def play_chime(self):
        for mixer in self._head_mixers:
            mixer.play_effect(self._effects.find_segment("chime"))

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

    def play_random_monologue(self, mixer):
        segments_lists = list(filter(lambda x: x.head_id == mixer.head_id(), 
                                     self._monologue_segments.lists.values()))
        segment_list = random.choice(segments_lists)
        mixer.play_segment_list(segment_list)

    def play_random_monologues(self):
        for mixer in self._head_mixers:
            head_id = mixer.head_id()
            head_state = self._installation_state.head_state(head_id)
            if not head_state.is_centered():
                self.play_random_monologue(mixer)

    def loop(self):
        if self._state == _INITIALIZING:
            if self._installation_state.last_update():
                if self._installation_state.all_heads_centered():
                    self.stop_all_heads()
                    self._set_state(_START_DIALOGUE)
                else:
                    self.stop_all_heads()
                    self._set_state(_START_MONOLOGUE)
        elif self._state == _START_DIALOGUE:
            if self.are_all_heads_stopped():
                self.play_random_dialogue()
                self._set_state(_PLAY_DIALOGUE)
        elif self._state == _PLAY_DIALOGUE:
            if not self._installation_state.all_heads_centered():
                self.stop_all_heads()
                self._set_state(_START_MONOLOGUE)
            else:
                if self._current_dialogue_mixer.is_stopped():
                    self.play_next_dialogue_segment()
        elif self._state == _START_MONOLOGUE:
            if self.are_all_heads_stopped():
                self.play_random_monologues()
                self._set_state(_PLAY_MONOLOGUE)
        elif self._state == _PLAY_MONOLOGUE:
            if self._installation_state.all_heads_centered():
                self.stop_all_heads()
                self._set_state(_START_DIALOGUE)
            else:
                for mixer in self._head_mixers:
                    head_id = mixer.head_id()
                    head_state = self._installation_state.head_state(head_id)
                    if head_state.is_centered():
                         if not mixer.is_stopped():
                            mixer.stop()
                    else:
                        if mixer.is_stopped():
                            self.play_random_monologue(mixer)

        for mixer in self._head_mixers:
            mixer.loop() 

        if self._installation_state.all_heads_centered() and not self._previous_installation_state.all_heads_centered():
            self.play_chime()

        self._previous_installation_state = copy.deepcopy(self._installation_state)
        self._event.set()

    async def run(self):
        poll_interval = 0.1
        while (True):
            self.loop()
            await asyncio.sleep(poll_interval)
