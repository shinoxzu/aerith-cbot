from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.services.implementations import DefaultChatMigrationService


@pytest.mark.asyncio
async def test_migrate_chat():
    mock_db_session = MagicMock(spec=AsyncSession)
    mock_db_session.execute = AsyncMock()
    mock_db_session.commit = AsyncMock()

    chat_migration_service = DefaultChatMigrationService(db_session=mock_db_session)
    await chat_migration_service.update(-100123, -100456)

    assert mock_db_session.execute.call_count == 4
    mock_db_session.commit.assert_called_once()
