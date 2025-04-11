import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import (
    GroupLimitEntry,
    UserGroupLimitEntry,
    UserPrivateLimitEntry,
)
from aerith_cbot.services.abstractions.support_service import SupportService
from aerith_cbot.services.implementations import DefaultLimitsService


@pytest.fixture
def mock_db_session():
    mock = MagicMock(spec=AsyncSession)
    mock.get = AsyncMock()
    mock.add = MagicMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.merge = AsyncMock()
    return mock


@pytest.fixture
def mock_support_service():
    mock = MagicMock(spec=SupportService)
    mock.is_active_supporter = AsyncMock(return_value=False)
    return mock


@pytest.mark.asyncio
async def test_check_private_limit_no_refresh_needed(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    current_time = int(time.time())

    limit_entry = UserPrivateLimitEntry(
        user_id=user_id,
        last_ref_time=current_time,
        remain_tokens=10,
    )

    mock_db_session.get.return_value = limit_entry

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    result = await service.check_private_limit(user_id)

    assert result is True
    mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_check_private_limit_needs_refresh_regular_user(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    current_time = int(time.time())

    limit_entry = UserPrivateLimitEntry(
        user_id=user_id,
        last_ref_time=current_time - default_limits_config.private_cooldown - 10,
        remain_tokens=0,
    )

    mock_db_session.get.return_value = limit_entry
    mock_support_service.is_active_supporter.return_value = False

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        result = await service.check_private_limit(user_id)

    assert result is True
    assert limit_entry.remain_tokens == default_limits_config.private_tokens_limit
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_private_limit_needs_refresh_supporter(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    current_time = int(time.time())

    limit_entry = UserPrivateLimitEntry(
        user_id=user_id,
        last_ref_time=current_time - default_limits_config.private_cooldown - 10,
        remain_tokens=0,
    )

    mock_db_session.get.return_value = limit_entry
    mock_support_service.is_active_supporter.return_value = True

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        result = await service.check_private_limit(user_id)

    assert result is True
    assert limit_entry.remain_tokens == default_limits_config.private_support_tokens_limit
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_subtract_private_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    tokens_count = 10

    limit_entry = UserPrivateLimitEntry(
        user_id=user_id, last_ref_time=int(time.time()), remain_tokens=20
    )

    mock_db_session.get.return_value = limit_entry

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    await service.subtract_private_tokens(user_id, tokens_count)

    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_group_limit_no_tokens_in_group(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(chat_id=chat_id, last_ref_time=current_time, remain_tokens=0)

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert result is False
    service._update_user_contact_and_create_limit_entry.assert_called_once_with(user_id, chat_id)
    service._update_group_members_limits.assert_called()


@pytest.mark.asyncio
async def test_subtract_group_tokens_from_active_user(
    default_limits_config, mock_db_session, mock_support_service
):
    chat_id = 456
    tokens_count = 10
    current_time = int(time.time())

    active_user = UserGroupLimitEntry(
        user_id=789,
        last_ref_time=current_time,
        remain_tokens=20,
    )

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[active_user, None])

    with patch("time.time", return_value=current_time):
        await service.subtract_group_tokens(chat_id, tokens_count)

    assert mock_db_session.execute.call_count == 2
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_subtract_group_tokens_from_inactive_user(
    default_limits_config, mock_db_session, mock_support_service
):
    chat_id = 456
    tokens_count = 10
    current_time = int(time.time())

    active_user = None

    inactive_user = UserGroupLimitEntry(
        user_id=101,
        last_ref_time=current_time,
        remain_tokens=40,
    )

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[active_user, inactive_user])

    with patch("time.time", return_value=current_time):
        await service.subtract_group_tokens(chat_id, tokens_count)

    assert mock_db_session.execute.call_count == 2
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_group_limit_entry(
    default_limits_config, mock_db_session, mock_support_service
):
    chat_id = 456
    current_time = int(time.time())

    mock_db_session.get.return_value = None

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        result = await service._create_or_fetch_group_limit_entry(chat_id)

    assert result.chat_id == chat_id
    assert result.last_ref_time == current_time
    assert result.remain_tokens == default_limits_config.group_generic_tokens_limit
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_user_private_limit_entry(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    current_time = int(time.time())

    mock_db_session.get.return_value = None

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        result = await service._create_or_fetch_user_limit_entry(user_id)

    assert result.user_id == user_id
    assert result.last_ref_time == current_time
    assert result.remain_tokens == default_limits_config.private_tokens_limit
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_group_limit_refresh_group_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(
        chat_id=chat_id,
        last_ref_time=current_time - default_limits_config.group_cooldown - 10,
        remain_tokens=0,
    )

    active_user = UserGroupLimitEntry(
        user_id=789,
        last_ref_time=current_time,
        remain_tokens=30,
    )

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[active_user, None])

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert group_limit.last_ref_time == current_time
    assert group_limit.remain_tokens == default_limits_config.group_generic_tokens_limit
    assert result is True
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_group_limit_no_users_with_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(chat_id=chat_id, last_ref_time=current_time, remain_tokens=50)

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[None, None])

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert result is False
    assert service._fetch_top_user_limit_entry.call_count == 1


@pytest.mark.asyncio
async def test_subtract_group_tokens_no_users_with_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    chat_id = 456
    tokens_count = 10
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[None, None])

    with patch("time.time", return_value=current_time):
        await service.subtract_group_tokens(chat_id, tokens_count)

    assert mock_db_session.execute.call_count == 0
    mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_user_contact_and_ensure_limit_entry(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        await service._update_user_contact_and_create_limit_entry(user_id, chat_id)

    mock_db_session.merge.assert_called_once()
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_group_limit_active_user_has_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(chat_id=chat_id, last_ref_time=current_time, remain_tokens=50)

    active_user = UserGroupLimitEntry(
        user_id=789,
        last_ref_time=current_time,
        remain_tokens=30,
    )

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)
    service._fetch_top_user_limit_entry = AsyncMock(return_value=active_user)

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert result is True
    service._fetch_top_user_limit_entry.assert_called_once()


