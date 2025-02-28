from aiogram import Router, types
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import GroupMessageProcessor

group_router = Router()
group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))


@group_router.message()
async def chat_message_handler(
    message: types.Message,
    processor: FromDishka[GroupMessageProcessor],
):
    await processor.process(message)
