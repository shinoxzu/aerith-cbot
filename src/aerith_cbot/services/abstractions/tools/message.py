from argparse import ArgumentError

from aiogram.types import Message, User

from aerith_cbot.services.abstractions.models import ModelInputMessage, ModelInputUser


def tg_user_to_model_input(user: User) -> ModelInputUser:
    return ModelInputUser(user_id=user.id, name=user.full_name)


def tg_msg_to_model_input(msg: Message) -> ModelInputMessage:
    if msg.from_user is None:
        raise ArgumentError(None, "Cannot parse messsage from chat")

    reply_message = None
    if msg.reply_to_message is not None:
        reply_message = tg_msg_to_model_input(msg.reply_to_message)

    return ModelInputMessage(
        message_id=msg.message_id,
        sender=tg_user_to_model_input(msg.from_user),
        text=msg.text or msg.caption or "",
        date=str(msg.date),
        reply_message=reply_message,
    )
