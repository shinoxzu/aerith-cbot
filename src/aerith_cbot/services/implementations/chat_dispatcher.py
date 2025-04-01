import asyncio
import logging

from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncEngine

from aerith_cbot.services.abstractions import MessageService
from aerith_cbot.services.abstractions.processors import ChatProcessor
from aerith_cbot.services.implementations.message_queue import (
    LocalQueueEntry,
    MessageQueue,
)


class ChatDispatcher:
    def __init__(
        self,
        db_engine: AsyncEngine,
        message_queue: MessageQueue,
        container: AsyncContainer,
    ) -> None:
        self._db_engine = db_engine
        self._message_queue = message_queue
        self._container = container

        self._logger = logging.getLogger(__name__)
        self._working_chats: dict[int, bool] = {}
        self._bg_tasks: list[asyncio.Task] = []

        self.run_task: asyncio.Task | None = None

    async def run(self) -> None:
        while True:
            try:
                entries_to_handle = self._message_queue.fetch_ready_entries()

                self._logger.debug("Handling %s ready entries", len(entries_to_handle))

                for entry in entries_to_handle:
                    if (
                        entry.chat_id not in self._working_chats
                        or not self._working_chats[entry.chat_id]
                    ):
                        self._message_queue.clear(entry.chat_id)

                        coro = self.handle_entry(entry.chat_id, entry)
                        task = asyncio.create_task(coro)

                        task.add_done_callback(self._bg_tasks.remove)
                        self._bg_tasks.append(task)
            except Exception as err:
                self._logger.error("Cannot handle entries cause of %s", err, exc_info=err)
            finally:
                await asyncio.sleep(1)

    async def handle_entry(self, chat_id: int, entry: LocalQueueEntry) -> None:
        self._logger.debug("Running chat processing for %s: %s", chat_id, entry)

        self._working_chats[chat_id] = True

        try:
            async with self._container() as container:
                # TODO: перед добавлением этих сообщений проверять, сфокусирован ли чат или уже нет
                message_service = await container.get(MessageService)
                await message_service.add_messages(chat_id, entry.messages)

                processor = await container.get(ChatProcessor)
                await processor.process(chat_id, entry.chat_type)
        except Exception as err:
            self._logger.error(
                "Cannot handle messages for %s cause of %s", chat_id, err, exc_info=err
            )
        finally:
            self._working_chats[chat_id] = False
