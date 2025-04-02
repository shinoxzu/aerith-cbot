import logging

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions.models import ChatType, InputMessage
from aerith_cbot.services.abstractions.processors import GroupMessageProcessor
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.services.implementations.chat_dispatcher.message_queue import MessageQueue


class DefaultGroupMessageProcessor(GroupMessageProcessor):
    def __init__(
        self,
        db_session: AsyncSession,
        message_queue: MessageQueue,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._db_session = db_session
        self._message_queue = message_queue

    async def process(self, message: InputMessage) -> None:
        chat_state = await self._db_session.get(ChatState, message.chat.id)

        if chat_state is None:
            self._logger.info("Adding new chat_state: %s", message.chat.id)

            # TODO: error can be raised if two tasks add one chat in parallel
            chat_state = ChatState(chat_id=message.chat.id)
            self._db_session.add(chat_state)
            await self._db_session.commit()

        if not chat_state.is_focused:
            self._logger.debug("Message from unfocused chat: %s", message.chat.id)

            if message.contains_aerith_mention:
                self._logger.info("Chat %s is focused now; processing message", message.chat.id)

                chat_state.ignoring_streak = 0
                chat_state.listening_streak = 0
                chat_state.is_focused = True

                await self._db_session.commit()
            else:
                return

        content = []
        if message.photo_url is not None:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": message.photo_url, "detail": "low"},
                }
            )
        content.append(
            {
                "type": "text",
                "text": input_msg_to_model_input(message).model_dump_json(exclude_none=True),
            }
        )

        new_messages = [
            {
                "role": "user",
                "content": content,
            }
        ]
        self._message_queue.add(message.chat.id, ChatType.group, new_messages)
