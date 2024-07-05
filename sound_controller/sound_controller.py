#!/usr/bin/env python3
"""A test script that uses pyaudio and asyncio generators for blocks of audio data.

You need Python 3.7 or newer to run this.

"""
import argparse
import asyncio
import json
import logging
import sys
import traceback

import numpy as np

from core.state import InstallationState
from core.state_updater import StateUpdater
from producer.producer import Producer


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s,%(msecs)d %(filename)s(%(lineno)d) %(funcName)s: %(message)s",
    datefmt="%H:%M:%S",
)


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-c", "--config", type=argparse.FileType('r'), default="sound_config.json",
                    help="Sound config file")
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
args = parser.parse_args(remaining)

async def main(** kwargs):
    
    if args.list_devices:
        import pyaudio
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            print(pa.get_device_info_by_index(i))
        return

    config = json.load(args.config)
    state = InstallationState(config)
    updater = StateUpdater(state, config)
    producer = Producer(state, config)
    tasks = [
        updater.run(),
        producer.run(),
    ]

    # Wait forever
    try:
        results = await asyncio.gather(
            *tasks,
            return_exceptions=False
        )
    except Exception as e:
        print('A sound controller exception has occured.')
        print(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
