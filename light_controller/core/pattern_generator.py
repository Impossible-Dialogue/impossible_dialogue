import asyncio
import copy
import json
import logging
import time

from core.head_pattern_generator import HeadPatternGenerator
from impossible_dialogue.config import HeadConfigs, LightConfig

_INITIALIZING = "INITIALIZING"
_CENTERED = "CENTERED"
_NOT_CENTERED = "NOT_CENTERED"

class PatternGenerator:

    class Results:
        def __init__(self, head_id, led_segments):
            self.head_id = head_id
            self.led_segments = led_segments

    def __init__(self, state, config, args):
        self._state = _INITIALIZING
        self._installation_state = state
        self._args = args
        self._results = asyncio.Future()
        self._head_configs = HeadConfigs(config["heads"])
        self._light_config = LightConfig(config["light_config"])
        self._generation_time_delta = 1.0 / args.animation_rate
        self._cur_generation_time = time.time()
        self._next_generation_time = self._cur_generation_time + self._generation_time_delta
        self._prev_log_time = self._cur_generation_time
        self._log_counter = 0

        self._head_generators = []
        for i, head_config in enumerate(self._head_configs.heads.values()):
            generator = HeadPatternGenerator(head_config, args)
            self._head_generators.append(generator)

        self._LOG_RATE = 1.0

    def _set_state(self, state):
        logging.info(f"State transitioning from {self._state} to {state}")
        self._state = state

    async def generate_patterns(self):
        results = {}
        for generator in self._head_generators:
            head_id = generator.head_id()
            segments = await generator.loop(self._generation_time_delta) 
            results[head_id] = self.Results(head_id, segments)

        # Update results future for processing by IO
        self._results.set_result(results)
        self._results = asyncio.Future()


    def results(self):
        return self._results

    def results(self):
        return self._results

    def update_head_patterns(self):
        for generator in self._head_generators:
            head_id = generator.head_id()
            head_state = self._installation_state.head_state(head_id)
            if self._installation_state.all_heads_centered():
                light_mode_config = self._light_config.all_centered
            elif head_state.is_centered():
                light_mode_config = self._light_config.centered
            else:
                light_mode_config = self._light_config.not_centered
            pattern_config = light_mode_config.patterns[head_id]
            generator.set_pattern_id(pattern_config.pattern_id)
            generator.set_effect_pattern_ids(pattern_config.effect_pattern_ids)
            generator.set_replace_pattern_ids(pattern_config.replace_pattern_ids)
            generator.set_brightness_pattern_ids(pattern_config.brightness_pattern_ids)


    def update_state(self):
        if self._state == _INITIALIZING:
            if self._installation_state.last_update():
                if self._installation_state.all_heads_centered():
                    self._set_state(_CENTERED)
                else:
                    self._set_state(_NOT_CENTERED)
        elif self._state == _CENTERED:
            if not self._installation_state.all_heads_centered():
                self._set_state(_NOT_CENTERED)
                return
            self.update_head_patterns()
        elif self._state == _NOT_CENTERED:
            if self._installation_state.all_heads_centered():
                self._set_state(_CENTERED)
                return
            self.update_head_patterns()


    async def loop(self):
        self._cur_generation_time = self._next_generation_time
        self._next_generation_time = self._cur_generation_time + self._generation_time_delta

        # Skip a frame if falling too far behind
        if time.time() > self._next_generation_time:
            return
        
        # Updates the pattern generation state machine and pattern selection
        self.update_state()

        # The main work happens here
        await self.generate_patterns()

        # Output update rate to console
        self._log_counter += 1
        cur_log_time = time.time()
        log_time_delta = cur_log_time - self._prev_log_time
        if log_time_delta > 1.0 / self._LOG_RATE:
            print("Animation FPS: %.1f" % (self._log_counter / log_time_delta))
            self._log_counter = 0
            self._prev_log_time = cur_log_time

        # Sleep for the remaining time
        await asyncio.sleep(max(0, self._next_generation_time - time.time()))

    async def run(self):
        for generator in self._head_generators:
            await generator.initialize()

        while (True):
            await self.loop()