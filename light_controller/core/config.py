
class OpcConfig:
    def __init__(self, config):
        self.server_ip = config["server_ip"]
        self.server_port = config["server_port"]

class HeadConfig:
    def __init__(self, config):
        self.id = config["id"]
        self.orientation = config["orientation"]
        self.orientation_ws_url = config["orientation_ws_url"]
        self.orientation_topic = config["orientation_topic"]
        self.led_config = config["led_config"]
        self.led_pattern_id = config["led_pattern_id"]
        self.opc = OpcConfig(config["opc"])

class HeadConfigs:
    def __init__(self, objects):
        self.heads = {}
        for config in objects:
            if config["type"] == "head":
                self.heads[config["id"]] = HeadConfig(config)