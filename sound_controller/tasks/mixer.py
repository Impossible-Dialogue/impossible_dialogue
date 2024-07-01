

async def orientation_mixer(input_queue1, input_queue2, state, output_queue):
    """Generator that fills output_queue with blocks of audio data as NumPy arrays.
    
    It generates the audio by mixing two input streams based on the head orientation.

    """

    while True:
        fraction = abs(state.orientation / 180.0)
        data1 = await input_queue1.get()
        data2 = await input_queue2.get()
        out = (1.0 - head_diff_fraction) * data1 + (head_diff_fraction) * data2
        await output_queue.put(out)


async def master_mixer(input_queues, output_queue, params):
    """Generator that fills q_out with blocks of audio data as NumPy arrays.
    
    It generates the audio by averaging all input streams.

    """
    while True:
        # Get a block of audio data from each stream.
        stream_data = np.ndarray(
            (len(input_streams), params.blocksize, params.channels), dtype='float32')
        for (i, stream) in enumerate(input_queues):
            data = await stream.get()
            stream_data[i, :] = data

        # Sum audio blocks.
        out = stream_data.sum(axis=0)
        await output_queue.put(out)
