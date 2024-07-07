import hashlib
import os


class AudioConfigConfig:
    def __init__(self, config):
        self.language_code = config["language_code"]
        self.voice_name = config["voice_name"]
        self.speaking_rate = config["speaking_rate"]
        self.pitch = config["pitch"]
        self.volume_gain_db = config["volume_gain_db"]


class HeadConfig:
    def __init__(self, config):
        self.id = config["id"]
        self.orientation = config["orientation"]
        self.orientation_ws_url = config["orientation_ws_url"]
        self.orientation_topic = config["orientation_topic"]
        self.audio_config = AudioConfigConfig(config["audio_config"])


class HeadConfigs:
    def __init__(self, head_configs):
        self.heads = {}
        for config in head_configs:
            self.heads[config["id"]] = HeadConfig(config)


class Segment:
    def __init__(self, index, config, segment_list, base_folder="media"):
        self.index = index
        self.segment_list = segment_list
        self.base_folder = base_folder
        self.id = config.get("id", None)
        self._head_id = config.get("head_id", None)
        self.text = config.get("text", None)
        self._filename = config.get("filename", None)

    def head_id(self):
        if self._head_id:
            return self._head_id
        else:
            return self.segment_list.head_id
    
    def hash(self):
        data = ''.join(filter(None, (self.text, self._head_id, self._filename)))
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:8]

    def filename(self):
        segment_list_id = self.segment_list.id
        if self._filename:
            return os.path.join(self.base_folder,
                                segment_list_id, 
                                self._filename)
        head_id = self.head_id()
        assert head_id
        if self.id:
            id = self.id
        else:
            id = self.hash()
        return os.path.join(self.base_folder,
                            segment_list_id,
                            str(self.index).zfill(3) + '_' + head_id + '_'  + str(id) + '.wav')

class SegmentList:
    def __init__(self, config, base_folder="media"):
        self.segments = []
        self.id = config["id"]
        self.head_id = config.get("head_id", None)
        for i, segment_config in enumerate(config["segments"]):
            self.segments.append(Segment(i, segment_config, self, base_folder))
        
    def num_segments(self):
        return len(self.segments)

    def find_segment(self, segment_id):
        for segment in self.segments:
            if segment.id == segment_id:
                return segment


class SegmentLists:
    def __init__(self, segment_lists_config, base_folder="media"):
        self.lists = {}
        for config in segment_lists_config:
            id = config["id"]
            self.lists[id] = SegmentList(config, base_folder)
    
    def num_lists(self):
        return len(self.lists)