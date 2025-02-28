import logging

from aiogram import Bot, Router, exceptions, types
from aiogram.filters import Command, CommandObject
from dishka import FromDishka

from aerith_cbot.services.abstractions import StickersService
from aerith_cbot.services.abstractions.models import StickerDTO

utils_router = Router()
logger = logging.getLogger(__name__)


@utils_router.message(Command("sload"))
async def private_message_handler(
    message: types.Message,
    stickers_service: FromDishka[StickersService],
    bot: Bot,
    command: CommandObject,
):
    if message.reply_to_message is not None and message.reply_to_message.sticker is not None:
        if message.reply_to_message.sticker.set_name is None:
            return await message.answer("это стикер не из сета :(")

        set_name = message.reply_to_message.sticker.set_name
    elif command.args is not None:
        set_name = command.args
    else:
        return await message.answer("введи, пожалуйста, названи сета!!!")

    try:
        sticker_set = await bot.get_sticker_set(set_name)
    except exceptions.TelegramBadRequest:
        return await message.answer("такого сета нет. вроде бы...")

    stickers_to_load = []
    for sticker in sticker_set.stickers:
        if sticker.emoji is None:
            continue

        stickers_to_load.append(
            StickerDTO(file_id=sticker.file_id, emoji=sticker.emoji, set_name=sticker_set.name)
        )

    await stickers_service.load(stickers_to_load)
    await message.answer("загрузила!")


@utils_router.error()
async def error_handler(event: types.ErrorEvent):
    logger.critical("Critical error caused by %s", event.exception, exc_info=True)
