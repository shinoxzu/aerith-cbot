from aiogram import Bot, Router, types
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
):
    input_message = await tg_msg_to_input_message(message, bot)
    await processor.process(input_message)
