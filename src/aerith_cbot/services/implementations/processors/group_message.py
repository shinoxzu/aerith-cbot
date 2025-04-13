import logging
import time

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LimitsConfig, LLMConfig
from aerith_cbot.database.models import ChatState, UserGroupLastContact
from aerith_cbot.services.abstractions import LimitsService, SenderService, VoiceTranscriber
from aerith_cbot.services.abstractions.models import ChatType, InputChat, InputMessage
from aerith_cbot.services.abstractions.processors import GroupMessageProcessor
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue


class DefaultGroupMessageProcessor(GroupMessageProcessor):
    IGNORED_MESSAGE_MIN_INTERVAL = 1800
    MAX_LAST_CONTACT_TIME = 3600

    def __init__(
        self,
        db_session: AsyncSession,
        message_queue: MessageQueue,
        limits_config: LimitsConfig,
        limits_service: LimitsService,
        llm_config: LLMConfig,
        sender_service: SenderService,
        voice_transcriber: VoiceTranscriber,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._db_session = db_session
        self._message_queue = message_queue
        self._limits_config = limits_config
        self._limits_service = limits_service
        self._llm_config = llm_config
        self._sender_service = sender_service
        self._voice_transcriber = voice_transcriber

    async def process(self, message: InputMessage) -> None:
        chat_state = await self._create_of_fetch_chat_state(message.chat)

        # if chat is inactive for now cause of limits
        if chat_state.sleeping_till > int(time.time()):
            if message.contains_aerith_mention:
                if (
                    time.time() - chat_state.last_ignored_answer
                    > DefaultGroupMessageProcessor.IGNORED_MESSAGE_MIN_INTERVAL
                ):
                    await self._sender_service.send_ignoring(message.chat.id)

                    chat_state.last_ignored_answer = int(time.time())
                    await self._db_session.commit()

            self._logger.debug(
                "Ignoring message cause sleeping (to %s) from chat: %s",
                chat_state.sleeping_till,
                message.chat,
            )

            return

        new_messages: list[dict] = []

        can_use = await self._limits_service.check_group_limit(message.sender.id, message.chat.id)

        if not chat_state.is_focused:
            self._logger.debug("Message from unfocused chat: %s", message.chat.id)

            if not message.contains_aerith_mention:
                return

            if not can_use:
                self._logger.info("Chat %s has used its limit; byeing", message.chat.id)

                chat_state.sleeping_till = int(time.time()) + self._limits_config.private_cooldown

                if (
                    time.time() - chat_state.last_ignored_answer
                    > DefaultGroupMessageProcessor.IGNORED_MESSAGE_MIN_INTERVAL
                ):
                    await self._sender_service.send_ignoring(message.chat.id)

                    chat_state.last_ignored_answer = int(time.time())

                await self._db_session.commit()
                return

            else:
                self._logger.info("Chat %s is focused now; processing message", message.chat.id)

                chat_state.ignoring_streak = 0
                chat_state.is_focused = True

                await self._db_session.commit()

                new_messages.append(
                    {
                        "role": "system",
                        "content": self._llm_config.additional_instructions.aerith_has_mentioned,
                    }
                )
        # chat is focused and last message here chat was too long time ago, we unfocus it
        else:
            is_last_contact_too_long = await self._if_last_contact_too_long(message.chat.id)
            if is_last_contact_too_long:
                self._logger.info(
                    "Chat %s was active too long ago so we unfocus it", message.chat.id
                )

                chat_state.is_focused = False
                await self._db_session.commit()

                return

        # if there are no tokens available, we say goodbye to the user
        # also we make chat inactive by setting sleeping_till property
        if not can_use:
            self._logger.info("Chat %s has used its limit; byeing", message.chat.id)

            chat_state.is_focused = False
            chat_state.sleeping_till = int(time.time()) + self._limits_config.private_cooldown

            await self._db_session.commit()

            new_messages.append(
                {
                    "role": "system",
                    "content": self._llm_config.additional_instructions.limit_in_group,
                }
            )

        content = []
        if message.photo_url is not None:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": message.photo_url, "detail": "low"},
                }
            )

        model_input_message = await input_msg_to_model_input(message, self._voice_transcriber)
        content.append(
            {
                "type": "text",
                "text": model_input_message.model_dump_json(exclude_none=True),
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

    async def _if_last_contact_too_long(self, chat_id) -> bool:
        stmt = (
            select(UserGroupLastContact.last_contacted_time)
            .where(UserGroupLastContact.chat_id == chat_id)
            .order_by(desc(UserGroupLastContact.last_contacted_time))
            .limit(1)
        )
        result = await self._db_session.scalar(stmt)
        return (
            result is None
            or int(time.time()) - result > DefaultGroupMessageProcessor.MAX_LAST_CONTACT_TIME
        )
