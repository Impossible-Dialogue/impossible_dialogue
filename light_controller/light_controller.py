import argparse
import json
import logging
import asyncio

import websockets
import traceback
import uvloop

from core.opc import OpenPixelControlConnection
from core.pattern_generator import PatternGenerator
from core.websockets import LightControllerWebSocketsServer
from impossible_dialogue.config import HeadConfigs, FirePitConfig
from impossible_dialogue.state import InstallationState
from impossible_dialogue.state_updater import StateUpdater

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s,%(msecs)d %(filename)s(%(lineno)d) %(funcName)s: %(message)s",
    datefmt="%H:%M:%S",
)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--config", type=argparse.FileType('r'), default="../config/head_config.json", 
                        help="LED config file")
    parser.add_argument("-c", "--enable_cache", action='store_true', default=True,
                        help="Enable pattern caching")
    parser.add_argument("-a", "--animation_rate", type=int, default=20, 
                        help="The target animation rate in Hz")
    parser.add_argument("--enable_websockets", action='store_true', default=True,
                        help="Enable the light controler WebSockets.")
    parser.add_argument("--websockets_port", type=int, default=5678, 
                        help="The light controler WebSockets port.")
    parser.add_argument("--websockets_host", default="0.0.0.0", 
                        help="The light controler WebSockets host.")
    parser.add_argument("--pattern_demo_mode", action='store_true', default=False,
                        help="Rotates through a list of patterns.")

    args = parser.parse_args()

    config = json.load(args.config)
    head_configs = HeadConfigs(config["heads"])
    if "fire_pit" in config:
        fire_pit_config = FirePitConfig(config["fire_pit"])
    else:
        fire_pit_config = None
    state = InstallationState(config)

    tasks = []

    # State updater
    updater = StateUpdater(state, config)
    tasks.append(updater.run())

    # Start pattern generator
    pattern_generator = PatternGenerator(state, config, args)
    tasks.append(pattern_generator.run())
    
    # WS servers for the web visualization
    if args.enable_websockets:
        ws = LightControllerWebSocketsServer(pattern_generator, args.websockets_host, args.websockets_port)
        tasks.append(ws.run())
    
    opc = OpenPixelControlConnection(
        pattern_generator, head_configs, fire_pit_config)
    tasks.append(opc.run())

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

uvloop.run(main())