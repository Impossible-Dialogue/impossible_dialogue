import argparse
import asyncio
import json
import logging
import sys
import websockets
import traceback

from impossible_dialogue.state import InstallationState



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
parser.add_argument("--config", type=argparse.FileType('r'), default="../config/head_config.json",
                    help="Sound config file")
args, remaining = parser.parse_known_args()


def set_value(topic, value):
    global values
    values[topic] = value
    logging.debug(f"Setting {topic} to {value}")


async def poll_orientation(url, topic, state, head_id, poll_interval=0.1, reconnect_interval=5.0):
    """Polls a websockets server at url with topic. Stores the received data in the orientations dictionary."""
    global values
    while True:
        try:
            connection = await websockets.connect(url)
            logging.info(f'Connected to orientation WS server at {url}')
            set_value(f"{head_id}/connected", True)


        except Exception as exc:
            logging.error(
                f'Couldnt connect to orientation WS server at {url}: {exc}')
            await asyncio.sleep(reconnect_interval)
            continue

        while True:
            if connection.closed:
                logging.error(
                    f'Websocket connection to {url} closed. Reconnecting in {reconnect_interval} seconds.')
                set_value(f"{head_id}/connected", False)
                break

            try:
                await connection.send(topic)
                res = await connection.recv()
                if res:
                    set_value(f"{head_id}/orientation", float(res))
                    state.set_head_orientation(head_id, float(res))
                else:
                    set_value(f"{head_id}/orientation", 0)
                    state.set_head_orientation(head_id, 0)
            except Exception as exc:
                logging.error(f'Websocket Error: {exc}')
            await asyncio.sleep(poll_interval)

        await asyncio.sleep(reconnect_interval)


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
    config = json.load(args.config)
    state = InstallationState(config)
    for head_config in config["heads"]:
        id = head_config["id"]
        set_value(f"{id}/connected", False)
        if "orientation_ws_url" in head_config:
            futures.append(asyncio.create_task(poll_orientation(
                url=head_config["orientation_ws_url"], 
                topic=head_config["orientation_topic"],
                state=state,
                head_id=id)))
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
