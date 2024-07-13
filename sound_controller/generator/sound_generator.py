import asyncio
import json
import logging
import copy
import random
import time

from generator.head_sound_generator import HeadSoundGenerator
from generator.output import Output
from impossible_dialogue.config import HeadConfigs, SegmentLists, SegmentList, Segment, SoundConfig

# SoundGenerator states
_INITIALIZING = "INITIALIZING"
_START_MONOLOGUE = "START_MONOLOGUE"
_PLAY_MONOLOGUE = "PLAY_MONOLOGUE"
_START_DIALOGUE = "START_DIALOGUE"
_PLAY_DIALOGUE = "PLAY_DIALOGUE"
_PLAY_MUSIC_CENTERED = "PLAY_MUSIC_CENTERED"
_PLAY_MUSIC_NOT_CENTERED = "PLAY_MUSIC_NOT_CENTERED"

# SoundGenerator states
_SOUND_MODE_SPEECH = "SPEECH"
_SOUND_MODE_MUSIC = "MUSIC"

class SoundGenerator:
    def __init__(self, state, config):
        self._event= asyncio.Event()
        self._state = _INITIALIZING
        self._installation_state = state
        self._sound_config = SoundConfig(config["sound_config"])
        self._head_configs = HeadConfigs(config["heads"])
        self._output = Output(state, self._sound_config.output_config)
        self._head_generators = []
        for i, head_config in enumerate(self._head_configs.heads.values()):
            generator = HeadSoundGenerator(head_config, self._output.input_stream(i))
            self._head_generators.append(generator)
        self._effects = SegmentList(config["effect_segments"])
        self._monologue_segments = SegmentLists(
            config["monologue_segments"], self._head_configs)
        self._dialogue_segments = SegmentLists(
            config["dialogue_segments"], self._head_configs)
        self._music_segments = SegmentLists(
            config["music_segments"], self._head_configs)

        random.seed(time.time())

    def _set_state(self, state):
        logging.info(f"State transitioning from {self._state} to {state}")
        self._state = state

    def to_dict(self):
        data = {}
        data["state"] = self._state
        data["head_generators"] = [generator.to_dict() for generator in self._head_generators]
        return data

    def to_json(self):
        return json.dumps(self.to_dict())

    def event(self):
        return self._event

    def heads(self):
        return self._heads

    def play_chime(self):
        for generator in self._head_generators:
            generator.play_effect(self._effects.find_segment("chime"))

    def stop_all_heads(self):
        for generator in self._head_generators:
            generator.stop()

    def are_all_heads_stopped(self):
        for generator in self._head_generators:
            if not generator.is_stopped():
                return False
        return True

    def find_head_generator(self, head_id):
        for generator in self._head_generators:
            if generator.head_id() == head_id:
                return generator

    def play_next_dialogue_segment(self):
        self._current_dialogue_index = (self._current_dialogue_index + 1) % self._current_dialogue.num_segments()
        self._current_dialogue_segment = self._current_dialogue.segments[self._current_dialogue_index]
        self._current_dialogue_generator = self.find_head_generator(self._current_dialogue_segment.head_id())
        self._current_dialogue_generator.play_segment(self._current_dialogue_segment)

    def play_dialogue(self, segment_list):
        self._current_dialogue = segment_list
        self._current_dialogue_index = -1
        self.play_next_dialogue_segment()

    def play_random_dialogue(self):
        self.play_dialogue(random.choice(list(self._dialogue_segments.lists.values())))

    def play_random_monologue(self, generator):
        segments_lists = list(filter(lambda x: x.head_id == generator.head_id(), 
                                     self._monologue_segments.lists.values()))
        segment_list = random.choice(segments_lists)
        generator.play_segment_list(segment_list)

    def play_random_monologues(self):
        for generator in self._head_generators:
            head_id = generator.head_id()
            head_state = self._installation_state.head_state(head_id)
            if not head_state.is_centered():
                self.play_random_monologue(generator)

    def play_random_music_list(self):
        for generator in self._head_generators:
            head_id = generator.head_id()
            head_state = self._installation_state.head_state(head_id)
            segments_lists = list(filter(lambda x: x.head_id == generator.head_id(), 
                                         self._music_segments.lists.values()))
            segment_list = random.choice(segments_lists)
            generator.play_segment_list(
                segment_list, loop_segments=self._sound_config.music_config.loop_segments)

    def set_volume_main(self, value):
        for generator in self._head_generators:
            generator.set_volume_main(value)

    def set_volume_effect(self, value):
        for generator in self._head_generators:
            generator.set_volume_effect(value)

    def run_speech_mode(self):
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
                self.set_volume_main(
                    self._sound_config.speech_config.dialogue_volume)
                self.play_random_dialogue()
                self._set_state(_PLAY_DIALOGUE)
        elif self._state == _PLAY_DIALOGUE:
            if not self._installation_state.all_heads_centered():
                self.stop_all_heads()
                self._set_state(_START_MONOLOGUE)
            else:
                if self._current_dialogue_generator.is_stopped():
                    self.play_next_dialogue_segment()
        elif self._state == _START_MONOLOGUE:
            if self.are_all_heads_stopped():
                self.set_volume_main(
                    self._sound_config.speech_config.monologue_volume)
                self.play_random_monologues()
                self._set_state(_PLAY_MONOLOGUE)
        elif self._state == _PLAY_MONOLOGUE:
            if self._installation_state.all_heads_centered():
                self.stop_all_heads()
                self.play_chime()
                self._set_state(_START_DIALOGUE)
            else:
                for generator in self._head_generators:
                    head_id = generator.head_id()
                    head_state = self._installation_state.head_state(head_id)
                    if head_state.is_centered():
                         if not generator.is_stopped():
                            generator.stop()
                    else:
                        if generator.is_stopped():
                            self.play_random_monologue(generator)
    
    def run_music_mode(self):
        if self._state == _INITIALIZING:
            if self._installation_state.last_update():
                if self._installation_state.all_heads_centered():
                    self.stop_all_heads()
                    self.play_random_music_list()
                    self._set_state(_PLAY_MUSIC_CENTERED)
                else:
                    self.stop_all_heads()
                    self.play_random_music_list()
                    self._set_state(_PLAY_MUSIC_NOT_CENTERED)
        elif self._state == _PLAY_MUSIC_CENTERED:
            if not self._installation_state.all_heads_centered():
                self.set_volume_main(
                    self._sound_config.music_config.not_centered_volume)
                self._set_state(_PLAY_MUSIC_NOT_CENTERED)
        elif self._state == _PLAY_MUSIC_NOT_CENTERED:
            if self._installation_state.all_heads_centered():
                self.set_volume_main(
                    self._sound_config.music_config.centered_volume)
                self._set_state(_PLAY_MUSIC_CENTERED)

    def loop(self):
        if self._sound_config.mode == _SOUND_MODE_SPEECH:
            self.run_speech_mode()
        elif self._sound_config.mode == _SOUND_MODE_MUSIC:
            self.run_music_mode()

        for generator in self._head_generators:
            generator.loop() 

        self._event.set()

    async def run(self):
        poll_interval = 0.1
        while (True):
            self.loop()
            await asyncio.sleep(poll_interval)
