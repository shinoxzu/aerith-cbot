from abc import ABC, abstractmethod


class HistorySummarizer(ABC):
    @abstractmethod
    async def summarize(self, messages_to_summarize: list[dict]) -> str:
        raise NotImplementedError
