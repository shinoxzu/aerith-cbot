from aerith_cbot.services.abstractions import VoiceTranscriber

from ..models import InputMessage, InputUser, ModelInputMessage, ModelInputUser


def input_user_to_model_input(user: InputUser) -> ModelInputUser:
    return ModelInputUser(user_id=user.id, name=user.name)


async def input_msg_to_model_input(
    msg: InputMessage, voice_transcriber: VoiceTranscriber
) -> ModelInputMessage:
    text = msg.text
    if msg.voice_url is not None:
        voice_text = await voice_transcriber.transcribe(msg.voice_url)
        text = f"Текст из голосового сообщения: {voice_text}"

    reply_message = None
    if msg.reply_message is not None:
        reply_message = await input_msg_to_model_input(msg.reply_message, voice_transcriber)

    return ModelInputMessage(
        message_id=msg.id,
        sender=input_user_to_model_input(msg.sender),
        date=msg.date,
        reply_message=reply_message,
        text=text,
    )
