import logging

from pydantic.main import BaseModel

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions.user_context_provider import UserContextProvider
from aerith_cbot.services.implementations.processors.tools.base import ToolCommand


class UpdateUserContextParams(BaseModel):
    user_id: int
    context: str


class UpdateUserContextCommand(ToolCommand):
    def __init__(self, context_provider: UserContextProvider, llm_config: LLMConfig) -> None:
        super().__init__()

        self._context_provider = context_provider
        self._logger = logging.getLogger(__name__)
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = UpdateUserContextParams.model_validate_json(arguments)
        await self._context_provider.update_context(params.user_id, params.context)

        return self._llm_config.additional_instructions.info_saved
