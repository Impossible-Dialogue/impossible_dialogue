import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from numpy import unique
from numpy import where
import math
import shapely
import csv
import ast

class Node:
    def __init__(self, p):
        self.p = p
        self.next = None

    def distance(self, other_node):
        return np.linalg.norm(self.p - other_node.p)


class Segment:
    def __init__(self, start, end):
        self.start = np.array(start)
        self.start_str = '{:.3f}, {:.3f}, {:.3f}'.format(
            start[0], start[1], start[2])
        self.end = np.array(end)
        self.end_str = '{:.3f}, {:.3f}, {:.3f}'.format(
            end[0], end[1], end[2])
        self.next = None

    def flip(self):
        self.start, self.end = self.end, self.start
        self.start_str, self.end_str = self.end_str, self.start_str

    def __repr__(self):
        return repr([self.start, self.end])


class Polygon:
    def __init__(self):
        self.vertices = []
        self.center = None

    def _compute_center(self):
        points = np.array(self.vertices)
        self.center = points.mean(axis=0)

    def from_segments(self, segments):
        for segment in segments:
            self.vertices.append(segment.start)
        self._compute_center()

    def __repr__(self):
        return repr(self.vertices)

    def to_dict(self):
        return [v.tolist() for v in self.vertices]

class Path:
    def __init__(self, segments=[]):
        self.vertices = []

    def from_segments(self, segments):
        for i, segment in enumerate(segments):
            if i == 0:
                self.vertices.append(segment.start)
            self.vertices.append(segment.end)

    def __repr__(self):
        return repr(self.vertices)

def pca(data):
    # Calculate the mean of the points, i.e. the 'center' of the cloud
    datamean = data.mean(axis=0)
    # print('mean ' + str(datamean))

    # PCA to generate a line representation for each tube
    mu = data.mean(0)
    C = np.cov(data - mu, rowvar=False)
    d, u = np.linalg.eigh(C)
    U = u.T[::-1]

    # Project points onto the principle axes
    Z = np.dot(data - mu, U.T)
    # print('min Z ' + str(Z.min()))
    # print('max Z ' + str(Z.max()))

    return Z, U, mu


def cluster(data, eps, min_samples):
    model = DBSCAN(eps=eps, min_samples=min_samples)

    # fit model and predict clusters
    labels = model.fit_predict(data)

    # retrieve unique clusters
    clusters = unique(labels)

    if False:
        x2 = Z.T[0]
        y2 = Z.T[1]

        # create scatter plot for samples from each cluster
        for cluster in clusters:
            # get row indexes for samples with this cluster
            row_ix = where(labels == cluster)
            # create scatter of these samples
            plt.scatter(x2[row_ix], y2[row_ix], s=3)
        # show the plot
        plt.rcParams['figure.figsize'] = [25, 5]
        plt.axis('scaled')
        plt.show()
    
    return clusters, labels


def create_line_segments(data, clusters, labels):
    # First create an unordered list of nodes, one per cluster with using the mean of the cluster points.
    nodes = []
    for cluster in clusters:
        if cluster < 0: 
            continue
        row_ix = where(labels == cluster)
        cluster_points = data[row_ix]
        node = Node(p=cluster_points.mean(axis=0))
        nodes.append(node)
    if len(nodes) == 0: 
        return None

    # Connect nodes to line segments starting from a random node and extending in both directions the result is a start and an end node connected in a linked list
    start = nodes.pop()
    end = start
    while len(nodes) > 0:
        min_node = None
        min_dist = float('inf')
        closest_to_start = True

        for node in nodes:
            start_dist = start.distance(node)
            end_dist = end.distance(node)

            if start_dist < min_dist and start_dist <= end_dist:
                min_dist = start_dist
                min_node = node
                closest_to_start = True

            if end_dist < min_dist and end_dist < start_dist:
                min_dist = end_dist
                min_node = node
                closest_to_start = False

        if closest_to_start:
            min_node.next = start
            start = min_node
        else:
            end.next = min_node
            end = min_node

        nodes.remove(min_node)

    return start


def line_segments_length(start):
    n = start
    total_length = 0
    while True:
        if n.next == None:
            break
        total_length = total_length + n.distance(n.next)
        n = n.next
    return total_length


# Generate LED positions by tracing along the line segments until the correct number of LED are created
def trace_line_segments(start, num_leds, offset, led_dist):
    segment_points = []
    fraction = 0
    n = start
    dist = offset
    for i in range(num_leds):
        new_fraction = fraction + dist / n.distance(n.next)
        while new_fraction >= 1:
            # Move to next segment
            dist = dist - (1 - fraction) * n.distance(n.next)
            n = n.next
            fraction = 0
            new_fraction = dist / n.distance(n.next)

        fraction = new_fraction
        p = n.p + fraction * (n.next.p - n.p)
        segment_points.append(p)
        dist = led_dist

    return np.array(segment_points)


