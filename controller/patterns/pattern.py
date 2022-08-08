import numpy as np
import sys


class Segment:
    def __init__(self, uid, num_leds, led_positions):
        self.uid = uid
        self.num_leds = num_leds
        self.colors = np.array([[255, 0, 0] for i in range(num_leds)])
        self.led_positions = np.array(led_positions)

class Pattern:
    class PatternParameters:
        pass

    def __init__(self):
        self.segments = []
        self.params = self.PatternParameters()

    def prepareSegments(self, led_config):
        for s in led_config['led_segments']:
            segment = Segment(s['uid'], s['num_leds'], s['led_positions'])
            self.segments.append(segment)

    def initialize(self):
        pass
        
    def animate(self, delta):
        pass

class PatternUV(Pattern):
   
    def __init__(self):
        super().__init__()

    def generateUVCoordinates(self, width, height, offset_u=0, offset_v=0):
        max_x = max_y = max_z = sys.float_info.min
        min_x = min_y = min_z = sys.float_info.max
        for segment in self.segments:
            for p in segment.led_positions:
                max_x = max(max_x, p[0])
                min_x = min(min_x, p[0])
                max_y = max(max_y, p[1])
                min_y = min(min_y, p[1])
                max_z = max(max_z, p[2])
                min_z = min(min_z, p[2])

        # Shift 3D points so that min(y) and min(z) are at the origin
        offset = np.array([-min_y, -min_z])
        # Scale y and z axis to [0, 1].
        # Note: the axis are scaled independently which could lead to distortions
        scale = np.array([(height - 1) / (max_y - min_y),
                          (width - 1) / (max_z - min_z)])
        for segment in self.segments:
            uv = []
            for p in segment.led_positions:
                pm = np.multiply(p[1:] + offset, scale).astype(int)
                u = int(height) - 1 - pm[0] + offset_u
                v = pm[1] + offset_v
                uv.append(np.array([u, v]))
            segment.uv = np.array(uv)

    def initialize(self):
        pass
        
    def animate(self, delta):
        pass

