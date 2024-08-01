from patterns.pattern import Pattern
import numpy as np


class FlashPattern(Pattern):
    def __init__(self):
        super().__init__()
        self.params.color = np.array([255, 255, 255], dtype=np.uint8)
        self.params.background_color = np.array([0, 0, 0], dtype=np.uint8)
        self.params.decay_param = 0.95
        self.params.reset_time = 5.0
        self._time_since_reset = 0

    def reset(self):
        self._time_since_reset = 0
        for pattern_segment in self.pattern_segments:
            pattern_segment.reset()
        
    def initialize(self):
        self.pattern_segments = []
        for segment in self.segments:
            pattern_segment = FlashPatternSegment(segment, self.params)
            pattern_segment.initialize()
            self.pattern_segments.append(pattern_segment)

    async def animate(self, iteration, delta):
        self._time_since_reset += delta
        if self._time_since_reset >= self.params.reset_time:
            self.reset()
        for pattern_segment in self.pattern_segments:
            await pattern_segment.animate(delta)


class FlashPatternSegment(Pattern):
    def __init__(self, segment, params):
        super().__init__()
        self.segment = segment
        self.params = params
        self.start_flash = True

    def reset(self):
        super().reset()
        self.start_flash = True

    async def animate(self, iteration, delta):
        if self.start_flash:
            self.segment.colors[:] = self.params.color
            self.start_flash = False
        else:
            for i in range(self.segment.num_leds):
                self.segment.colors[i] = self.params.decay_param * self.segment.colors[i] + \
                        (1 - self.params.decay_param) * self.params.background_color
                