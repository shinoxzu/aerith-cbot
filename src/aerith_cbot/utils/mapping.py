import aiohttp
from aiogram import Bot
from aiogram.types import Chat, Message, User

from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser


def tg_chat_to_input_chat(chat: Chat) -> InputChat:
    return InputChat(id=chat.id, name=chat.full_name)


def tg_user_to_input_user(user: User) -> InputUser:
    return InputUser(id=user.id, name=user.full_name)


async def tg_msg_to_input_message(
    msg: Message, bot: Bot, client_seesion: aiohttp.ClientSession, is_inner=False
) -> InputMessage:
    if msg.from_user is None:
        raise ValueError("Cannot parse messsage with sender_chat")

    # max depth of replies is 1
    reply_message = None
    if msg.reply_to_message is not None and not is_inner:
        reply_message = await tg_msg_to_input_message(
            msg.reply_to_message, bot, client_seesion, is_inner=True
        )

    text = msg.text or msg.caption or (msg.sticker and msg.sticker.emoji)

    photo_url = None
    if msg.photo is not None:
        file_id = msg.photo[-1].file_id
        file = await bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    voice_url = None
    if msg.voice is not None and msg.voice.duration < 1200:
        file_id = msg.voice.file_id
        file = await bot.get_file(file_id)
        voice_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"

    # 5 KB and text/* mime-type
    if (
        msg.document is not None
        and msg.document.file_size is not None
        and msg.document.file_size <= 1024 * 15
        and msg.document.mime_type is not None
        and msg.document.mime_type.startswith("text/")
    ):
        file_id = msg.document.file_id
        file = await bot.get_file(file_id)
        document_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
        file_text = await fetch_file_text(document_url, client_seesion)

        if text is None:
            text = f'{msg.document.file_name}\n"""{file_text}"""'
        else:
            text += f'\n\n{msg.document.file_name}\n"""{file_text}"""'

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
        voice_url=voice_url,
        text=text,
        date=str(msg.date),
        contains_aerith_mention=await _is_aerith_mentioned(msg, bot),
    )


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


async def fetch_file_text(url: str, client_seesion: aiohttp.ClientSession) -> str:
    try:
        async with client_seesion.get(url) as response:
            return await response.text()
    except aiohttp.ClientError:
        return ""