def generate_led_positions(data, clusters, labels, start_offset, end_offset, leds_per_meter):
    leds_distance = 1 / leds_per_meter
    segments = create_line_segments(data, clusters, labels)
    if segments == None:
        return [], 0
    length = line_segments_length(segments)
    length = length - start_offset - end_offset
    num_leds = math.floor(length * leds_per_meter)
    points = trace_line_segments(segments, num_leds, start_offset, leds_distance)
    return points, length


def prepare_data(group):
    x = np.array([v[0] for v in group.vertices])
    y = np.array([v[1] for v in group.vertices])
    z = np.array([v[2] for v in group.vertices])

    data = np.concatenate((x[:, np.newaxis],
                        y[:, np.newaxis],
                        z[:, np.newaxis]),
                        axis=1)
    return data


def plot_segment(data, clusters, labels, segment_points):
    Z, U, mu = pca(data)
    x2 = Z.T[0]
    y2 = Z.T[1]

    # create scatter plot for samples from each cluster
    for cluster in clusters:
        # get row indexes for samples with this cluster
        row_ix = where(labels == cluster)
        # create scatter of these samples
        plt.scatter(x2[row_ix], y2[row_ix], s=3)

    # # create scatter plot for line segments
    # print('U ' + str(U))
    L = np.dot(segment_points - mu, U.T)
    xl2 = L.T[0]
    yl2 = L.T[1]
    plt.scatter(xl2, yl2, s=3)

    plt.axis('scaled')
    plt.show()
    plt.rcParams['figure.figsize'] = [25, 5]


def project_2d(data):
    Z, U, mu = pca(data)
    return Z[:,:2]


def distance(point, other_point):
    return np.linalg.norm(point - other_point)


def create_paths(path_segments, max_distance=0.01):
    segments = [Segment(segment_points[0], segment_points[1])
                for segment_points in path_segments]

    paths = []
    while segments:
        path_segments = []
        first_segment = segments.pop()
        last_segment = first_segment
        path_segments.append(first_segment)
        start_new_path = False

        while not start_new_path:
            start_new_path = True
            for segment in segments:
                if distance(last_segment.end, segment.start) <= max_distance:
                    segments.remove(segment)
                    path_segments.append(segment)
                    last_segment = segment
                    start_new_path = False
                    break

                if distance(last_segment.end, segment.end) <= max_distance:
                    segments.remove(segment)
                    segment = Segment(segment.end, segment.start)
                    path_segments.append(segment)
                    last_segment = segment
                    start_new_path = False
                    break

                if distance(first_segment.start, segment.end) <= max_distance:
                    segments.remove(segment)
                    path_segments.insert(0, segment)
                    first_segment = segment
                    start_new_path = False
                    break

                if distance(first_segment.start, segment.start) <= max_distance:
                    segments.remove(segment)
                    segment = Segment(segment.end, segment.start)
                    path_segments.insert(0, segment)
                    first_segment = segment
                    start_new_path = False
                    break

        # print(len(path_segments))
        p = Path()
        p.from_segments(path_segments)
        paths.append(p)

    return paths


def project_point_2d(point, U, mu):
    L = np.dot(point - mu, U.T)
    return np.array([L.T[0], L.T[1]])


def project_polygons_2d(polygons):
    x = np.array([v[0] for p in polygons for v in p.vertices])
    y = np.array([v[1] for p in polygons for v in p.vertices])
    z = np.array([v[2] for p in polygons for v in p.vertices])

    data = np.concatenate((x[:, np.newaxis],
                           y[:, np.newaxis],
                           z[:, np.newaxis]),
                          axis=1)

    Z, U, mu = pca(data)
    polygons_2d = []
    for p in polygons:
        polygon_2d = Polygon()
        for v in p.vertices:
            vertex_2d = project_point_2d(v, U, mu)
            polygon_2d.vertices.append(vertex_2d)
        polygons_2d.append(polygon_2d)
    return polygons_2d, U, mu


def plot_polygons_2d(polygons_2d):

    # create scatter plot for samples from each cluster
    for polygon in polygons_2d:
        x = [v[0] for v in polygon.vertices] + [polygon.vertices[0][0]]
        y = [v[1] for v in polygon.vertices] + [polygon.vertices[0][1]]
        plt.plot(x, y)

    # plt.axis('scaled')
    # plt.show()
    # plt.rcParams['figure.figsize'] = [25, 5]


def plot_paths(polygons_2d):

    # create scatter plot for samples from each cluster
    for polygon in polygons_2d:
        x = [v[0] for v in polygon.vertices] + [polygon.vertices[0][0]]
        y = [v[1] for v in polygon.vertices] + [polygon.vertices[0][1]]
        plt.plot(x, y)

    # plt.axis('scaled')
    # plt.show()
    # plt.rcParams['figure.figsize'] = [25, 5]


def plot_segment(segment):
    fig = plt.figure()
    x = segment.points_2d[:][:, 0]
    y = segment.points_2d[:][:, 1]
    plt.plot(x, y)

    plt.axis('scaled')
    plt.show()
    plt.rcParams['figure.figsize'] = [25, 5]


