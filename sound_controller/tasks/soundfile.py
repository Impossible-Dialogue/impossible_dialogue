import asyncio
import numpy as np
import soundfile as sf


async def read_soundfile(filename, output_queue, done_even=None, blocksize=512, volume=1.0, loop=False):
    """Reads a sound file from filename and fills output_queue with blocks of sound data."""
    try:
        while True:
            with sf.SoundFile(filename) as f:
                for block in f.blocks(blocksize=blocksize, dtype='float32'):
                    if f.channels == 1:
                        block = np.column_stack([block, block])
                    if len(block) < blocksize:
                        break
                    if volume != 1.0:
                        block = block * volume
                    await output_queue.put(block)
                if not loop: 
                    break
    except asyncio.CancelledError:
        print('Received a request to cancel')
    finally:
        if done_event:
            done_event.set()

