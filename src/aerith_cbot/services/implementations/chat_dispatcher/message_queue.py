import copy
import logging
import random
import time

from aerith_cbot.services.abstractions.models import ChatType


class LocalQueueEntry:
    def __init__(self, chat_id: int, chat_type: ChatType, messages: list[dict]) -> None:
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.messages = messages
        self.last_updated = time.time()

    def __repr__(self) -> str:
        return f"{self.chat_id}/{self.chat_type}/{self.last_updated}: {self.messages}"


class MessageQueue:
    TIME_LIMIT_UPPER_BOUND = 4
    COUNT_LIMIT = 4

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._local_entries: dict[int, LocalQueueEntry] = {}

    def add(self, chat_id: int, chat_type: ChatType, messages: list[dict]) -> None:
        self._logger.debug("Addding new messages in %s/%s chat: %s", chat_id, chat_type, messages)

        if chat_id not in self._local_entries:
            self._local_entries[chat_id] = LocalQueueEntry(chat_id, chat_type, messages)
        else:
            self._local_entries[chat_id].last_updated = time.time()
            self._local_entries[chat_id].messages.extend(messages)

    def fetch_ready_entries(self) -> list[LocalQueueEntry]:
        ready_entries = []
        current_time = time.time()

        for chat_id, entry in self._local_entries.items():
            if entry.messages and (
                current_time - entry.last_updated
                > random.randint(0, MessageQueue.TIME_LIMIT_UPPER_BOUND)
                or len(entry.messages) > MessageQueue.COUNT_LIMIT
            ):
                ready_entries.append(copy.deepcopy(entry))

        return ready_entries

    def clear(self, chat_id: int) -> None:
        self._logger.debug("Clearing message_queue for chat %s", chat_id)

        if chat_id in self._local_entries:
            self._local_entries[chat_id].messages.clear()
