import logging

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import MessageService
from aerith_cbot.services.abstractions.models import ChatType, InputMessage
from aerith_cbot.services.abstractions.processors import PrivateMessageProcessor
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.services.implementations.message_queue import MessageQueue


class DefaultPrivateMessageProcessor(PrivateMessageProcessor):
    def __init__(
        self,
        db_session: AsyncSession,
        message_service: MessageService,
        llm_config: LLMConfig,
        message_queue: MessageQueue,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._db_session = db_session
        self._message_service = message_service
        self._llm_config = llm_config
        self._message_queue = message_queue

    async def process(self, message: InputMessage) -> None:
        chat_state = await self._db_session.get(ChatState, message.chat.id)

        if chat_state is None:
            self._logger.info("Adding new chat_state: %s", message.chat.id)

            chat_state = ChatState(chat_id=message.chat.id)
            self._db_session.add(chat_state)
            await self._db_session.commit()

        old_messages: list[dict] = await self._message_service.fetch_messages(message.chat.id)
        new_messages: list[dict] = []

        if not old_messages:
            new_messages.append(
                {"role": "developer", "content": self._llm_config.private_instruction}
            )

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

        new_messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

        self._message_queue.add(message.chat.id, ChatType.private, new_messages)
