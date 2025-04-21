import aiohttp
from aiogram import Bot
from aiogram.types import Chat, Message, User

from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser


def tg_chat_to_input_chat(chat: Chat) -> InputChat:
    return InputChat(id=chat.id, name=chat.full_name)


async def tg_user_to_input_user(user: User, bot: Bot) -> InputUser:
    aerith_bot = await bot.me()
    return InputUser(id=user.id, name=user.full_name, is_aerith=user.id == aerith_bot.id)


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

    is_aerith_mentioned = await _is_aerith_mentioned(msg, bot)
    is_aerith_replied = await _is_aerith_replied(msg, bot)

    return InputMessage(
        id=msg.message_id,
        chat=tg_chat_to_input_chat(msg.chat),
        sender=await tg_user_to_input_user(msg.from_user, bot),
        reply_message=reply_message,
        photo_url=photo_url,
        voice_url=voice_url,
        text=text,
        date=str(msg.date),
        is_aerith_called=is_aerith_mentioned or is_aerith_replied,
        is_aerith_joined=_is_aerith_joined(msg, bot),
        meta=_parse_message_meta(msg),
    )


def _parse_message_meta(msg: Message) -> str | None:
    meta = None

    if msg.audio is not None:
        if msg.audio.title and msg.audio.performer:
            meta = f"В сообщении есть аудио: {msg.audio.title} — {msg.audio.performer}"
        else:
            meta = "В сообщении есть аудио"

    if msg.video is not None:
        meta = "В сообщении есть видео"

    if msg.document is not None:
        meta = f"В сообщении есть документ: {msg.document.file_name}"

    if msg.poll is not None:
        options = "/".join([option.text for option in msg.poll.options])
        meta = f"В сообщении есть опрос: {msg.poll.question} (варианты: {options})"

    if msg.pinned_message is not None:
        meta = "Сообщение было закреплено"

    if msg.new_chat_title is not None:
        meta = f"Название чата было обновлено: {msg.new_chat_title}"

    if msg.new_chat_photo is not None:
        meta = "Фото чата было обновлено"

    if msg.delete_chat_photo is not None:
        meta = "Фото чата было удалено"

    if msg.new_chat_members:
        meta = "Некоторые участники присоединились к чату"

    if msg.left_chat_member:
        meta = "Некоторые участники покинули чат"

    return meta


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


async def _is_aerith_replied(msg: Message, bot: Bot) -> bool:
    aerith_bot = await bot.me()
    return (
        msg.reply_to_message is not None
        and msg.reply_to_message.from_user is not None
        and msg.reply_to_message.from_user.id == aerith_bot.id
    )


def _is_aerith_joined(msg: Message, bot: Bot) -> bool:
    if msg.new_chat_members:
        for chat_member in msg.new_chat_members:
            if chat_member.id == bot.id:
                return True
    return False


async def fetch_file_text(url: str, client_seesion: aiohttp.ClientSession) -> str:
    try:
        async with client_seesion.get(url) as response:
            return await response.text()
    except aiohttp.ClientError:
        return ""
