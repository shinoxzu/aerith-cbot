import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LimitsConfig, LLMConfig
from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import VoiceTranscriber
from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser
from aerith_cbot.services.implementations import DefaultLimitsService, DefaultSenderService
from aerith_cbot.services.implementations.chat_dispatcher import MessageQueue
from aerith_cbot.services.implementations.processors import (
    DefaultGroupMessageProcessor,
)


@pytest.mark.asyncio
async def test_sleeping_chat_ignore(
    default_message_to_process: InputMessage,
    default_limits_config: LimitsConfig,
    default_llm_config: LLMConfig,
):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(
            chat_id=1,
            is_focused=False,
            ignoring_streak=0,
            sleeping_till=1000000000000000,
            last_ignored_answer=0,
        )
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.check_private_limit = AsyncMock(return_value=True)

    mock_sender_service = MagicMock(spec=DefaultSenderService)
    mock_voice_transcriber = MagicMock(spec=VoiceTranscriber)

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=MessageQueue(),
        limits_config=default_limits_config,
        limits_service=mock_limits_service,
        llm_config=default_llm_config,
        sender_service=mock_sender_service,
        voice_transcriber=mock_voice_transcriber,
    )

    await group_message_processor.process(default_message_to_process)

    mock_limits_service.check_private_limit.assert_not_called()
    mock_message_queue.add.assert_not_called()


@pytest.mark.asyncio
async def test_addding_chat_state_if_none(
    default_message_to_process: InputMessage,
    default_limits_config: LimitsConfig,
    default_llm_config: LLMConfig,
):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(return_value=None)
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.scalar = AsyncMock(return_value=0)

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.check_private_limit = AsyncMock(return_value=False)

    mock_sender_service = MagicMock(spec=DefaultSenderService)
    mock_voice_transcriber = MagicMock(spec=VoiceTranscriber)

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=MessageQueue(),
        limits_config=default_limits_config,
        limits_service=mock_limits_service,
        llm_config=default_llm_config,
        sender_service=mock_sender_service,
        voice_transcriber=mock_voice_transcriber,
    )

    await group_message_processor.process(default_message_to_process)

    mock_db_session.add.assert_called_once()
    assert mock_db_session.commit.call_count >= 1  # adding at least chat_state


@pytest.mark.asyncio
async def test_skipping_unfocused(
    default_limits_config: LimitsConfig, default_llm_config: LLMConfig
):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=False, ignoring_streak=0, sleeping_till=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.check_private_limit = AsyncMock(return_value=True)

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    mock_sender_service = MagicMock(spec=DefaultSenderService)

    mock_voice_transcriber = MagicMock(spec=VoiceTranscriber)

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
        limits_config=default_limits_config,
        limits_service=mock_limits_service,
        llm_config=default_llm_config,
        sender_service=mock_sender_service,
        voice_transcriber=mock_voice_transcriber,
    )
    
    group_message_processor._is_chat_inactive = AsyncMock(return_value=False)

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            voice_url=None,
            text="привет",
            date="1 января, 2025",
            is_aerith_called=False,
            is_aerith_joined=False,
            meta=None,
        )
    )

    mock_db_session.commit.assert_not_called()
    mock_message_queue.add.assert_not_called()


@pytest.mark.asyncio
async def test_focusing_unfocused(
    default_limits_config: LimitsConfig, default_llm_config: LLMConfig
):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=False, ignoring_streak=0, sleeping_till=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.check_private_limit = AsyncMock(return_value=True)

    mock_sender_service = MagicMock(spec=DefaultSenderService)

    mock_voice_transcriber = MagicMock(spec=VoiceTranscriber)

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
        limits_config=default_limits_config,
        limits_service=mock_limits_service,
        llm_config=default_llm_config,
        sender_service=mock_sender_service,
        voice_transcriber=mock_voice_transcriber,
    )
    
    group_message_processor._is_chat_inactive = AsyncMock(return_value=False)

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            voice_url=None,
            text="привет",
            date="1 января, 2025",
            is_aerith_called=True,
            is_aerith_joined=False,
            meta=None,
        )
    )

    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_adding_message_to_queue(
    default_limits_config: LimitsConfig, default_llm_config: LLMConfig
):
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock(
        return_value=ChatState(chat_id=1, is_focused=True, ignoring_streak=0, sleeping_till=0)
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.scalar = AsyncMock(return_value=int(time.time()))

    mock_message_queue = MagicMock(spec=MessageQueue)
    mock_message_queue.add = MagicMock()

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.check_private_limit = AsyncMock(return_value=True)

    mock_sender_service = MagicMock(spec=DefaultSenderService)

    mock_voice_transcriber = MagicMock(spec=VoiceTranscriber)

    group_message_processor = DefaultGroupMessageProcessor(
        db_session=mock_db_session,
        message_queue=mock_message_queue,
        limits_config=default_limits_config,
        limits_service=mock_limits_service,
        llm_config=default_llm_config,
        sender_service=mock_sender_service,
        voice_transcriber=mock_voice_transcriber,
    )

    await group_message_processor.process(
        InputMessage(
            id=1,
            chat=InputChat(id=1, name="чат друзей"),
            sender=InputUser(id=1, name="Петя"),
            reply_message=None,
            photo_url=None,
            voice_url=None,
            text="привет",
            date="1 января, 2025",
            is_aerith_called=False,
            is_aerith_joined=False,
            meta=None,
        )
    )

    mock_message_queue.add.assert_called_once()
