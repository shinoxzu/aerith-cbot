from abc import ABC, abstractmethod

from aerith_cbot.services.abstractions.models import InputMessage


class GroupMessageProcessor(ABC):
    @abstractmethod
    async def process(self, message: InputMessage) -> None:
        raise NotImplementedError
