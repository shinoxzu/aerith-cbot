from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from aerith_cbot.config import DbConfig


class DataBaseProvider(Provider):
    @provide(scope=Scope.APP)
    def engine(self, db_config: DbConfig) -> AsyncEngine:
        return create_async_engine(db_config.connection_string)

    @provide(scope=Scope.REQUEST)
    async def session(self, engine: AsyncEngine) -> AsyncIterable[AsyncSession]:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session
