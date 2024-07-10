import argparse
import json
import asyncio

import websockets
import traceback

from core.opc import connect_to_opc
from core.pattern_generator import PatternGenerator
from core.websockets import LightControllerWebSocketsServer


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--config", type=argparse.FileType('r'), default="../config/head_config.json", 
                        help="LED config file")
    parser.add_argument("-c", "--enable_cache", action='store_true', default=True,
                        help="Enable pattern caching")
    parser.add_argument("-a", "--animation_rate", type=int, default=20, 
                        help="The target animation rate in Hz")
    parser.add_argument("--websockets_port", type=int, default=5678, 
                        help="The light controler WebSockets port.")
    parser.add_argument("--websockets_host", default="0.0.0.0", 
                        help="The light controler WebSockets host.")
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
    pattern_generator = PatternGenerator(None, config, args)
    futures.append(pattern_generator.run())
    
    # WS servers for the web visualization
    ws = LightControllerWebSocketsServer(pattern_generator, args.websockets_host, args.websockets_port)
    futures.append(ws.run())
  
    loop = asyncio.get_event_loop()
    for o in config['objects']:
        object_id = o['id']
        if 'opc' in o.keys():
            opc = o['opc']
            # Start OPC client
            futures.append(connect_to_opc(loop, object_id, pattern_generator, opc['server_ip'], opc['server_port']))
        if 'imu' in o.keys():
            imu = o['imu']
            url = "ws://" + imu['server_ip'] + ":" + str(imu['server_port'])
            channel = imu['channel'] 
            pattern_selector = pattern_generator.pattern_selectors[object_id]
            pattern_selector.imu_orientation_channel = channel
            # Start IMU websocket client
            futures.append(pattern_selector.orientationWSListener(url))

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
