import asyncio
import websockets


async def poll_orientation(id, url, topic, orientations, poll_interval=0.1, reconnect_interval=5.0):
    """Polls a websockets server at url with topic. Stores the received data in the orientations dictionary."""

    while True:
        try:
            connection = await websockets.connect(url)
            print(f'Connected to orientation WS server for {id} at {url}')

        except Exception as exc:
            print(
                f'Couldnt connect to orientation WS server for {id} at {url}: {exc}')
            await asyncio.sleep(reconnect_interval)
            continue

        while True:
            if connection.closed:
                print(
                    f'Websocket connection for {id} to {url} closed. Reconnecting in {reconnect_interval} seconds.')
                break

            try:
                await connection.send(topic)
                res = await connection.recv()
                orientations[id] = float(res)
            except Exception as exc:
                print(f'Websocket Error: {exc}')
            await asyncio.sleep(poll_interval)

        await asyncio.sleep(reconnect_interval)
