import numpy as np

class LedConfig():
    def __init__(self):
        self.total_num_leds = 0
        self.total_length = 0
        self.total_num_segments = 0
        self.led_segments = []
        self.polygons = []

    def to_dict(self):
        return {
            'total_num_leds': self.total_num_leds,
            'total_length': self.total_length,
            'total_num_segments': self.total_num_segments,
            'led_segments': [s.to_dict() for s in self.led_segments],
            'polygons': [p.to_dict() for p in self.polygons]
        }


class Segment():
    def __init__(self, uid, name, points, num_leds, length, polygon_indices=None, polygon_centers=None, num_points_in_polygons=None, points_2d=None):
        self.uid = uid
        self.name = name
        self.points = points
        self.num_leds = num_leds
        self.length = length
        self.polygon_indices = polygon_indices
        self.polygon_centers = polygon_centers
        self.num_points_in_polygons = num_points_in_polygons
        self.points_2d = points_2d

    def merge(self, other):
        self.points = np.concatenate((self.points, other.points), axis=0)
        self.polygon_indices = np.concatenate((self.polygon_indices, other.polygon_indices), axis=0)
        self.polygon_centers = np.concatenate((self.polygon_centers, other.polygon_centers), axis=0)
        self.num_points_in_polygons = np.concatenate((self.num_points_in_polygons, other.num_points_in_polygons), axis=0)
        self.points_2d = np.concatenate((self.points_2d, other.points_2d), axis=0)
        self.num_leds += other.num_leds
        self.length += other.length

    def flip(self):
        self.points = np.flip(self.points, axis=0)
        self.polygon_indices = np.flip(self.polygon_indices, axis=0)
        self.polygon_centers = np.flip(self.polygon_centers, axis=0)
        self.num_points_in_polygons = np.flip(self.num_points_in_polygons, axis=0)
        self.points_2d = np.flip(self.points_2d, axis=0)

    def to_dict(self):
        return {
            'uid': self.uid,
            'name': self.name,
            'num_leds': self.num_leds,
            'length': self.length,
            'led_positions': self.points.tolist(),
            'polygon_indices': self.polygon_indices.tolist(),
            'polygon_centers': self.polygon_centers.tolist(),
            'num_points_in_polygons': self.num_points_in_polygons.tolist()
        }