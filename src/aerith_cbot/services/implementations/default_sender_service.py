import asyncio
import logging
import random

from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from chatgpt_md_converter import telegram_format
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import SenderService, StickersService
from aerith_cbot.services.abstractions.models import ModelResponse


class DefaultSenderService(SenderService):
    IGNORING_STICKER_CHANCE = 0.5

    def __init__(
        self, db_session: AsyncSession, stickers_service: StickersService, bot: Bot
    ) -> None:
        super().__init__()

        self._bot = bot
        self._stickers_service = stickers_service
        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def send_model_response(self, chat_id: int, response: ModelResponse) -> None:
        reply_used = False

        if response.text or response.sticker:
            await self._bot.send_chat_action(chat_id=chat_id, action="typing")

            for text in response.text:
                # model sometime returns empty text string
                formatted_text = telegram_format(text)
                if not formatted_text:
                    continue

                await asyncio.sleep(random.randint(0, 1))

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
                    self._logger.debug(
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
                    self._logger.debug(
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
                update(ChatState).where(ChatState.chat_id == chat_id).values(ignoring_streak=0)
            )
            await self._db_session.commit()

    async def send_model_refusal(self, chat_id: int, refusal: str) -> None:
        await self._bot.send_message(chat_id, refusal)

        await self._db_session.execute(
            update(ChatState).where(ChatState.chat_id == chat_id).values(ignoring_streak=0)
        )
        await self._db_session.commit()

    async def send_ignoring(self, chat_id: int) -> None:
        await self._bot.send_chat_action(chat_id=chat_id, action="typing")

        random_sleep_interval = random.randint(1, 3)
        await asyncio.sleep(random_sleep_interval)

        # TODO: generate phrase from LLM
        phrase = random.choice(
            [
                "извини, но я сейчас занята. обязательно поговорим позже!!!",
                "ой, сейчас не могу, давай чуть позже..",
                "извини, сейчас не могу, позже наверстаем!",
                "занята, но обещаю скоро откликнуться.......",
            ]
        )
        await self._bot.send_message(chat_id, phrase)

        if random.random() < DefaultSenderService.IGNORING_STICKER_CHANCE:
            emojies = "😴💤💼"
            emoji = random.choice(emojies)
            sticker_file_id = await self._stickers_service.search(emoji)

            if sticker_file_id is not None:
                self._logger.debug(
                    "Sticker with emoji %s found, file_id is: %s",
                    emoji,
                    sticker_file_id,
                )
                await self._bot.send_sticker(chat_id, sticker_file_id)
            else:
                self._logger.debug("Cannot find sticker with emoji %s", emoji)

    async def send_support_end_notify(self, chat_id: int) -> None:
        keyboard = InlineKeyboardBuilder()
        keyboard.row(types.InlineKeyboardButton(text="продлить!", callback_data="prolong_support"))
        await self._bot.send_message(
            chat_id=chat_id,
            text="привет! твоя поддержка заканчивается меньше, чем через сутки...",
            reply_markup=keyboard.as_markup(),
        )