@pytest.mark.asyncio
async def test_check_group_limit_active_users_no_tokens_other_user_has(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(chat_id=chat_id, last_ref_time=current_time, remain_tokens=50)

    active_user = UserGroupLimitEntry(
        user_id=789,
        last_ref_time=current_time,
        remain_tokens=0,
    )

    inactive_user = UserGroupLimitEntry(
        user_id=101,
        last_ref_time=current_time,
        remain_tokens=300,
    )

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[active_user, inactive_user])

    min_tokens = (
        1 - default_limits_config.group_per_user_max_other_usage_coeff
    ) * default_limits_config.group_per_user_tokens_limit

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert inactive_user.remain_tokens > min_tokens
    assert result is True
    assert service._fetch_top_user_limit_entry.call_count == 2


@pytest.mark.asyncio
async def test_check_group_limit_all_users_insufficient_tokens(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    chat_id = 456
    current_time = int(time.time())

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    service._update_user_contact_and_create_limit_entry = AsyncMock()
    service._update_group_members_limits = AsyncMock()

    group_limit = GroupLimitEntry(chat_id=chat_id, last_ref_time=current_time, remain_tokens=50)

    active_user = UserGroupLimitEntry(
        user_id=789,
        last_ref_time=current_time,
        remain_tokens=0,
    )

    inactive_user = UserGroupLimitEntry(
        user_id=101,
        last_ref_time=current_time,
        remain_tokens=5,
    )

    service._create_or_fetch_group_limit_entry = AsyncMock(return_value=group_limit)
    service._fetch_top_user_limit_entry = AsyncMock(side_effect=[active_user, inactive_user])

    min_tokens = (
        1 - default_limits_config.group_per_user_max_other_usage_coeff
    ) * default_limits_config.group_per_user_tokens_limit

    with patch("time.time", return_value=current_time):
        result = await service.check_group_limit(user_id, chat_id)

    assert inactive_user.remain_tokens <= min_tokens
    assert result is False
    assert service._fetch_top_user_limit_entry.call_count == 2


@pytest.mark.asyncio
async def test_update_group_members_limits(
    default_limits_config, mock_db_session, mock_support_service
):
    chat_id = 456
    min_last_contacted_time = 100
    current_time = int(time.time())

    user_ids_result = MagicMock()
    user_ids_result.all.return_value = [(101,), (202,)]

    supporter_ids_result = MagicMock()
    supporter_ids_result.all.return_value = [(202,)]

    mock_db_session.execute = AsyncMock(
        side_effect=[user_ids_result, supporter_ids_result, None, None]
    )

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    with patch("time.time", return_value=current_time):
        await service._update_group_members_limits(chat_id, min_last_contacted_time)

    assert mock_db_session.execute.call_count == 4
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_private_limit_no_tokens_left(
    default_limits_config, mock_db_session, mock_support_service
):
    user_id = 123
    current_time = int(time.time())

    limit_entry = UserPrivateLimitEntry(
        user_id=user_id,
        last_ref_time=current_time,
        remain_tokens=0,
    )

    mock_db_session.get.return_value = limit_entry

    service = DefaultLimitsService(mock_db_session, default_limits_config, mock_support_service)

    result = await service.check_private_limit(user_id)

    assert result is False
    mock_db_session.commit.assert_not_called()
