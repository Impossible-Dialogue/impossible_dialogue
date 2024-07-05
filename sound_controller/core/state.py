

class HeadState:
    id = None
    orientation = None

    def __init__(self, config):
        self._config = config
        self._id = config["id"]
        self._orientation = config["orientation"]

    def is_centered(self):
        return self._orientation <= 30 and self._orientation > -30

    def set_orientation(self, val):
        self._orientation = val


class InstallationState:
    def __init__(self, config):
        self._config = config
        self._head_states = self._create_head_states(config)

    def _create_head_states(self, config):
        head_states = {}
        for head_config in config["heads"]:
            id = head_config["id"]
            head_states[id] = HeadState(head_config)
        return head_states

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
