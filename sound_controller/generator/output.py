import asyncio
import logging

from generator.stream import Stream
from generator.channel_mixer import MultiChannelMixer
from tasks.pyaudio import pyaudio_output, pyaudio_output_stereo


class Output:
    def __init__(self, state, config, sample_rate=48000, channels=2, blocksize=512, dtype='float32'):
        self._state = state
        self._sample_rate = sample_rate
        self._channels = channels
        self._blocksize = blocksize
        self._dtype = dtype

        self._multiplex = config.multiplex
        self._output_streams = []
        self._input_streams = []
        self._multiplexers = []
        self._pyaudio_tasks = []

        if self._multiplex:
            output_stream = Stream(queue_size=config.queue_size, channels=channels,
                                   blocksize=blocksize, dtype=dtype)
            self._output_streams.append(output_stream)
            self._multiplexer = MultiChannelMixer(
                num_input_streams=state.num_heads(), output_stream=output_stream, channels=channels,
                blocksize=blocksize, dtype=dtype)
            self._pyaudio_task = asyncio.create_task(
                pyaudio_output(output_stream, device_index=None, samplerate=sample_rate, channels=channels, blocksize=blocksize, dtype=dtype))
        else:
            self._input_streams = [Stream(channels=channels, blocksize=blocksize, dtype=dtype)
                                   for i in range(state.num_heads())]
            
            output_configs = [
                {
                    "device_index": 0,
                    "head_index_channel_1": 0,
                    "head_index_channel_2": 1,
                },
                {
                    "device_index": 2,
                    "head_index_channel_1": 2,
                    "head_index_channel_2": 3,
                },
                {
                    "device_index": 1,
                    "head_index_channel_1": 4,
                    "head_index_channel_2": 5,
                }
            ]
            
            for output_config in output_configs:
                self._pyaudio_tasks.append(asyncio.create_task(
                    pyaudio_output_stereo(
                        self._input_streams[output_config["head_index_channel_1"]], 
                        self._input_streams[output_config["head_index_channel_2"]], 
                        device_index=output_config["device_index"], 
                        samplerate=sample_rate, channels=channels, blocksize=blocksize, dtype=dtype)))


    def input_stream(self, index):
        if self._multiplex:
            return self._multiplexer.input_stream(index)
        else:
            return self._input_streams[index]
