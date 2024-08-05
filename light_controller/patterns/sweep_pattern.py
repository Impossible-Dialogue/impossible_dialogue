from patterns.pattern import Pattern
from patterns import utils
import numpy as np
import random

class SweepPattern(Pattern):
    def __init__(self):
        super().__init__()
        self.params.color = np.array([255, 255, 255], dtype=np.uint8)
        self.params.background_color = np.array([0, 0, 0], dtype=np.uint8)
        self.params.decay_random = True
        self.params.decay_param = 0.5
        self.params.sweep_speed = 0.3
        self.params.loop = True

    def initialize(self):
        self.pattern_segments = []
        for segment in self.segments:
            pattern_segment = SweepPatternSegment(segment, self.params)
            pattern_segment.initialize()
            self.pattern_segments.append(pattern_segment)

    async def animate(self, iteration, delta):
        for pattern_segment in self.pattern_segments:
            await pattern_segment.animate(iteration, delta)


class SweepPatternSegment(Pattern):
    def __init__(self, segment, params):
        self.segment = segment
        self.params = params
        self.current_sweep_fraction = 0
        
    def initialize(self):
        np.copyto(self.segment.colors, np.array(
            [self.params.background_color for i in range(self.segment.num_leds)]))    

    async def animate(self, iteration, delta):
        current_index = int(self.current_sweep_fraction *
                            self.segment.num_leds)
        if current_index == self.segment.num_leds:
            if self.params.loop:
                self.current_sweep_fraction = 0
            return

        new_sweep_fraction = utils.clamp(
            0.0, self.current_sweep_fraction + delta * self.params.sweep_speed, 1.0)
        new_index = int(new_sweep_fraction * self.segment.num_leds)

        # Color sweeped LEDs
        for i in range(current_index, min(new_index + 1, self.segment.num_leds)):
            self.segment.colors[i] = self.params.color

        # Decay all other LEDs
        for i in range(0, min(current_index + 1, self.segment.num_leds)):
            if (not self.params.decay_random) or (random.randint(0, 10) > 5):
                self.segment.colors[i] = self.params.decay_param * self.segment.colors[i] + \
                    (1 - self.params.decay_param) * self.params.background_color

        if new_index < self.segment.num_leds - 2:
            for i in range(new_index + 1, self.segment.num_leds):
                if (not self.params.decay_random) or (random.randint(0, 10) > 5):
                    self.segment.colors[i] = self.params.decay_param * self.segment.colors[i] + (
                        1 - self.params.decay_param) * self.params.background_color

        self.current_sweep_fraction = new_sweep_fraction
