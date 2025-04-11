import asyncio

from aiogram import Bot
from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.aiogram import AiogramProvider

from aerith_cbot.config import Config
from aerith_cbot.database import DataBaseProvider
from aerith_cbot.services.abstractions import (
    HistorySummarizer,
    LimitsService,
    MemoryService,
    MessageService,
    PermissionChecker,
    SenderService,
    StickersService,
    SupportService,
    VoiceTranscriber,
)
from aerith_cbot.services.abstractions.processors import (
    ChatProcessor,
    GroupMessageProcessor,
    PrivateMessageProcessor,
)
from aerith_cbot.services.implementations import (
    AerimoryMemoryService,
    DefaultLimitsService,
    DefaultMessageService,
    DefaultSenderService,
    DefaultStickersService,
    DefaultSupportService,
    GroupPermissionChecker,
    OpenAIHistorySummarizer,
    OpenAIVoiceTranscriber,
    SupportNotifier,
)
from aerith_cbot.services.implementations.chat_dispatcher import ChatDispatcher, MessageQueue
from aerith_cbot.services.implementations.processors import (
    DefaultChatProcessor,
    DefaultGroupMessageProcessor,
    DefaultPrivateMessageProcessor,
)
from aerith_cbot.services.implementations.processors.tools import (
    DefaultToolCommandDispatcher,
    ToolCommandDispatcher,
)
from aerith_cbot.services.implementations.providers import ClientsProvider, ConfigProvider


async def init_dishka_container(config: Config, bot: Bot) -> AsyncContainer:
    service_provider = Provider(scope=Scope.REQUEST)

    service_provider.provide(SupportNotifier, scope=Scope.APP)
    service_provider.provide(ChatDispatcher, scope=Scope.APP)
    service_provider.provide(MessageQueue, scope=Scope.APP)
    service_provider.provide(OpenAIVoiceTranscriber, provides=VoiceTranscriber)
    service_provider.provide(DefaultSupportService, provides=SupportService)
    service_provider.provide(DefaultLimitsService, provides=LimitsService)
    service_provider.provide(DefaultToolCommandDispatcher, provides=ToolCommandDispatcher)
    service_provider.provide(GroupPermissionChecker, provides=PermissionChecker)
    service_provider.provide(OpenAIHistorySummarizer, provides=HistorySummarizer)
    service_provider.provide(DefaultMessageService, provides=MessageService)
    service_provider.provide(DefaultPrivateMessageProcessor, provides=PrivateMessageProcessor)
    service_provider.provide(DefaultGroupMessageProcessor, provides=GroupMessageProcessor)
    service_provider.provide(DefaultChatProcessor, provides=ChatProcessor)
    service_provider.provide(DefaultSenderService, provides=SenderService)
    service_provider.provide(DefaultStickersService, provides=StickersService)
    service_provider.provide(AerimoryMemoryService, provides=MemoryService)
    service_provider.provide(lambda: bot, scope=Scope.APP, provides=Bot)

    container = make_async_container(
        service_provider,
        ConfigProvider(config),
        DataBaseProvider(),
        ClientsProvider(),
        AiogramProvider(),
    )

    await _run_bg_workers(container)

    return container


async def _run_bg_workers(container: AsyncContainer) -> None:
    chat_dispatcher = await container.get(ChatDispatcher)
    chat_dispatcher.run_task = asyncio.create_task(chat_dispatcher.run())

    support_notifier = await container.get(SupportNotifier)
    support_notifier.run_task = asyncio.create_task(support_notifier.run())
