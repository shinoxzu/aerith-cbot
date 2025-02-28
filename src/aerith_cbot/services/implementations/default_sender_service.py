import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import Message
from chatgpt_md_converter import telegram_format
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import SenderService, StickersService
from aerith_cbot.services.abstractions.models import ModelResponse


class DefaultSenderService(SenderService):
    def __init__(
        self, db_session: AsyncSession, stickers_service: StickersService, bot: Bot
    ) -> None:
        super().__init__()

        self._bot = bot
        self._stickers_service = stickers_service
        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def send(self, message: Message, response: ModelResponse) -> None:
        if response.text or response.sticker:
            await self._bot.send_chat_action(chat_id=message.chat.id, action="typing")

            for text in response.text:
                await asyncio.sleep(1)
                await message.answer(telegram_format(text), parse_mode=ParseMode.HTML)

            if response.sticker is not None:
                sticker_file_id = await self._stickers_service.search(response.sticker)

                if sticker_file_id is not None:
                    self._logger.info(
                        "Sticker with emoji %s found, file_id is: %s",
                        response.sticker,
                        sticker_file_id,
                    )
                    await message.answer_sticker(sticker=sticker_file_id)
                else:
                    self._logger.info(
                        "Cannot find sticker with emoji %s, sending text message instead",
                        response.sticker,
                    )
                    await message.answer(response.sticker)

            await self._db_session.execute(
                update(ChatState)
                .where(ChatState.chat_id == message.chat.id)
                .values(listening_streak=0, ignoring_streak=0)
            )
            await self._db_session.commit()
