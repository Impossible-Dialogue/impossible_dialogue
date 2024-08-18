import asyncio
import logging
import websockets


class StateUpdater:
    def __init__(self, state, config):
        self._state = state
        self._config = config

    async def _poll_orientation(self, url, topic, state, head_id, poll_interval=0.1, reconnect_interval=5.0):
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
                        state.set_head_orientation(head_id, float(res))
                    else:
                        state.set_head_orientation(head_id, 0)
                except Exception as exc:
                    logging.error(f'Websocket Error: {exc}')
                await asyncio.sleep(poll_interval)

            await asyncio.sleep(reconnect_interval)
        
    async def run(self):
        tasks = []
        for head_config in self._config["heads"]:
            id = head_config["id"]
            tasks.append(asyncio.create_task(self._poll_orientation(
                url="ws://localhost:7891",
                topic=f"{id}/orientation",
                state=self._state,
                head_id=id)))
        await asyncio.gather(
            *tasks,
            return_exceptions=False
        )
