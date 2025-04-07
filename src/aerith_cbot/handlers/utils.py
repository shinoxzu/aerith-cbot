import logging

from aiogram import Router, types
from aiogram.filters import Command

utils_router = Router()
logger = logging.getLogger(__name__)


@utils_router.error()
async def error_handler(event: types.ErrorEvent):
    logger.critical("Critical error caused by %s", event.exception, exc_info=True)


@utils_router.message(Command("help"))
async def help_command_handler(message: types.Message):
    await message.answer("тут уже не помочь")


@utils_router.message(Command("terms"))
async def terms_command_handler(message: types.Message):
    await message.answer(
        "Используя бота, вы соглашаетесь с тем, что мы сохраняем введенную вами "
        "информацию для дальнейшего взаимодействия."
    )
