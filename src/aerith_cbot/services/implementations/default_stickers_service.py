import random

import emoji
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import Sticker
from aerith_cbot.services.abstractions import StickersService
from aerith_cbot.services.abstractions.models import StickerDTO


class DefaultStickersService(StickersService):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session

    async def load(self, stickers: list[StickerDTO]) -> None:
        models = []
        for sticker_dto in stickers:
            models.append(
                Sticker(
                    file_id=sticker_dto.file_id,
                    emoji=sticker_dto.emoji,
                    set_name=sticker_dto.set_name,
                )
            )

        self._db_session.add_all(models)
        await self._db_session.commit()

    async def search(self, emoji: str) -> str | None:
        stmt = select(Sticker.file_id).where(Sticker.emoji == emoji)
        file_ids_raw = await self._db_session.execute(stmt)
        file_ids = list(file_ids_raw.scalars())

        if file_ids:
            return random.choice(file_ids)

    def is_valid_emoji(self, emoji_string: str) -> bool:
        return len(emoji_string) == 1 and emoji.emoji_count(emoji_string) == 1
