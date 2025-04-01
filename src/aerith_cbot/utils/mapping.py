import base64

import aiohttp
from aiogram import Bot
from aiogram.types import Chat, Message, User

from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser


def tg_chat_to_input_chat(chat: Chat) -> InputChat:
    return InputChat(id=chat.id, name=chat.full_name)


def tg_user_to_input_user(user: User) -> InputUser:
    return InputUser(id=user.id, name=user.full_name)


async def tg_msg_to_input_message(msg: Message, bot: Bot) -> InputMessage:
    if msg.from_user is None:
        raise ValueError("Cannot parse messsage with sender_chat")

    reply_message = None
    if msg.reply_to_message is not None:
        reply_message = await tg_msg_to_input_message(msg.reply_to_message, bot)

    photo_url = None
    if msg.photo is not None:
        if len(msg.photo) >= 3:
            file_id = msg.photo[2].file_id
        else:
            file_id = msg.photo[-1].file_id

        file = await bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    # text of the message will be one of:
    # * text
    # * caption
    # * sticker emoji

    return InputMessage(
        id=msg.message_id,
        chat=tg_chat_to_input_chat(msg.chat),
        sender=tg_user_to_input_user(msg.from_user),
        reply_message=reply_message,
        photo_url=photo_url,
        text=msg.text or msg.caption or (msg.sticker and msg.sticker.emoji),
        date=str(msg.date),
        contains_aerith_mention=await _is_aerith_mentioned(msg, bot),
    )


async def _fetch_image_as_base64(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            image_data = await response.read()
            return base64.b64encode(image_data).decode("utf-8")


async def _is_aerith_mentioned(msg: Message, bot: Bot) -> bool:
    is_triggered = False

    if msg.entities is not None:
        me = await bot.me()
        text = msg.text or msg.caption or ""

        for entity in msg.entities:
            if entity.type == "mention":
                mention = entity.extract_from(text)
                is_triggered = mention == "@" + (me.username or "")

            elif entity.type == "text_mention" and entity.user is not None:
                is_triggered = entity.user.id == me.id

            if is_triggered:
                break

    return is_triggered
