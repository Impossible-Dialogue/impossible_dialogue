
class SoundFile:
    def __init__(self, config):
        self._id = config["id"]
        self._filename = config["filename"]

    def id(self):
        return self._id

    def filename(self):
        return self._filename
