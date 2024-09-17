import json
import time

class HeadState:
    id = None
    orientation = None

    def __init__(self, config):
        self._config = config
        self._id = config["id"]
        self._orientation = config["orientation"]
        self._last_udpate = None

    def to_dict(self):
        data = {}
        data["id"] = self._id
        data["orientation"] = self._orientation
        data["last_udpate"] = self._last_udpate
        return data
    
    def is_centered(self):
        return self._orientation <= 45 and self._orientation > -45

    def orientation(self):
        return self._orientation

    def set_orientation(self, val):
        self._orientation = val
        self._last_udpate = time.time()


class InstallationState:
    def __init__(self, config):
        self._config = config
        self._last_udpate = None
        self._head_states = self._create_head_states(config)

    def _create_head_states(self, config):
        head_states = {}
        for head_config in config["heads"]:
            id = head_config["id"]
            head_states[id] = HeadState(head_config)
        return head_states

    def to_dict(self):
        data = {}
        data["head_states"] = [state.to_dict() for state in self._head_states.values()]
        return data
    
    def to_json(self):
        return json.dumps(self.to_dict())

    def last_update(self):
        return self._last_udpate

    def num_heads(self):
        return len(self._head_states)

    def all_heads_centered(self):
        num_heads_centered = sum(head.is_centered()
                                 for head in self._head_states.values())
        return num_heads_centered == self.num_heads()

    def some_heads_centered(self):
        num_heads_centered = sum(head.is_centered()
                                 for head in self._head_states.values())
        return num_heads_centered > 0 and num_heads_centered < self.num_heads()

    def no_heads_centered(self):
        num_heads_centered = sum(head.is_centered()
                                 for head in self._head_states.values())
        return num_heads_centered == 0

    def head_state(self, id):
        return self._head_states[id]

    def set_head_orientation(self, head_id, val):
        self._head_states[head_id].set_orientation(val)
        self._last_udpate = time.time()
