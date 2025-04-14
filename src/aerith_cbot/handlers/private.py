from aiogram import Bot, Router, types
from aiohttp import ClientSession
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions.processors import PrivateMessageProcessor
from aerith_cbot.utils.mapping import tg_msg_to_input_message

private_router = Router()
private_router.message.filter(ChatTypeFilter("private"))


@private_router.message()
async def private_message_handler(
    message: types.Message,
    bot: Bot,
    processor: FromDishka[PrivateMessageProcessor],
    client_session: FromDishka[ClientSession],
):
    input_message = await tg_msg_to_input_message(message, bot, client_session)
    await processor.process(input_message)
