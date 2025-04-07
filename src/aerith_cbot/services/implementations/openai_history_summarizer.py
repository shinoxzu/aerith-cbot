import logging

from openai import AsyncClient

from aerith_cbot.config import LLMConfig, OpenAIConfig
from aerith_cbot.services.abstractions import HistorySummarizer


class OpenAIHistorySummarizer(HistorySummarizer):
    def __init__(
        self,
        openai_client: AsyncClient,
        openai_config: OpenAIConfig,
        llm_config: LLMConfig,
    ) -> None:
        self._openai_client = openai_client
        self._openai_config = openai_config
        self._llm_config = llm_config

        self._logger = logging.getLogger(__name__)

    async def summarize(self, messages_to_summarize: list[dict]) -> str:
        messages = (
            [{"role": "developer", "content": self._llm_config.summarize_instruction}]
            + messages_to_summarize
            + [{"role": "developer", "content": self._llm_config.summarize_instruction}]
        )

        content = ""

        try:
            result = await self._openai_client.chat.completions.create(
                model=self._openai_config.summarizer_model,
                messages=messages,  # type: ignore
            )

            if result.choices[0].message.refusal is not None:
                self._logger.warning("Refusal in %s: %s", result.choices[0].message.refusal)

            elif result.choices[0].message.content is not None:
                content = result.choices[0].message.content

        except Exception as err:
            self._logger.error("Cannot shorten messages cause of %s", err, exc_info=err)

        return content
