import asyncio
import logging

from dishka import AsyncContainer

from aerith_cbot.services.abstractions import SupportService


class SupportNotifier:
    NOTIFY_MINTERVAL = 43_200

    def __init__(self, container: AsyncContainer) -> None:
        self._container = container

        self._logger = logging.getLogger(__name__)

        self.run_task: asyncio.Task | None = None

    async def run(self) -> None:
        while True:
            try:
                async with self._container() as container:
                    support_service = await container.get(SupportService)
                    await support_service.notify_users_to_prolong()
            except Exception as err:
                self._logger.error("Cannot send prolong message cause of %s", err, exc_info=err)
            finally:
                await asyncio.sleep(SupportNotifier.NOTIFY_MINTERVAL)
