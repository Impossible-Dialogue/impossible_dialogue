import asyncio

from tasks.teensy import poll_orientation


class StateUpdater:
    def __init__(self, state, config):
        self._state = state
        self._config = config

    async def run(self):
        tasks = []
        for head_config in self._config["heads"]:
            id = head_config["id"]
            tasks.append(asyncio.create_task(poll_orientation(
                url=head_config["orientation_ws_url"], 
                topic=head_config["orientation_topic"],
                head_state=self._state.head_state(id))))
        await asyncio.gather(
            *tasks,
            return_exceptions=False
        )
