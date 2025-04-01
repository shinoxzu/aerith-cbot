from ..models import InputMessage, InputUser, ModelInputMessage, ModelInputUser


def input_user_to_model_input(user: InputUser) -> ModelInputUser:
    return ModelInputUser(user_id=user.id, name=user.name)


def input_msg_to_model_input(msg: InputMessage) -> ModelInputMessage:
    return ModelInputMessage(
        message_id=msg.id,
        sender=input_user_to_model_input(msg.sender),
        date=msg.date,
        reply_message=input_msg_to_model_input(msg.reply_message) if msg.reply_message else None,
        text=msg.text,
    )
