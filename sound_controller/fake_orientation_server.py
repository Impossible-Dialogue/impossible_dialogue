import argparse
import asyncio
import json
import logging
import sys
import websockets
import traceback


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s,%(msecs)d %(filename)s(%(lineno)d) %(funcName)s: %(message)s",
    datefmt="%H:%M:%S",
)

values = {}

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-r', '--get_server_port', type=int, default=7891, help='Port of the get WS server')
parser.add_argument(
    '-c', '--set_server_port', type=int, default=7892, help='Port of the set WS server')
args, remaining = parser.parse_known_args()


async def get_server():
    async def serve_handler(ws):
        while True:
            try:
                global values
                topic = await ws.recv()
                if topic in values:
                    await ws.send(str(values[topic]))
                else:
                    await ws.send("")
            except Exception as exc:
                logging.error(f'Websocket Error: {exc}')
                print(traceback.format_exc())
                break

    logging.info(f"Starting get_server at port {args.get_server_port}")
    async with websockets.serve(serve_handler, '0.0.0.0', args.get_server_port) as ws:
        await asyncio.Future()


async def set_server():
    async def serve_handler(ws):
        while True:
            try:
                global values
                res = await ws.recv()
                data = json.loads(res)
                topic = data["topic"]
                value = data["value"]
                values[topic] = value
                logging.info(f"Setting {topic} to {value}")
            except Exception as exc:
                logging.error(f'Websocket Error: {exc}')
                break

    logging.info(f"Starting set_server at port {args.get_server_port}")
    async with websockets.serve(serve_handler, '0.0.0.0', args.set_server_port) as ws:
        await asyncio.Future()


async def main(** kwargs):
    futures = [
        get_server(),
        set_server()
    ]
    # Wait forever
    try:
        results = await asyncio.gather(
            *futures,
            return_exceptions=False
        )
        print(results)
    except Exception as e:
        logging.error('An exception has occured.')
        print(traceback.format_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')
