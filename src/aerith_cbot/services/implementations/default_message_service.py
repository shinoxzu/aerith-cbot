import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import Message
from aerith_cbot.services.abstractions import HistorySummarizer, MessageService


class DefaultMessageService(MessageService):
    def __init__(self, db_session: AsyncSession, history_summarizer: HistorySummarizer) -> None:
        super().__init__()

        self._db_session = db_session
        self._history_summarizer = history_summarizer
        self._logger = logging.getLogger(__name__)

    async def fetch_messages(self, chat_id: int) -> list[dict]:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.id)
        old_messages_raw = await self._db_session.execute(stmt)

        return [om.data for om in old_messages_raw.scalars()]

    async def add_messages(self, chat_id: int, messages: list[dict]) -> None:
        self._db_session.add_all([Message(chat_id=chat_id, data=md) for md in messages])
        await self._db_session.commit()

    async def shorten_history(self, chat_id: int) -> None:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.id)
        messages_raw = await self._db_session.execute(stmt)
        messages: list[Message] = list(messages_raw.scalars())

        # the problem is messages with 'tool' role must be a response to messages
        messages_to_summarize: list[Message] = messages[: len(messages) // 2]
        for ci in range(len(messages) // 2, len(messages)):
            if messages[ci].data["role"] == "tool" or ("tool_calls" in messages[ci].data):
                messages_to_summarize.append(messages[ci])
            else:
                break

        summarize_result = await self._history_summarizer.summarize(
            [msg.data for msg in messages_to_summarize]
        )

        self._logger.info("Summarize result in %s is:\n%s", chat_id, summarize_result)

        # edit first message
        message_to_edit_id = messages_to_summarize[0].id
        stmt = (
            update(Message)
            .where(Message.id == message_to_edit_id)
            .values(data={"role": "assistant", "content": summarize_result})
        )
        await self._db_session.execute(stmt)

        # delete other messages
        message_to_delete_ids = [msg.id for msg in messages_to_summarize[1:]]
        stmt = delete(Message).where(Message.id.in_(message_to_delete_ids))
        await self._db_session.execute(stmt)

        await self._db_session.commit()

    async def shorten_full_history_without_media(self, chat_id: int) -> None:
        stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.id)
        messages_raw = await self._db_session.execute(stmt)
        messages_to_summarize: list[Message] = list(messages_raw.scalars())

        messages_data_to_summarize = []
        for message in messages_to_summarize:
            if type(message.data["content"]) is str:
                messages_data_to_summarize.append(message.data)
            if type(message.data["content"]) is list:
                for content in message.data["content"]:
                    if content["type"] != "text":
                        break
                else:
                    messages_data_to_summarize.append(message.data)

        summarize_result = await self._history_summarizer.summarize(messages_data_to_summarize)

        self._logger.info("Summarize result in %s is:\n%s", chat_id, summarize_result)

        # edit first message
        message_to_edit_id = messages_to_summarize[0].id
        stmt = (
            update(Message)
            .where(Message.id == message_to_edit_id)
            .values(data={"role": "assistant", "content": summarize_result})
        )
        await self._db_session.execute(stmt)

        # delete other messages
        message_to_delete_ids = [msg.id for msg in messages_to_summarize[1:]]
        stmt = delete(Message).where(Message.id.in_(message_to_delete_ids))
        await self._db_session.execute(stmt)

        await self._db_session.commit()

    async def clear(self, chat_id: int) -> None:
        stmt = delete(Message).where(Message.chat_id == chat_id)
        await self._db_session.execute(stmt)
        await self._db_session.commit()
