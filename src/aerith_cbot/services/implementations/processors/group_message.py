import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LimitsConfig
from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import LimitsService
from aerith_cbot.services.abstractions.models import ChatType, InputChat, InputMessage
from aerith_cbot.services.abstractions.processors import GroupMessageProcessor
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue


class DefaultGroupMessageProcessor(GroupMessageProcessor):
    def __init__(
        self,
        db_session: AsyncSession,
        message_queue: MessageQueue,
        limits_config: LimitsConfig,
        limits_service: LimitsService,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._db_session = db_session
        self._message_queue = message_queue
        self._limits_config = limits_config
        self._limits_service = limits_service

    async def process(self, message: InputMessage) -> None:
        chat_state = await self._create_of_fetch_chat_state(message.chat)

        # if chat is inactive for now cause of limits
        if chat_state.sleeping_till > int(time.time()):
            self._logger.info("Ignoring message cause sleeping from chat: %s", message.chat)

            # TODO: send message "я занята, так что давай позже..."

            return

        can_use = await self._limits_service.check_group_limit(message.sender.id, message.chat.id)

        if not chat_state.is_focused:
            self._logger.debug("Message from unfocused chat: %s", message.chat.id)

            if not can_use:
                self._logger.info("Chat %s has used its limit; byeing", message.chat.id)

                chat_state.sleeping_till = int(time.time()) + self._limits_config.private_cooldown
                await self._db_session.commit()

                # TODO: send message "я занята, так что давай позже..."

                return

            if message.contains_aerith_mention:
                self._logger.info("Chat %s is focused now; processing message", message.chat.id)

                chat_state.ignoring_streak = 0
                chat_state.listening_streak = 0
                chat_state.is_focused = True

                await self._db_session.commit()
            else:
                return

        new_messages = []

        # if there are no tokens available, we say goodbye to the user
        # also we make chat inactive by setting sleeping_till property
        if not can_use:
            self._logger.info("Chat %s has used its limit; byeing", message.chat.id)

            chat_state.is_focused = False
            chat_state.sleeping_till = int(time.time()) + self._limits_config.private_cooldown

            await self._db_session.commit()

            new_messages: list[dict] = [
                {
                    "role": "system",
                    "content": "В группе лимит на общение с тобой. Извинись и сообщи, что тебе пора.",
                }
            ]
        else:
            new_messages: list[dict] = []

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
        self._message_queue.add(message.chat.id, ChatType.group, new_messages)

    async def _create_of_fetch_chat_state(self, chat: InputChat) -> ChatState:
        chat_state = await self._db_session.get(ChatState, chat.id)
        if chat_state is None:
            self._logger.debug("Adding new chat_state for chat: %s", chat)

            chat_state = ChatState(chat_id=chat.id, sleeping_till=0, is_focused=False)
            self._db_session.add(chat_state)
            await self._db_session.commit()

        return chat_state
