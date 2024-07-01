import asyncio
import logging

from head_mixer import HeadMixer
from channel import Channel

_ALL_CENTERED = "ALL_CENTERED"
_SOME_CENTERED = "SOME_CENTERED"
_NONE_CENTERED = "_NONE_CENTERED"



class Mixer:
    def __init__(self, heads):
        self._heads = heads
        self._heads_state = self.get_heads_state()
        self._head_mixers = {}
        self._channels = {}
        self._dialogue_mixer = None

        for head in heads:
            channel = Channel()
            self._channels[head] = channel
            self._head_mixers[head] = HeadMixer(head, channel)


    def heads_centered(self):
        num_heads_centered = sum(head.is_centered() for head in self._heads)
        if num_heads_centered == len(self._heads):
            return _ALL_CENTERED
        elif num_heads_centered > 0:
            return _SOME_CENTERED
        else:
            return _NONE_CENTERED

    def play_chime(self):
        return

    def mix_dialogue(self):
        return

    def loop(self):
        new_heads_state = self.heads_centered()
        if (self._heads_state == _SOME_CENTERED and
            new_heads_state == _ALL_CENTERED):
            self.play_chime()

        if (new_heads_state == _ALL_CENTERED):
            self._dialogue_mixer.loop()
        else:
            for head in self._heads:
                mixer = self._head_mixers[head]
                mixer.loop()


    async def run(self):
        poll_interval = 0.01
        while(True):
            self.loop()
            await asyncio.sleep(poll_interval)
