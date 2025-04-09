import logging

from aiogram import Bot, Router, exceptions, types
from aiogram.filters import Command, CommandObject
from dishka import FromDishka

from aerith_cbot.config import BotConfig
from aerith_cbot.services.abstractions import StickersService
from aerith_cbot.services.abstractions.models import StickerDTO

stickers_router = Router()
logger = logging.getLogger(__name__)


@stickers_router.message(Command("sload"))
async def sticker_load_handler(
    message: types.Message,
    stickers_service: FromDishka[StickersService],
    bot_config: FromDishka[BotConfig],
    bot: Bot,
    command: CommandObject,
):
    if message.from_user and message.from_user.id not in bot_config.admin_ids:
        return

    if message.reply_to_message is not None and message.reply_to_message.sticker is not None:
        if message.reply_to_message.sticker.set_name is None:
            return await message.answer("этот стикер не из сета :(")

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


@stickers_router.message(Command("sunload"))
async def sticker_unload_handler(
    message: types.Message,
    stickers_service: FromDishka[StickersService],
    bot_config: FromDishka[BotConfig],
    bot: Bot,
    command: CommandObject,
):
    if message.from_user and message.from_user.id not in bot_config.admin_ids:
        return

    if message.reply_to_message is not None and message.reply_to_message.sticker is not None:
        if message.reply_to_message.sticker.set_name is None:
            return await message.answer("этот стикер не из сета :(")

        set_name = message.reply_to_message.sticker.set_name
    elif command.args is not None:
        set_name = command.args
    else:
        return await message.answer("введи, пожалуйста, названи сета!!!")

    await stickers_service.unload(set_name)
    await message.answer("удалила!")
