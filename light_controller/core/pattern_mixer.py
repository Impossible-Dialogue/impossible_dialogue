from patterns.pattern import Pattern
import numpy as np

class PatternMix(Pattern):
    def __init__(self, pattern_manager):
        super().__init__()
        self.params.use_polygon_centers = False
        self.pattern_manager = pattern_manager
        self.base_patterns = []
        self.mix_patterns = []
        self.replace_patterns = []
        self.brighness_patterns = []
        self.intensity = 1.0

    def get_patterns_from_id(self, pattern_ids):
        selected_patterns = []
        for pattern_id in pattern_ids:
            pattern = self.pattern_manager.pattern(pattern_id)
            selected_patterns.append(pattern)
        return selected_patterns

    def set_mix(self, base_pattern_ids, replace_pattern_ids, mix_pattern_ids, brighness_pattern_ids):
        self.base_patterns = self.get_patterns_from_id(base_pattern_ids)
        self.replace_patterns = self.get_patterns_from_id(replace_pattern_ids)
        self.mix_patterns = self.get_patterns_from_id(mix_pattern_ids)
        self.brighness_patterns = self.get_patterns_from_id(brighness_pattern_ids)

    def _maybe_repeat_colors(self, segment, pattern):
        if pattern.params.use_polygon_centers:
            return np.repeat(segment.colors, segment.color_repeats, axis=0)
        else:
            return segment.colors
        
    async def update(self):
        # Zero out colors
        for segment in self.segments:
            segment.colors[:] = 0

        # Base
        for pattern in self.base_patterns:
            for segment, mix_segment in zip(self.segments, pattern.segments):
                colors = self._maybe_repeat_colors(mix_segment, pattern)
                if mix_segment.mask:
                    # Mask available, copy masked LEDs only
                    m = mix_segment.mask
                    segment.colors[m.start:m.end] = colors[m.start:m.end]
                else:
                    # No mask, copy everything
                    np.copyto(segment.colors, colors)

        # Replace
        for pattern in self.replace_patterns:
            included_segments = list(pattern.getSegments())
            for segment, mix_segment in zip(self.segments, pattern.segments):
                colors = self._maybe_repeat_colors(mix_segment, pattern)
                if mix_segment in included_segments:
                    if mix_segment.mask:
                        # Mask available, copy masked LEDs only
                        m = mix_segment.mask
                        segment.colors[m.start:m.end] = colors[m.start:m.end]
                    else:
                        # No mask, copy everything
                        np.copyto(segment.colors, colors)

        # Mix
        for pattern in self.mix_patterns:
            for segment, mix_segment in zip(self.segments, pattern.segments):
                colors = self._maybe_repeat_colors(mix_segment, pattern)
                tmp = 255 - colors  # a temp uint8 array here
                np.putmask(segment.colors, tmp < segment.colors, tmp)  # a temp bool array here
                if mix_segment.mask:
                    # Mask available, copy masked LEDs only
                    m = mix_segment.mask
                    segment.colors[m.start:m.end] += colors[m.start:m.end]
                else:
                    # No mask, copy everything
                    segment.colors += colors

        # Brightness
        for pattern in self.brighness_patterns:
            for segment, mix_segment in zip(self.segments, pattern.segments):
                colors = self._maybe_repeat_colors(mix_segment, pattern)
                if mix_segment.mask:
                    # Mask available, multiply masked LEDs only
                    m = mix_segment.mask
                    segment.colors[m.start:m.end] = np.multiply(segment.colors[m.start:m.end], colors[m.start:m.end] / 255.0)
                else:
                    # No mask, multiply everything
                    segment.colors = np.multiply(segment.colors, colors / 255.0)
                        

        return self.segments
