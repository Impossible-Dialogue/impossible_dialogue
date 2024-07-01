
import numpy as np
import pyaudio


async def pyaudio_output(input_queue, device_index, params):
    """Generator that streams blocks of audio data to a PyAudio output stream."""

    def callback(in_data, frame_count, time_info, status):
        assert frame_count == args.blocksize
        try:
            data = input_queue.get_nowait()
        except asyncio.QueueEmpty:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            data = np.zeros(
                (params.blocksize, params.channels), dtype='float32')
        return (data, pyaudio.paContinue)

    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=params.channels,
        rate=params.samplerate,
        output=True,
        output_device_index=device_index,
        frames_per_buffer=params.blocksize,
        stream_callback=callback
    )

    # Wait for stream to finish.
    while stream.is_active():
        await asyncio.sleep(1.0)

    # Close the stream.
    stream.close()

    # Release PortAudio system resources.
    pa.terminate()
