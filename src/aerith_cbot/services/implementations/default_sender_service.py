import asyncio
import logging

from aiogram import Bot
from aiogram.enums import ParseMode
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

    async def send(self, chat_id: int, response: ModelResponse) -> None:
        reply_used = False

        if response.text or response.sticker:
            await self._bot.send_chat_action(chat_id=chat_id, action="typing")

            for text in response.text:
                await self._bot.send_chat_action(chat_id=chat_id, action="typing")

                # model sometime returns empty text string
                formatted_text = telegram_format(text)
                if not formatted_text:
                    continue

                await self._bot.send_message(
                    chat_id,
                    formatted_text,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=response.reply_to_message_id if not reply_used else None,
                )
                reply_used = True

                await asyncio.sleep(1)

            if response.sticker is not None and self._stickers_service.is_valid_emoji(
                response.sticker
            ):
                sticker_file_id = await self._stickers_service.search(response.sticker)

                if sticker_file_id is not None:
                    self._logger.info(
                        "Sticker with emoji %s found, file_id is: %s",
                        response.sticker,
                        sticker_file_id,
                    )
                    await self._bot.send_sticker(
                        chat_id,
                        sticker_file_id,
                        reply_to_message_id=response.reply_to_message_id
                        if not reply_used
                        else None,
                    )
                else:
                    self._logger.info(
                        "Cannot find sticker with emoji %s, sending text message instead",
                        response.sticker,
                    )
                    await self._bot.send_message(
                        chat_id,
                        response.sticker,
                        reply_to_message_id=response.reply_to_message_id
                        if not reply_used
                        else None,
                    )

            await self._db_session.execute(
                update(ChatState)
                .where(ChatState.chat_id == chat_id)
                .values(listening_streak=0, ignoring_streak=0)
            )
            await self._db_session.commit()

    async def send_refusal(self, chat_id: int, refusal: str) -> None:
        await self._bot.send_message(chat_id, refusal)

        await self._db_session.execute(
            update(ChatState)
            .where(ChatState.chat_id == chat_id)
            .values(listening_streak=0, ignoring_streak=0)
        )
        await self._db_session.commit()
