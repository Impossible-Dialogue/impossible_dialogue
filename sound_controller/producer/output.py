import asyncio
import logging

from producer.stream import Stream
from producer.channel_mixer import MultiChannelMixer
from tasks.pyaudio import pyaudio_output


class Output:
    def __init__(self, state, config, sample_rate=48000, channels=2, blocksize=512, dtype='float32'):
        self._state = state
        self._sample_rate = sample_rate
        self._channels = channels
        self._blocksize = blocksize
        self._dtype = dtype

        self._multiplex = config["multiplex"]
        self._output_streams = []

        if self._multiplex:
            output_stream = Stream(channels=channels,
                                   blocksize=blocksize, dtype=dtype)
            self._output_streams.append(output_stream)
            self._multiplexer = MultiChannelMixer(
                num_input_streams=state.num_heads(), output_stream=output_stream, channels=channels,
                blocksize=blocksize, dtype=dtype)
            self._pyaudio_task = asyncio.create_task(
                pyaudio_output(output_stream, device_index=None, samplerate=sample_rate, channels=channels, blocksize=blocksize, dtype=dtype))


    def input_stream(self, index):
        if self._multiplex:
            return self._multiplexer.input_stream(index)
