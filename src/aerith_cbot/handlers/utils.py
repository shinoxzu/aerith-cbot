import logging

from aiogram import Router, types
from aiogram.filters import Command
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import MessageService

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
        """
Используя бота, вы соглашаетесь с тем, что мы храним некоторую информацию (воспоминания, активный контекст) для дальнейшего взаимодействия. Также вы должны понимать, что написанная ботом информация может являться ложной. Вы не должны ориентироваться на нее в сложных ситуациях.

Вы обязуетесь не автоматизировать взаимодействие с ботом и не использовать его тем или иным образом для противоправных целей. За нарушение этих правил мы можем ограничить для вас доступ к боту навсегда.
"""
    )


# TODO: clear context in groups too
@utils_router.message(ChatTypeFilter("private"), Command("clear"))
async def clear_command_handler(
    message: types.Message, message_service: FromDishka[MessageService]
):
    await message_service.clear(message.chat.id)
    await message.answer("контекст очищен!")
