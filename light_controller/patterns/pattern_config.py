from .rainbow_pattern import RainbowPattern
import numpy as np
from collections import namedtuple

import patterns.palettes as palettes
from patterns.color_roll_pattern import ColorRollPattern
from patterns.crossfade_pattern import CrossfadePattern
from patterns.fire_pattern import FirePatternUV
from patterns.flash_pattern import FlashPattern
from patterns.sparkle_pattern import SparklePattern
from patterns.sweep_pattern import SweepPattern
from patterns.theater_chase_pattern import TheaterChasePattern
from patterns.rainbow_pattern import RainbowPattern
from patterns.starburst_pattern import StarburstPattern
from patterns.checkers_pattern import CheckersPattern
from patterns.rainbow_waves_pattern import RainbowWavesPattern
from patterns.bouncing_blocks_pattern import BouncingBlocksPattern
from patterns.video_pattern import VideoPattern, Rect
from patterns.solid_color_pattern import SolidColorPattern
from patterns.color_distribution_pattern import ColorDistributionPattern
from patterns.pulse_pattern import PulsePattern


PatternConfig = namedtuple(
    'PatternConfig', ['pattern_class', 'params'])

SegmentMask = namedtuple(
    'SegmentMask', ['segment_uid', 'start', 'end'])

PATTERNS = {
    '0x0': PatternConfig("FirePatternUV", dict(palette=palettes.FIRE, width=2, height=100)),
    '1x0': PatternConfig("VideoPattern", dict(file='media/neon_tunnel.mp4', crop=Rect(169, 397, 200, 200))),
    '2x0': PatternConfig("VideoPattern", dict(file='media/radial_beams.mp4')),
    '3x0': PatternConfig("VideoPattern", dict(file='media/butter_churn.mp4', crop=Rect(60, 60, 60, 60))),
    '4x0': PatternConfig("VideoPattern", dict(file='media/psychill1.mp4', fps=10)),
    '5x0': PatternConfig("VideoPattern", dict(file='media/psychill1.mp4', crop=Rect(60, 130, 60, 60))),
    '6x0': PatternConfig("VideoPattern", dict(file='media/psychill2.mp4', crop=Rect(60, 130, 60, 60))),
    '7x0': PatternConfig("RainbowWavesPattern", dict()),
    '0x1': PatternConfig("VideoPattern", dict(file='media/blue_lines.mp4')),
    '1x1': PatternConfig("VideoPattern", dict(file='media/hearts.mp4')),
    '2x1': PatternConfig("VideoPattern", dict(file='media/rising_beams.mp4')),
    '3x1': PatternConfig("VideoPattern", dict(file='media/blue_horizon.mp4')),
    '4x1': PatternConfig("VideoPattern", dict(file='media/space_warp.mp4')),
    '5x1': PatternConfig("VideoPattern", dict(file='media/sparkling_ring.mp4')),
    '6x1': PatternConfig("VideoPattern", dict(file='media/neon_tunnel.mp4')),
    '7x1': PatternConfig("VideoPattern", dict(file='media/triangle_kaleidoscope.mp4')),
    '0x2': PatternConfig("CrossfadePattern", dict()),
    '1x2': PatternConfig("TheaterChasePattern", dict(speed=1.5, step_size=3)),
    '2x2': PatternConfig("SweepPattern", dict(decay_param=0.5, sweep_speed=0.3)),
    '3x2': PatternConfig("ColorRollPattern", dict()),
    '4x2': PatternConfig("BouncingBlocksPattern", dict()),
    # Head patterns - Not centered
    '1x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([255,   0,   0], dtype=np.uint8))),
    '2x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([255, 255,   0], dtype=np.uint8))),
    '3x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([255,  94, 218], dtype=np.uint8))),
    '4x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([  0,   0, 255], dtype=np.uint8))),
    '5x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([255, 127,   0], dtype=np.uint8))),
    '6x3': PatternConfig("ColorDistributionPattern", dict(use_polygon_centers=True, color=np.array([  0, 200,  20], dtype=np.uint8))),
    # Head pulsing when centered
    '5x7': PatternConfig("PulsePattern", dict()),
    # Fire pit pulsing patterns - centered
    'head_3x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 0, 14)])),
    'head_2x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 59, 73)])),
    'head_1x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 29, 43)])),
    'head_6x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 74, 88)])),
    'head_5x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 15, 28)])),
    'head_4x4': PatternConfig("PulsePattern", dict(segment_masks=[SegmentMask(1, 44, 58)])),
    # Fire pit solid patterns - centered
    'head_3x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1,  0, 14)], color=np.array([255,  94, 218], dtype=np.uint8))),
    'head_2x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1, 59, 73)], color=np.array([255, 255,   0], dtype=np.uint8))),
    'head_1x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1, 29, 43)], color=np.array([255,   0,   0], dtype=np.uint8))),
    'head_6x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1, 74, 88)], color=np.array([  0, 200,  20], dtype=np.uint8))),
    'head_5x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1, 15, 28)], color=np.array([255, 127,   0], dtype=np.uint8))),
    'head_4x5': PatternConfig("ColorDistributionPattern", dict(segment_masks=[SegmentMask(1, 44, 58)], color=np.array([  0,   0, 255], dtype=np.uint8))),
    # Other patterns
    '0x7': PatternConfig("FlashPattern", dict()),
    '1x7': PatternConfig("SparklePattern", dict(sparkle_probability=0.001, decay_param=0.95)),
    '2x7': PatternConfig("CheckersPattern", dict(decay_param=0.95)),
    '3x7': PatternConfig("StarburstPattern", dict(decay_param=0.95)),
    '4x7': PatternConfig("VideoPattern", dict(file='media/hearts.mp4', fps=10, crop=Rect(0, 0, 1, 1))),
    '6x7': PatternConfig("SolidColorPattern", dict(color=np.array([60, 60, 60], dtype=np.uint8))),
}

def pattern_factory(pattern_id):
    pattern_config = PATTERNS[pattern_id]
    cls = globals()[pattern_config.pattern_class]
    pattern = cls()
    for key, value in pattern_config.params.items():
        setattr(pattern.params, key, value)
    return pattern
