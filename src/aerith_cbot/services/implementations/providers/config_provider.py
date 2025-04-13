from dishka import Provider, Scope, provide

from aerith_cbot.config import (
    BotConfig,
    ChromaConfig,
    Config,
    DbConfig,
    LimitsConfig,
    LLMConfig,
    OpenAIConfig,
    SupportConfig,
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
    def chroma_config(self) -> ChromaConfig:
        return self.config.chroma

    @provide(scope=Scope.APP)
    def openai_config(self) -> OpenAIConfig:
        return self.config.openai

    @provide(scope=Scope.APP)
    def limits_config(self) -> LimitsConfig:
        return self.config.limits

    @provide(scope=Scope.APP)
    def support_config(self) -> SupportConfig:
        return self.config.support
