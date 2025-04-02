from abc import ABC, abstractmethod


class PermissionChecker(ABC):
    @abstractmethod
    async def check_permissions(self, chat_id: int, user_id: int) -> bool:
        raise NotImplementedError
