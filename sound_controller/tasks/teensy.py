import asyncio
import logging
import websockets


async def poll_orientation(url, topic, head_state, poll_interval=0.1, reconnect_interval=5.0):
    """Polls a websockets server at url with topic. Stores the received data in the orientations dictionary."""

    while True:
        try:
            connection = await websockets.connect(url)
            logging.info(f'Connected to orientation WS server at {url}')

        except Exception as exc:
            logging.error(
                f'Couldnt connect to orientation WS server at {url}: {exc}')
            await asyncio.sleep(reconnect_interval)
            continue

        while True:
            if connection.closed:
                logging.error(
                    f'Websocket connection to {url} closed. Reconnecting in {reconnect_interval} seconds.')
                break

            try:
                await connection.send(topic)
                res = await connection.recv()
                if res:
                    head_state.set_orientation(float(res))
                else:
                    head_state.set_orientation(0)
            except Exception as exc:
                logging.error(f'Websocket Error: {exc}')
            await asyncio.sleep(poll_interval)

        await asyncio.sleep(reconnect_interval)
