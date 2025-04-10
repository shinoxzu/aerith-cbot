from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.services.abstractions import StickersService
from aerith_cbot.services.abstractions.models import ModelResponse
from aerith_cbot.services.implementations.default_sender_service import DefaultSenderService


@pytest.mark.asyncio
async def test_send_text_message():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock()
    mock_stickers_service.is_valid_emoji = MagicMock()

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()

    response = ModelResponse(text=["hi", "how are u"], sticker=None, reply_to_message_id=None)

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()

    mock_stickers_service.search.assert_not_called()
    mock_stickers_service.is_valid_emoji.assert_not_called()

    assert mock_bot.send_message.call_count == 2
    assert mock_bot.send_chat_action.call_count == 1


@pytest.mark.asyncio
async def test_send_empty_message():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock()
    mock_stickers_service.is_valid_emoji = MagicMock()

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()

    response = ModelResponse(text=[], sticker=None, reply_to_message_id=None)

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_bot.send_chat_action.assert_not_called()
    mock_bot.send_message.assert_not_called()

    mock_stickers_service.search.assert_not_called()
    mock_stickers_service.is_valid_emoji.assert_not_called()

    mock_db_session.execute.assert_not_called()
    mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_send_empty_text_message():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock()
    mock_stickers_service.is_valid_emoji = MagicMock()

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()

    response = ModelResponse(
        text=["", ""],  # with [""] test also passed
        sticker=None,
        reply_to_message_id=None,
    )

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_bot.send_chat_action.assert_called()
    mock_bot.send_message.assert_not_called()

    mock_stickers_service.search.assert_not_called()
    mock_stickers_service.is_valid_emoji.assert_not_called()

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_send_sticker():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock(return_value="sticker_file_id")
    mock_stickers_service.is_valid_emoji = MagicMock(return_value=True)

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_sticker = AsyncMock()

    response = ModelResponse(text=[""], sticker="😁", reply_to_message_id=None)

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_bot.send_chat_action.assert_called()
    mock_bot.send_message.assert_not_called()
    mock_bot.send_sticker.assert_called_once()

    mock_stickers_service.is_valid_emoji.assert_called_once()
    mock_stickers_service.search.assert_called_once()

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_send_unknown_sticker():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock(return_value=None)
    mock_stickers_service.is_valid_emoji = MagicMock(return_value=True)

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_sticker = AsyncMock()

    response = ModelResponse(text=[""], sticker="😁", reply_to_message_id=None)

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_bot.send_chat_action.assert_called()
    mock_bot.send_message.assert_called_once()
    mock_bot.send_sticker.assert_not_called()

    mock_stickers_service.is_valid_emoji.assert_called_once()
    mock_stickers_service.search.assert_called_once()

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_send_text_instead_of_emoji():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    mock_stickers_service = MagicMock(spec=StickersService)
    mock_stickers_service.search = AsyncMock(return_value=None)
    mock_stickers_service.is_valid_emoji = MagicMock(return_value=False)

    mock_bot = MagicMock()
    mock_bot.send_chat_action = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_sticker = AsyncMock()

    response = ModelResponse(text=[""], sticker="null", reply_to_message_id=None)

    send_service = DefaultSenderService(
        db_session=mock_db_session, stickers_service=mock_stickers_service, bot=mock_bot
    )
    await send_service.send(chat_id=1, response=response)

    mock_bot.send_chat_action.assert_called()
    mock_bot.send_message.assert_not_called()
    mock_bot.send_sticker.assert_not_called()

    mock_stickers_service.is_valid_emoji.assert_called_once()
    mock_stickers_service.search.assert_not_called()

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()
