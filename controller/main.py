import argparse
import json
import time
import sys
import asyncio

import websockets
import functools
import time
import traceback

from funky_lights import connection, messages
from core.opc import OpenPixelControlClient, create_opc_connection
from core.serial import SerialWriter
from core.pattern_generator import PatternGenerator
from core.websockets import TextureWebSocketsServer, PatternMixWebSocketsServer



async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--config", type=argparse.FileType('r'), default="../config/head_config.json", 
                        help="LED config file")
    parser.add_argument("-c", "--enable_cache", action='store_true', 
                        help="Enable pattern caching")
    parser.add_argument("-a", "--animation_rate", type=int, default=20, 
                        help="The target animation rate in Hz")
    parser.add_argument("--ws_port_texture", type=int, default=5678, 
                        help="The WebSockets port for the texture server")
    parser.add_argument("--enable_launchpad", action='store_true', 
                        help="Enables support for a USB launchpad device")
    parser.add_argument("--ws_port_launchpad", type=int, default=5679, 
                        help="The WebSockets port for the launchpad server")
    parser.add_argument("--pattern_rotation_time", type=int, default=600, 
                        help="The maximum duration a pattern is displayed before rotating to the next.")
    parser.add_argument("--enable_pattern_mix_publisher", action='store_true', 
                        help="Enables a WebSockets server to publish the pattern mix")
    parser.add_argument("--pattern_mix_publish_port", type=int, default=5680, 
                        help="The WebSockets port for the pattern mix publisher")
    parser.add_argument("--enable_pattern_mix_subscriber", action='store_true', 
                        help="Enables a WebSockets client to subscribe to a pattern mix")
    parser.add_argument("--pattern_mix_subscribe_uri", default='ws://funkypi.wlan:5680', 
                        help="The WebSockets URI for the pattern mix subscriber")

    args = parser.parse_args()

    config = json.load(args.config)
    
    futures = []

    # Start pattern generator
    pattern_generator = PatternGenerator(args, config)
    futures.append(pattern_generator.run())
    
    # WS servers for the web visualization
    ws_texture = TextureWebSocketsServer(pattern_generator)
    futures.append(websockets.serve(ws_texture.serve,
                   '0.0.0.0', args.ws_port_texture))
    # futures.append(websockets.serve(pattern_selector.launchpadWSListener,
    #                '0.0.0.0', args.ws_port_launchpad))

    # Publisher and subscriber for pattern mix
    if args.enable_pattern_mix_publisher:
        ws_pattern_mix_publish = PatternMixWebSocketsServer(pattern_generator) 
        futures.append(websockets.serve(ws_pattern_mix_publish.serve, '0.0.0.0', args.pattern_mix_publish_port))
    
    # if args.enable_pattern_mix_subscriber:
    #     futures.append(pattern_selector.patternMixWSListener(args.pattern_mix_subscribe_uri))
    
    # Start Open Pixel Control
    loop = asyncio.get_event_loop()
    for o in config['objects']:
        object_id = o['id']
        if not 'opc_connection' in o.keys():
            continue
        connection = o['opc_connection']
        opc_handler = functools.partial(
            OpenPixelControlClient, 
            generator=pattern_generator, 
            object_id=object_id)
        futures.append(create_opc_connection(
            loop, opc_handler, connection['server_ip'], connection['server_port']))
        
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


asyncio.run(main())
