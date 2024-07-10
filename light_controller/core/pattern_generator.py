import asyncio
import copy
import json
import time

from core.head_pattern_generator import HeadPatternGenerator
from core.config import HeadConfigs

class PatternGenerator:

    class Results:
        def __init__(self, head_id, led_segments):
            self.head_id = head_id
            self.led_segments = led_segments


    def __init__(self, state, head_configs, args):
        self._installation_state = state
        self._previous_installation_state = copy.deepcopy(state)
        self._args = args
        self._results = asyncio.Future()
        self._head_configs = head_configs
        self._animation_time_delta = 1.0 / args.animation_rate
        self._cur_animation_time = time.time()
        self._next_animation_time = self._cur_animation_time + self._animation_time_delta
        self._prev_log_time = self._cur_animation_time
        self._log_counter = 0

        self._head_generators = []
        for i, head_config in enumerate(self._head_configs.heads.values()):
            generator = HeadPatternGenerator(head_config, args)
            self._head_generators.append(generator)

        self._LOG_RATE = 1.0

    def results(self):
        return self._results

    async def loop(self):
        self._cur_animation_time = self._next_animation_time
        self._next_animation_time = self._cur_animation_time + self._animation_time_delta

        # Skip a frame if falling too far behind
        if time.time() > self._next_animation_time:
            return
        
        results = {}
        for generator in self._head_generators:
            head_id = generator.head_id()
            segments = await generator.loop(self._animation_time_delta) 
            results[head_id] = self.Results(head_id, segments)

        # Update results future for processing by IO
        self._results.set_result(results)
        self._results = asyncio.Future()

        # Output update rate to console
        self._log_counter += 1
        cur_log_time = time.time()
        log_time_delta = cur_log_time - self._prev_log_time
        if log_time_delta > 1.0 / self._LOG_RATE:
            print("Animation FPS: %.1f" % (self._log_counter / log_time_delta))
            self._log_counter = 0
            self._prev_log_time = cur_log_time

        # Sleep for the remaining time
        await asyncio.sleep(max(0, self._next_animation_time - time.time()))

    async def run(self):
        for generator in self._head_generators:
            await generator.initialize()

        while (True):
            await self.loop()