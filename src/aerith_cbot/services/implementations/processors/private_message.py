import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LimitsConfig, LLMConfig
from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import LimitsService, SenderService, VoiceTranscriber
from aerith_cbot.services.abstractions.models import ChatType, InputChat, InputMessage
from aerith_cbot.services.abstractions.processors import PrivateMessageProcessor
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue


class DefaultPrivateMessageProcessor(PrivateMessageProcessor):
    IGNORED_MESSAGE_MIN_INTERVAL = 1800

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
            self._logger.debug(
                "Ignoring message cause sleeping (to %s) from chat: %s",
                chat_state.sleeping_till,
                message.chat,
            )

            await self._send_ignoring_if_needed(chat_state)
            return

        can_use = await self._limits_service.check_private_limit(message.sender.id)

        # if there are no tokens available, we say goodbye to the user
        # also we make chat inactive by setting sleeping_till property
        if not can_use:
            self._logger.info("Chat %s has used its limit; byeing", message.chat.id)

            chat_state.sleeping_till = int(time.time()) + self._limits_config.private_cooldown

            await self._db_session.commit()

            new_messages: list[dict] = [
                {
                    "role": "system",
                    "content": self._llm_config.additional_instructions.limit_in_private,
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

        self._message_queue.add(message.chat.id, ChatType.private, new_messages)

    async def _create_of_fetch_chat_state(self, chat: InputChat) -> ChatState:
        chat_state = await self._db_session.get(ChatState, chat.id)
        if chat_state is None:
            self._logger.debug("Adding new chat_state for chat: %s", chat)

            chat_state = ChatState(chat_id=chat.id, sleeping_till=0)
            self._db_session.add(chat_state)
            await self._db_session.commit()

        return chat_state

    async def _send_ignoring_if_needed(self, chat_state: ChatState) -> None:
        if (
            time.time() - chat_state.last_ignored_answer
            > DefaultPrivateMessageProcessor.IGNORED_MESSAGE_MIN_INTERVAL
        ):
            await self._sender_service.send_ignoring(chat_state.chat_id)

            chat_state.last_ignored_answer = int(time.time())
            await self._db_session.commit()
