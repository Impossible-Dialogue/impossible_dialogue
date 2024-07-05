import asyncio
import numpy as np
import soundfile as sf


async def read_soundfile(filename, output_stream, channels=2, blocksize=512, volume=1.0, loop=False):
    """Reads a sound file from filename and fills output_queue with blocks of sound data."""
    try:
        while True:
            with sf.SoundFile(filename) as f:
                for block in f.blocks(blocksize=blocksize, dtype='float32'):
                    if channels == 2 and f.channels == 1:
                        block = np.column_stack([block, block])
                    if len(block) < blocksize:
                        break
                    if volume != 1.0:
                        block = block * volume
                    await output_stream.put(block)
                if not loop: 
                    break
    except asyncio.CancelledError:
        print('Received a request to cancel')
