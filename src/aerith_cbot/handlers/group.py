from aiogram import Bot, Router, types
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions.processors import GroupMessageProcessor
from aerith_cbot.utils.mapping import tg_msg_to_input_message

group_router = Router()
group_router.message.filter(ChatTypeFilter(["group", "supergroup"]))


@group_router.message()
async def chat_message_handler(
    message: types.Message,
    bot: Bot,
    processor: FromDishka[GroupMessageProcessor],
):
    input_message = await tg_msg_to_input_message(message, bot)
    await processor.process(input_message)
