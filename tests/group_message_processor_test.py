from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue
from aerith_cbot.services.implementations.processors import (
    DefaultGroupMessageProcessor,
)


@pytest.mark.asyncio
async def test_addding_chat_state_if_none(default_message_to_process: InputMessage):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(return_value=None)
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=MessageQueue(),
    )

    await group_message_processor.process(default_message_to_process)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_skipping_unfocused():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=False, ignoring_streak=0, listening_streak=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
    )

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            text="привет",
            date="1 января, 2025",
            contains_aerith_mention=False,
        )
    )

    mock_db_session.commit.assert_not_called()
    mock_message_queue.add.assert_not_called()


@pytest.mark.asyncio
async def test_focusing_unfocused():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=False, ignoring_streak=0, listening_streak=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
    )

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            text="привет",
            date="1 января, 2025",
            contains_aerith_mention=True,
        )
    )

    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_adding_message_to_queue():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=True, ignoring_streak=0, listening_streak=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
    )

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            text="привет",
            date="1 января, 2025",
            contains_aerith_mention=False,
        )
    )

    mock_message_queue.add.assert_called_once()
