from patterns.pattern import Pattern
import numpy as np


def clamp_color(c): 
    if c < 0: 
        return 0
    elif c > 255: 
        return 255
    else: 
        return round(c) 

class ColorDistributionPattern(Pattern):
    def __init__(self):
        super().__init__()
        self.params.color = np.array([255, 255, 255], dtype=np.uint8)
        self.params.standard_deviation = 30

    def initialize(self):
        for segment in self.segments:
            for i in range(segment.num_leds):
                for j in range(3):
                    segment.colors[i][j]  = clamp_color(np.random.normal(
                        loc=self.params.color[j], 
                        scale=self.params.standard_deviation))

    async def animate(self, delta):
        pass
