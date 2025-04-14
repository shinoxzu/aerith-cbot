import logging

from aiogram import Bot, exceptions
from aiohttp import ClientSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import VoiceTranscriber
from aerith_cbot.services.abstractions.utils.mapping import input_msg_to_model_input
from aerith_cbot.utils.mapping import tg_msg_to_input_message

from . import ToolCommand


class GetChatInfoToolCommand(ToolCommand):
    def __init__(
        self,
        bot: Bot,
        llm_config: LLMConfig,
        voice_transcriber: VoiceTranscriber,
        client_session: ClientSession,
    ) -> None:
        super().__init__()

        self._bot = bot
        self._llm_config = llm_config
        self._voice_transcriber = voice_transcriber
        self._client_session = client_session
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        try:
            chat = await self._bot.get_chat(chat_id=chat_id)

            chat_info = {
                "name": chat.full_name,
                "description": chat.description,
            }

            if chat.pinned_message is not None:
                pinned_input_message = await tg_msg_to_input_message(
                    chat.pinned_message, self._bot, self._client_session
                )
                pinned_model_input_message = await input_msg_to_model_input(
                    pinned_input_message, self._voice_transcriber
                )
                chat_info["pinned_message"] = pinned_model_input_message.dict()

            return str(chat_info)
        except exceptions.TelegramAPIError:
            return self._llm_config.additional_instructions.aerith_hasnt_rights
