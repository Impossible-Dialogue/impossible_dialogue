

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


async def multichannel_mix(input_channels, output_channel, done_event=None):
    try:
        while True:
            # Get a block of audio data from each active channel.    
            for channel in input_channels:
                data = await stream.get()
                stream_data[i, :] = data

            # Sum audio blocks.
            out = stream_data.sum(axis=0)
            await output_queue.put(out)
    except asyncio.CancelledError:
        logging.info('Received a request to cancel')
    finally:
        if done_event:
            done_event.set()
