from aiogram import Bot
from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.aiogram import AiogramProvider

from aerith_cbot.config import Config
from aerith_cbot.database import DataBaseProvider
from aerith_cbot.services.abstractions import (
    GroupMessageProcessor,
    MemoryService,
    PrivateMessageProcessor,
    SenderService,
    StickersService,
)
from aerith_cbot.services.implementations import (
    ClientsProvider,
    ConfigProvider,
    DefaultSenderService,
    DefaultStickersService,
    Mem0MemoryService,
    OpenAIGroupMessageProcessor,
    OpenAIPrivateMessageProcessor,
    ToolCommandDispatcher,
)


async def init_dishka_container(config: Config, bot: Bot) -> AsyncContainer:
    service_provider = Provider(scope=Scope.REQUEST)

    service_provider.provide(DefaultSenderService, provides=SenderService)
    service_provider.provide(DefaultStickersService, provides=StickersService)
    service_provider.provide(OpenAIPrivateMessageProcessor, provides=PrivateMessageProcessor)
    service_provider.provide(OpenAIGroupMessageProcessor, provides=GroupMessageProcessor)
    service_provider.provide(Mem0MemoryService, provides=MemoryService)
    service_provider.provide(ToolCommandDispatcher)
    service_provider.provide(lambda: bot, scope=Scope.APP, provides=Bot)

    return make_async_container(
        service_provider,
        ConfigProvider(config),
        DataBaseProvider(),
        ClientsProvider(),
        AiogramProvider(),
    )