def read_line_segments(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        segments = []
        for row in reader:
            uid = int(row[0])
            name = row[1]
            actual_num_leds = int(row[2])
            actual_length = float(row[3])
            reverse = (row[4] == 'TRUE')
            led_offset = int(row[5])
            sub_component = row[6]
            actual_num_adressable_leds = int(row[7])
            csv_points = ast.literal_eval(row[10])

            segment_points = []
            for p in csv_points:
                point = np.array(p)
                point = (point.reshape((3, 1))).reshape((1, 3))
                point = np.squeeze(np.asarray(point))
                segment_points.append(p)
            segments.append(segment_points)

    return segments


def create_polygons_from_segments(segments):
    start_dict = {}
    end_dict = {}
    for segment_points in segments:
        segment = Segment(segment_points[0], segment_points[1])
        if segment.start_str in start_dict:
            segment2 = start_dict[segment.start_str]
            if segment.end_str == segment2.end_str:
                print(
                    f"Ignoring duplicate line segment [[{segment.start_str}], [{segment.end_str}]]")
                continue
            else:
                segment = Segment(segment_points[1], segment_points[0])
                print(
                    f"Flipping line segment [[{segment.start_str}], [{segment.end_str}]]")
        if segment.end_str in end_dict:
            segment2 = end_dict[segment.end_str]
            if segment.start_str == segment2.start_str:
                print(
                    f"Ignoring duplicate line segment [[{segment.start_str}], [{segment.end_str}]]")
                continue
            else:
                segment = Segment(segment_points[1], segment_points[0])
                print(
                    f"Flipping line segment [[{segment.start_str}], [{segment.end_str}]]")
        start_dict[segment.start_str] = segment
        end_dict[segment.end_str] = segment

    polygons = []
    while start_dict:
        polygon_segments = []
        polygon_start_str, segment = start_dict.popitem()
        end_str = '%s' % segment.end_str
        end_dict.pop(end_str)
        polygon_segments.append(segment)
        while end_str != polygon_start_str:
            if end_str in start_dict:
                segment = start_dict.pop(end_str)
                end_str = '%s' % segment.end_str
                end_dict.pop(end_str)
                polygon_segments.append(segment)
            elif end_str in end_dict:
                segment = end_dict.pop(end_str)
                start_dict.pop(segment.start_str)
                segment = Segment(segment.end, segment.start)
                end_str = '%s' % segment.end_str
                polygon_segments.append(segment)
            else:
                print(
                    f"Couldn't find line segment {end_str} to finish polygon.")
                break
        # print(len(polygon_segments))
        p = Polygon()
        p.from_segments(polygon_segments)
        polygons.append(p)

    return polygons


def polygon_index(point_2d, polygons_2d):
    point = shapely.Point(point_2d[0], point_2d[1])
    for i, p in enumerate(polygons_2d):
        polygon = shapely.Polygon([(v[0], v[1]) for v in p.vertices])
        if polygon.contains(point):
            plt.scatter([point_2d[0]], point_2d[1], color=f"C{i}")
            return i
    print(f"ERROR: couldn't find a polygon containing {point_2d}")
    # plt.scatter([point_2d[0]], point_2d[1])


def project_path_2d(path, U=None, mu=None):
    # if not isinstance(U, np.ndarray) or not isinstance(mu, np.ndarray):
    #     x = np.array([v[0] for v in path.vertices])
    #     y = np.array([v[1] for v in path.vertices])
    #     z = np.array([v[2] for v in path.vertices])

    #     data = np.concatenate((x[:, np.newaxis],
    #                            y[:, np.newaxis],
    #                            z[:, np.newaxis]),
    #                            axis=1)
    #     Z, U, mu = pca(data)

    path_2d = Path()
    for v in path.vertices:
        vertex_2d = project_point_2d(v, U, mu)
        path_2d.vertices.append(vertex_2d)

    return path_2d


def find_polygon_indices(path_2d, polygons_2d, index_offset=0):
    polygon_indices = []
    for point in path_2d.vertices:
        index = polygon_index(point, polygons_2d)
        polygon_indices.append(index + index_offset)
    return polygon_indices


def create_polygon_path(polygon_indices, polygons):
    current_polygon_cluster = -1
    path = Path()
    for i in polygon_indices:
        if i == current_polygon_cluster:
            continue
        polygon = polygons[i]
        path.vertices.append(polygon.center)
        current_polygon_cluster = i

    num_points_in_polygons = []
    count = 1
    for i in range(len(polygon_indices) - 1):
        # Check if the next number is consecutive
        if polygon_indices[i] == polygon_indices[i+1]:
            count = count + 1
        else:
            # If it is not append the count and restart counting
            num_points_in_polygons.append(count)
            count = 1
    # Since we stopped the loop one early append the last count
    num_points_in_polygons.append(count)

    return path, num_points_in_polygons


def plot_path_2d(path_2d):
    plt.plot([v[0] for v in path_2d.vertices], 
             [v[1] for v in path_2d.vertices], linewidth=7.0)
