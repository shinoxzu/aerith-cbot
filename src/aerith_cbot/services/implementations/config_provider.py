from dishka import Provider, Scope, provide

from aerith_cbot.config import (
    BotConfig,
    Config,
    DbConfig,
    LLMConfig,
    Neo4jConfig,
    OpenAIConfig,
    QdrantConfig,
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
    def neo4j_config(self) -> Neo4jConfig:
        return self.config.neo4j

    @provide(scope=Scope.APP)
    def qdrant_config(self) -> QdrantConfig:
        return self.config.qdrant

    @provide(scope=Scope.APP)
    def openai_config(self) -> OpenAIConfig:
        return self.config.openai
