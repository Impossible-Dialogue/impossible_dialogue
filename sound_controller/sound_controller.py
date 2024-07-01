#!/usr/bin/env python3
"""A test script that uses pyaudio and asyncio generators for blocks of audio data.

You need Python 3.7 or newer to run this.

"""
import argparse
import asyncio
import json
import logging
import queue
import sys
import traceback

import numpy as np

import websockets

from tasks.teensy import poll_orientation
from tasks.soundfile import read_soundfile
from tasks.mixer import orientation_mixer, master_mixer
from tasks.pyaudio import pyaudio_output


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
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

orientations = {}
orientation_topic = "imu/head_orientation"
orientation_url = "ws://10.10.3.10:7891"
noise_volume = 1.0


class Mixer:
    def __init__(self, output_queue, params):
        self.input_queues = []
        self.output_queue = output_queue
        self.params = params
        self.lock

    def play_track(self, filename):
        queue = asyncio.Queue()
        task = asyncio.create_task(read_soundfile(filename, queue))
        with lock:
            self.input_queues[task] = queue
        return task

    def stop_track(self, task):
        task.cancel()

    async def run(self):
        while True:
            
            with lock:
                # Get a block of audio data from each stream.
                stream_data = np.ndarray(
                    (len(input_queues), params.blocksize, params.channels), dtype='float32')
                for (i, stream) in enumerate(input_queues):
                    data = await stream.get()
                    stream_data[i, :] = data

                # Sum audio blocks.
                out = stream_data.sum(axis=0)
                await output_queue.put(out)


async def head_producer(output_queue, state, params):
    poll_interval = 0.1
    queues = []
    while True:
        
        play_track
        stop_track

        play_track_sequence(queue)
        stop_track_sequence(queue)


        await asyncio.sleep(poll_interval)


async def main(** kwargs):
    pa = pyaudio.PyAudio()
    if args.list_devices:
        for i in range(pa.get_device_count()):
            print(pa.get_device_info_by_index(i))
        return

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
        orientations[head_id] = 180.0
    orientations["head_1"] = 0.0

    tasks = [
        poll_orientation('head_1', orientation_url,
                         orientation_topic, orientations),
        # orientation_ws_client('head_2', head_orientations_ws_url),
        # orientation_ws_client('head_3', head_orientations_ws_url),
        # orientation_ws_client('head_4', head_orientations_ws_url),
        # orientation_ws_client('head_5', head_orientations_ws_url),
        # orientation_ws_client('head_6', head_orientations_ws_url),
        # orientation_threejs_client(),
        read_soundfile(
            head1_audio, 'media/sampler/head_1.wav'),
        read_soundfile(
            head1_noise, 'media/sampler/noise_1.wav', volume=noise_volume),
        headmixer_generator(head1_mix, head1_audio, head1_noise, 'head_1'),
        read_soundfile(
            head2_audio, 'media/sampler/head_2.wav'),
        read_soundfile(
            head2_noise, 'media/sampler/noise_2.wav', volume=noise_volume),
        headmixer_generator(head2_mix, head2_audio, head2_noise, 'head_2'),
        read_soundfile(
            head3_audio, 'media/sampler/head_3.wav'),
        read_soundfile(
            head3_noise, 'media/sampler/noise_3.wav', volume=noise_volume),
        headmixer_generator(head3_mix, head3_audio, head3_noise, 'head_3'),
        read_soundfile(
            head4_audio, 'media/sampler/head_4.wav'),
        read_soundfile(
            head4_noise, 'media/sampler/noise_4.wav', volume=noise_volume),
        headmixer_generator(head4_mix, head4_audio, head4_noise, 'head_4'),
        read_soundfile(
            head5_audio, 'media/sampler/head_5.wav'),
        read_soundfile(
            head5_noise, 'media/sampler/noise_5.wav', volume=noise_volume),
        headmixer_generator(head5_mix, head5_audio, head5_noise, 'head_5'),
        read_soundfile(
            head6_audio, 'media/sampler/head_6.wav'),
        read_soundfile(
            head6_noise, 'media/sampler/noise_6.wav', volume=noise_volume),
        headmixer_generator(head6_mix, head6_audio, head6_noise, 'head_6'),
        mastermixer_generator(
            master_mix, [head1_mix, head2_mix, head3_mix, head4_mix, head5_mix, head6_mix]),
        outputstream_generator(master_mix, None),
    ]

    # Wait forever
    try:
        results = await asyncio.gather(
            *tasks,
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
