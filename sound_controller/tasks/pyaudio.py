
import asyncio
import logging
import numpy as np
import pyaudio

pa = pyaudio.PyAudio()


async def pyaudio_output(input_stream, device_index=None, samplerate=48000, channels=2, blocksize=512, dtype='float32'):
    """Generator that streams blocks of audio data to a PyAudio output stream."""

    def callback(in_data, frame_count, time_info, status):
        assert frame_count == blocksize
        try:
            data = input_stream.get_nowait()
        except asyncio.QueueEmpty:
            logging.debug('Buffer is empty: increase buffersize?')
            data = np.zeros((blocksize, channels), dtype=dtype)
        return (data, pyaudio.paContinue)

    output_stream = pa.open(
        format=pyaudio.paFloat32,
        channels=channels,
        rate=samplerate,
        output=True,
        output_device_index=device_index,
        frames_per_buffer=blocksize,
        stream_callback=callback
    )

    # Wait for stream to finish.
    while output_stream.is_active():
        await asyncio.sleep(1.0)

    # Close the stream.
    output_stream.close()

    # Release PortAudio system resources.
    pa.terminate()
