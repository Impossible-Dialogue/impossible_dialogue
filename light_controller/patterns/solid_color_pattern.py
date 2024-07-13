from patterns.pattern import Pattern
import numpy as np


class SolidColorPattern(Pattern):
    def __init__(self):
        super().__init__()
        self.params.color = np.array([255, 255, 255], dtype=np.uint8)

    def initialize(self):
        for segment in self.segments:
            for i in range(segment.num_leds):
                segment.colors[i] = self.params.color

    async def animate(self, delta):
        pass
