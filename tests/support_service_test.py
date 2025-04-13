from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import UserSupport
from aerith_cbot.services.implementations import DefaultLimitsService, DefaultSupportService


@pytest.mark.asyncio
async def test_active_supporter():
    end_support_time = 100

    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock()
    mock_db_session.get.return_value = UserSupport(
        user_id=123, end_timestamp=end_support_time, is_notified=False
    )

    mock_sender_service = MagicMock(spec=DefaultLimitsService)

    support_service = DefaultSupportService(mock_db_session, mock_sender_service)

    with patch("time.time", return_value=end_support_time - 50):
        assert await support_service.is_active_supporter(123)

    with patch("time.time", return_value=end_support_time + 50):
        assert not await support_service.is_active_supporter(123)


@pytest.mark.asyncio
async def test_active_supporter_is_none():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.get = AsyncMock()
    mock_db_session.get.return_value = None

    mock_sender_service = MagicMock(spec=DefaultLimitsService)

    support_service = DefaultSupportService(mock_db_session, mock_sender_service)

    with patch("time.time", return_value=50):
        assert not await support_service.is_active_supporter(123)


@pytest.mark.asyncio
async def test_notify_supporter():
    end_support_time = 100

    mock_db_session = MagicMock(spec=AsyncSession)

    mock_result = MagicMock()
    mock_result.scalars = MagicMock()
    mock_result.scalars.return_value = [
        UserSupport(user_id=123, end_timestamp=end_support_time + 1, is_notified=False),
        UserSupport(user_id=123, end_timestamp=end_support_time + 3, is_notified=False),
    ]

    mock_db_session.execute = AsyncMock()
    mock_db_session.execute.return_value = mock_result
    mock_db_session.commit = AsyncMock()

    mock_sender_service = MagicMock(spec=DefaultLimitsService)
    mock_sender_service.send_support_end_notify = AsyncMock()

    support_service = DefaultSupportService(mock_db_session, mock_sender_service)

    with patch("time.time", return_value=end_support_time - 50):
        with patch("asyncio.sleep", AsyncMock()):
            await support_service.notify_users_to_prolong()

    assert mock_sender_service.send_support_end_notify.call_count == 2
