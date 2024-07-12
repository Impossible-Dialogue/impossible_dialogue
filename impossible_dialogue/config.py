import hashlib
import os

class OutputConfig:
    def __init__(self, config):
        self.multiplex = config.get("multiplex", False)
        self.queue_size = config.get("queue_size", 50)


class MusicConfig:
    def __init__(self, config):
        self.loop_segments = config.get("loop_segments", False)


class SoundConfig:
    def __init__(self, config):
        self.mode = config["mode"]
        if "output" in config:
            self.output_config = OutputConfig(config["output"])
        if "music_config" in config:
            self.music_config = MusicConfig(config["music_config"])

class OpcConfig:
    def __init__(self, config):
        self.server_ip = config["server_ip"]
        self.server_port = config["server_port"]


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
        self.led_config = config["led_config"]
        self.led_pattern_id = config["led_pattern_id"]
        self.opc = OpcConfig(config["opc"])


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

    def set_head_id(self, head_id):
        self._head_id = head_id

    def head_id(self):
        if self._head_id:
            return self._head_id
        else:
            return self.segment_list.head_id
    
    def hash(self):
        data = ''.join(filter(None, (self.text, self.head_id(), self._filename)))
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
        self.loop = config.get("loop", False)
        for i, segment_config in enumerate(config["segments"]):
            self.segments.append(Segment(i, segment_config, self, base_folder))
        
    def num_segments(self):
        return len(self.segments)

    def find_segment(self, segment_id):
        for segment in self.segments:
            if segment.id == segment_id:
                return segment


class SegmentLists:
    def __init__(self, segment_lists_config, head_configs, base_folder="media"):
        self.lists = {}
        for config in segment_lists_config:
            id = config["id"]
            if config.get("head_id", "") == "all":
                # Expand segments lists to all heads
                for head_config in head_configs.heads.values():
                    head_id = head_config.id
                    config["head_id"] = head_id
                    self.lists[id + "_" + head_id]  = SegmentList(config, base_folder)
            else:
                self.lists[id]  = SegmentList(config, base_folder)
    
    def num_lists(self):
        return len(self.lists)