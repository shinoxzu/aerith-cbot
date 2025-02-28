from aiogram import Router, types
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import PrivateMessageProcessor

private_router = Router()
private_router.message.filter(ChatTypeFilter("private"))


@private_router.message()
async def private_message_handler(
    message: types.Message,
    processor: FromDishka[PrivateMessageProcessor],
):
    await processor.process(message)
