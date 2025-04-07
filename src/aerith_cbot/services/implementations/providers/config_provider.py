from dishka import Provider, Scope, provide

from aerith_cbot.config import (
    BotConfig,
    Config,
    DbConfig,
    LimitsConfig,
    LLMConfig,
    OpenAIConfig,
    QdrantConfig,
    SupportConfig,
    YooKassaConfig,
)


class ConfigProvider(Provider):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    @provide(scope=Scope.APP)
    def llm_config(self) -> LLMConfig:
        return self.config.llm

    @provide(scope=Scope.APP)
    def db_config(self) -> DbConfig:
        return self.config.db

    @provide(scope=Scope.APP)
    def bot_config(self) -> BotConfig:
        return self.config.bot

    @provide(scope=Scope.APP)
    def qdrant_config(self) -> QdrantConfig:
        return self.config.qdrant

    @provide(scope=Scope.APP)
    def openai_config(self) -> OpenAIConfig:
        return self.config.openai

    @provide(scope=Scope.APP)
    def limits_config(self) -> LimitsConfig:
        return self.config.limits

    @provide(scope=Scope.APP)
    def yookassa_config(self) -> YooKassaConfig:
        return self.config.yookassa

    @provide(scope=Scope.APP)
    def support_config(self) -> SupportConfig:
        return self.config.support
