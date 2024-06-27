#!/usr/bin/env python3
"""A test script that uses pyaudio and asyncio generators for blocks of audio data.

You need Python 3.7 or newer to run this.

"""
import argparse
import asyncio
import json
import queue
import sys
import traceback

import numpy as np
import pyaudio
import soundfile as sf
import websockets


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


pa = pyaudio.PyAudio()
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    for i in range(pa.get_device_count()):
        print(pa.get_device_info_by_index(i))
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-r', '--samplerate', type=int, default=48000, help='sampling rate')
parser.add_argument(
    '-c', '--channels', type=int, default=2, help='number of input channels')
parser.add_argument(
    '-b', '--blocksize', type=int, default=512,
    help='block size (default: %(default)s)')
parser.add_argument(
    '-q', '--buffersize', type=int, default=100,
    help='number of blocks used for buffering (default: %(default)s)')
parser.add_argument(
    '-p', '--ws_port', type=int, default=5680,
    help='websocket port (default: %(default)s)')
args = parser.parse_args(remaining)
if args.blocksize == 0:
    parser.error('blocksize must not be zero')
if args.buffersize < 1:
    parser.error('buffersize must be at least 1')
args = parser.parse_args(remaining)

head_orientations = {}
imu_orientation_channel = "imu/head_orientation"
head_orientations_ws_url = "ws://10.10.3.10:7891"
noise_volume = 1.0

async def orientation_ws_client(head_id, url):
    poll_interval = 0.1  # In seconds
    reconnect_interval = 5.0  # In seconds
    while True:
        try:
            imu_ws = await websockets.connect(url)
            print(f'Connected to orientation WS server for {head_id} at {url}')
            
        except Exception as exc:
            print(f'Couldnt connect to orientation WS server for {head_id} at {url}: {exc}')
            await asyncio.sleep(reconnect_interval)
            continue

        while True:
            if imu_ws.closed: 
                print(f'Websocket connection for {head_id} to {url} closed. Reconnecting in {reconnect_interval} seconds.')
                break

            try:
                await imu_ws.send(imu_orientation_channel)
                res = await imu_ws.recv()
                head_orientations[head_id] = float(res)
                print(head_orientations[head_id])
            except Exception as exc:
                print(f'Websocket Error: {exc}')
            await asyncio.sleep(poll_interval)

        await asyncio.sleep(reconnect_interval)


async def orientation_threejs_client():
    """Updates head_state with data received from a websocket connection."""
    while True:
        # Handler for receiving head_state updates from an active WebSocket connection.
        async def serve_handler(ws):
            poll_interval = 0.1  # In seconds
            while True:
                try:
                    await ws.send('head_state')
                    res = await ws.recv()
                    global head_orientations
                    head_state = json.loads(res)
                    for head in head_state["heads"]:
                        diff = head["orientation"] - head["center"]
                        if diff > 180.0:
                            diff = diff - 360.0
                        if diff < -180.0:
                            diff = diff + 360.0
                        head_orientations[head["id"]] = abs(diff)
                except Exception as exc:
                    print(f'Websocket Error: {exc}')
                await asyncio.sleep(poll_interval)


        async with websockets.serve(serve_handler, '0.0.0.0', args.ws_port) as ws:
            await asyncio.Future()


async def inputstream_generator(q_out, filename, volume=1.0):
    """Generator that fills q_out with blocks of input data as NumPy arrays read from a sound file."""
    while True:
        with sf.SoundFile(filename) as f:
            for block in f.blocks(blocksize=args.blocksize, dtype='float32'):
                if f.channels == 1:
                    block = np.column_stack([block, block])
                if len(block) < args.blocksize:
                    break
                if volume != 1.0:
                    block = block * volume
                await q_out.put(block)


async def headmixer_generator(q_out, input_stream1, input_stream2, head_id):
    """Generator that fills q_out with blocks of audio data as NumPy arrays.
    
    It generates the audio by mixing two input streams based on the head orientation.

    """
    stream_data = np.ndarray(
        (2, args.blocksize, args.channels), dtype='float32')
    while True:
        global head_orientations
        orientation = head_orientations[head_id]
        head_diff_fraction = abs(orientation / 180.0)

        data = await input_stream1.get()
        stream_data[0, :] = (1.0 - head_diff_fraction) * data
        data = await input_stream2.get()
        stream_data[1, :] = (head_diff_fraction) * data

        # Sum audio blocks.
        out = stream_data.sum(axis=0)
        await q_out.put(out)


async def mastermixer_generator(q_out, input_streams):
    """Generator that fills q_out with blocks of audio data as NumPy arrays.
    
    It generates the audio by averaging all input streams.

    """
    stream_data = np.ndarray(
        (len(input_streams), args.blocksize, args.channels), dtype='float32')
    while True:
        # Get a block of audio data from each stream.
        for (i, stream) in enumerate(input_streams):
            data = await stream.get()
            stream_data[i, :] = data

        # Average audio blocks.
        out = stream_data.sum(axis=0)
        await q_out.put(out)


