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
        self._pattern_manager = PatternManager(pattern_config.DEFAULT_CONFIG, self._led_config, args)
        self._pattern_mix = PatternMix(self._pattern_manager)
        self._current_pattern_id = head_config.led_pattern_id
        self._current_replace_pattern_ids = []
        self._current_effect_pattern_ids = []

    async def initialize(self):
        await self._pattern_manager.initialize_patterns()
        self._pattern_mix.prepareSegments(self._led_config)
        self._pattern_mix.initialize()

    def head_id(self):
        return self._head_config.id

    async def loop(self, animation_time_delta):
        self._pattern_mix.set_mix(
            base_pattern_ids=[self._current_pattern_id],
            replace_pattern_ids=self._current_replace_pattern_ids,
            mix_pattern_ids=self._current_effect_pattern_ids)
        active_patterns = [self._current_pattern_id] + self._current_replace_pattern_ids + self._current_effect_pattern_ids
        self._pattern_manager.update_pattern_selection(active_patterns)
        await self._pattern_manager.animate(animation_time_delta)
        segments = await self._pattern_mix.update()
        return segments
        