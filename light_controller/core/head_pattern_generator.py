import asyncio
import json
import time

from core.pattern_manager import PatternManager
from core.pattern_mixer import PatternMix
from patterns import pattern_config


class HeadPatternGenerator:
    def __init__(self, head_config, args):
        self._args = args
        self._head_config = head_config
        self._led_config_file = open(head_config.led_config)
        self._led_config = json.load(self._led_config_file)
        self._pattern_manager = PatternManager(self._led_config, args)
        self._pattern_mix = PatternMix(self._pattern_manager)
        self._current_pattern_id = head_config.led_pattern_id
        self._current_replace_pattern_ids = []
        self._current_effect_pattern_ids = []
        self._current_brightness_pattern_ids = []

    async def initialize(self):
        await self._pattern_manager.initialize_patterns()
        self._pattern_mix.prepareSegments(self._led_config)
        self._pattern_mix.initialize()

    def head_id(self):
        return self._head_config.id

    def set_pattern_id(self, value):
        self._current_pattern_id = value
    
    def set_replace_pattern_ids(self, value):
        self._current_replace_pattern_ids = value

    def set_effect_pattern_ids(self, value):
        self._current_effect_pattern_ids = value

    def set_brightness_pattern_ids(self, value):
        self._current_brightness_pattern_ids = value

    async def loop(self, iteration, animation_time_delta):
        self._pattern_mix.set_mix(
            base_pattern_ids=[self._current_pattern_id],
            replace_pattern_ids=self._current_replace_pattern_ids,
            mix_pattern_ids=self._current_effect_pattern_ids,
            brighness_pattern_ids=self._current_brightness_pattern_ids)
        active_patterns = [self._current_pattern_id] + self._current_replace_pattern_ids +  self._current_effect_pattern_ids + self._current_brightness_pattern_ids
        self._pattern_manager.update_pattern_selection(active_patterns)
        await self._pattern_manager.animate(iteration, animation_time_delta)
        segments = await self._pattern_mix.update()
        return segments
        