async def outputstream_generator(q_in, device_index):
    """Generator that streams blocks of audio data to a PyAudio output stream."""

    def callback(in_data, frame_count, time_info, status):
        assert frame_count == args.blocksize
        try:
            data = q_in.get_nowait()
        except asyncio.QueueEmpty:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            data = np.zeros((args.blocksize, args.channels), dtype='float32')
        return (data, pyaudio.paContinue)

    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=args.channels,
        rate=args.samplerate,
        output=True,
        output_device_index=device_index,
        frames_per_buffer=args.blocksize,
        stream_callback=callback
    )

    # Wait for stream to finish.
    while stream.is_active():
        await asyncio.sleep(1.0)

    # Close the stream.
    stream.close()

    # Release PortAudio system resources.
    pa.terminate()


async def main(** kwargs):
    head1_audio = asyncio.Queue(maxsize=args.buffersize)
    head1_noise = asyncio.Queue(maxsize=args.buffersize)
    head1_mix = asyncio.Queue(maxsize=args.buffersize)
    head2_audio = asyncio.Queue(maxsize=args.buffersize)
    head2_noise = asyncio.Queue(maxsize=args.buffersize)
    head2_mix = asyncio.Queue(maxsize=args.buffersize)
    head3_audio = asyncio.Queue(maxsize=args.buffersize)
    head3_noise = asyncio.Queue(maxsize=args.buffersize)
    head3_mix = asyncio.Queue(maxsize=args.buffersize)
    head4_audio = asyncio.Queue(maxsize=args.buffersize)
    head4_noise = asyncio.Queue(maxsize=args.buffersize)
    head4_mix = asyncio.Queue(maxsize=args.buffersize)
    head5_audio = asyncio.Queue(maxsize=args.buffersize)
    head5_noise = asyncio.Queue(maxsize=args.buffersize)
    head5_mix = asyncio.Queue(maxsize=args.buffersize)
    head6_audio = asyncio.Queue(maxsize=args.buffersize)
    head6_noise = asyncio.Queue(maxsize=args.buffersize)
    head6_mix = asyncio.Queue(maxsize=args.buffersize)
    master_mix = asyncio.Queue(maxsize=args.buffersize)

    # Pre-fill head-orientations.
    for head_id in ["head_1", "head_2", "head_3", "head_4", "head_5", "head_6"]:
        head_orientations[head_id] = 180.0
    head_orientations["head_1"] = 0.0

    futures = [
        orientation_ws_client('head_1', head_orientations_ws_url),
        # orientation_ws_client('head_2', head_orientations_ws_url),
        # orientation_ws_client('head_3', head_orientations_ws_url),
        # orientation_ws_client('head_4', head_orientations_ws_url),
        # orientation_ws_client('head_5', head_orientations_ws_url),
        # orientation_ws_client('head_6', head_orientations_ws_url),
        # orientation_threejs_client(),
        inputstream_generator(
            head1_audio, 'media/sampler/head_1.wav'),
        inputstream_generator(
            head1_noise, 'media/sampler/noise_1.wav', volume=noise_volume),
        headmixer_generator(head1_mix, head1_audio, head1_noise, 'head_1'),
        inputstream_generator(
            head2_audio, 'media/sampler/head_2.wav'),
        inputstream_generator(
            head2_noise, 'media/sampler/noise_2.wav', volume=noise_volume),
        headmixer_generator(head2_mix, head2_audio, head2_noise, 'head_2'),
        inputstream_generator(
            head3_audio, 'media/sampler/head_3.wav'),
        inputstream_generator(
            head3_noise, 'media/sampler/noise_3.wav', volume=noise_volume),
        headmixer_generator(head3_mix, head3_audio, head3_noise, 'head_3'),
        inputstream_generator(
            head4_audio, 'media/sampler/head_4.wav'),
        inputstream_generator(
            head4_noise, 'media/sampler/noise_4.wav', volume=noise_volume),
        headmixer_generator(head4_mix, head4_audio, head4_noise, 'head_4'),
        inputstream_generator(
            head5_audio, 'media/sampler/head_5.wav'),
        inputstream_generator(
            head5_noise, 'media/sampler/noise_5.wav', volume=noise_volume),
        headmixer_generator(head5_mix, head5_audio, head5_noise, 'head_5'),
        inputstream_generator(
            head6_audio, 'media/sampler/head_6.wav'),
        inputstream_generator(
            head6_noise, 'media/sampler/noise_6.wav', volume=noise_volume),
        headmixer_generator(head6_mix, head6_audio, head6_noise, 'head_6'),
        mastermixer_generator(
            master_mix, [head1_mix, head2_mix, head3_mix, head4_mix, head5_mix, head6_mix]),
        outputstream_generator(master_mix, None),
    ]

    # Wait forever
    try:
        results = await asyncio.gather(
            *futures,
            return_exceptions=False
        )
        print(results)
    except Exception as e:
        print('An exception has occured.')
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
