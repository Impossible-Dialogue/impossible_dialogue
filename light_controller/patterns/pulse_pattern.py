from patterns.pattern import Pattern
import math
import numpy as np


class PulsePattern(Pattern):
    def __init__(self):
        super().__init__()
        self.params.color = np.array([255, 255, 255], dtype=np.uint8)
        self.params.pulse_speed = 0.8
        self.params.pulse_min_value = 0.0
        self.params.pulse_max_value = 1.0
        self.time = 0

    def initialize(self):
        for segment in self.segments:
            np.copyto(segment.colors, np.array(
                [self.params.color for i in range(segment.num_leds)]))

    async def animate(self, iteration, delta):
        d = (self.params.pulse_max_value -
             self.params.pulse_min_value) / 2.35040238
        self.time += delta
        dV = (math.exp(math.sin(self.params.pulse_speed * self.time / 2.0 * math.pi)) - 0.36787944) * d
        val = self.params.pulse_min_value + dV
        for segment in self.segments:
            for i in range(segment.num_leds):
                segment.colors[i] = self.params.color * val