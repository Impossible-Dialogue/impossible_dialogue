import asyncio
import copy
import json
import logging
import time

from core.head_pattern_generator import HeadPatternGenerator
from impossible_dialogue.config import HeadConfigs, LightConfig, FirePitConfig
from patterns.pattern_config import PATTERNS

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
        self._fire_pit_config = None
        if "fire_pit" in config:
            self._fire_pit_config = FirePitConfig(config["fire_pit"])
        self._fire_pit_generator = None
        self._light_config = LightConfig(config["light_config"])
        self._generation_time_delta = 1.0 / args.animation_rate
        self._cur_generation_time = time.time()
        self._next_generation_time = self._cur_generation_time + self._generation_time_delta
        self._prev_log_time = self._cur_generation_time
        self._prev_rotation_time = time.time()
        self._rotation_index = 0
        self._log_counter = 0
        self._iteration = 0

        self._head_generators = []
        for i, head_config in enumerate(self._head_configs.heads.values()):
            generator = HeadPatternGenerator(head_config, args)
            self._head_generators.append(generator)
        if self._fire_pit_config:
            self._fire_pit_generator = HeadPatternGenerator(self._fire_pit_config, args)

        self._LOG_RATE = 1.0

    def _set_state(self, state):
        logging.info(f"State transitioning from {self._state} to {state}")
        self._state = state

    async def generate_patterns(self):
        results = {}
        for generator in self._head_generators:
            head_id = generator.head_id()
            segments = await generator.loop(self._iteration, self._generation_time_delta) 
            results[head_id] = self.Results(head_id, segments)
        
        if self._fire_pit_config:
            fire_pit_id = self._fire_pit_config.id
            segments = await self._fire_pit_generator.loop(self._iteration, self._generation_time_delta)
            results[fire_pit_id] = self.Results(fire_pit_id, segments)

        # Update results future for processing by IO
        self._results.set_result(results)
        self._results = asyncio.Future()


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
        # Update fire pit
        if self._fire_pit_generator:
            fire_pit_pattern_id = "0x0"
            fire_pit_set_replace_pattern_ids = []
            fire_pit_effect_pattern_ids = []
            fire_pit_brightness_pattern_ids = []
            for generator in self._head_generators:
                head_id = generator.head_id()
                head_state = self._installation_state.head_state(head_id)
                if self._installation_state.all_heads_centered():
                    fire_pit_pattern_id = "1x1"
                elif head_state.is_centered():
                    fire_pit_set_replace_pattern_ids.append(f"{head_id}x5")
                    fire_pit_brightness_pattern_ids.append(f"{head_id}x4")
            self._fire_pit_generator.set_pattern_id(fire_pit_pattern_id)
            self._fire_pit_generator.set_effect_pattern_ids(fire_pit_effect_pattern_ids)
            self._fire_pit_generator.set_replace_pattern_ids(fire_pit_set_replace_pattern_ids)
            self._fire_pit_generator.set_brightness_pattern_ids(fire_pit_brightness_pattern_ids)    


    def update_state(self):
        if self._args.pattern_demo_mode:
            return

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

        if self._args.pattern_demo_mode:
            cur_rotation_time = time.time()
            time_delta = cur_rotation_time - self._prev_rotation_time
            if time_delta > 10.0:
                patterns_ids = list(PATTERNS.keys())
                self._rotation_index = (self._rotation_index + 1) % len(patterns_ids)
                next_pattern_id = patterns_ids[self._rotation_index]
                for generator in self._head_generators:
                    generator.set_pattern_id(next_pattern_id)
                    generator.set_effect_pattern_ids([])
                    generator.set_replace_pattern_ids([])
                    generator.set_brightness_pattern_ids([])
                        
                self._prev_rotation_time = cur_rotation_time

        # Sleep for the remaining time
        await asyncio.sleep(max(0, self._next_generation_time - time.time()))

    async def run(self):
        for generator in self._head_generators:
            await generator.initialize()
        if self._fire_pit_generator:
            await self._fire_pit_generator.initialize()

        while (True):
            await self.loop()
            self._iteration += 1