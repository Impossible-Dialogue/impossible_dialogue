import numpy as np

from core.pattern_cache import PatternCache
from patterns.pattern_config import PATTERNS, pattern_factory
    

class PatternManager:
    def __init__(self, led_config, args):
        self.led_config = led_config
        self.args = args

        # Pattern cache
        self.enable_cache = args.enable_cache
        self.cached_patterns = []
        if args.enable_cache:
            self.pattern_cache = PatternCache(led_config, args)
        else:
            self.pattern_cache = None

        # Dict of all patterns
        self.patterns = {}

        # List of pattern ids per group
        self.pattern_selected = []
   

    async def initialize_patterns(self):
        # Initialize all patterns
        for pattern_id in PATTERNS.keys():
            pattern = pattern_factory(pattern_id)
            pattern.prepareSegments(self.led_config)
            pattern.initialize()
            self.patterns[pattern_id] = pattern  
        
        # Initialize cached patterns
        if self.args.enable_cache:
            await self.pattern_cache.initialize_patterns()


    def _maybe_cached_pattern(self, pattern_id):
        if self.pattern_cache and pattern_id in self.pattern_cache.patterns:
            return self.pattern_cache.patterns[pattern_id]
        else:
            return self.patterns[pattern_id]
    

    def pattern(self, pattern_id):
        return self._maybe_cached_pattern(pattern_id)


    def reset_pattern(self, pattern_id):
        self.pattern(pattern_id).reset()


    def update_pattern_selection(self, pattern_ids):
        self.pattern_selected = pattern_ids
    

    def clear_selected_patterns(self):
        self.pattern_selected.clear()

    async def animate(self, iteration, delta):
        for pattern_id in self.pattern_selected:
            await self.pattern(pattern_id).animate(iteration, delta)