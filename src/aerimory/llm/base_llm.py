from abc import ABC, abstractmethod

from aerimory.types import MemoriesStatus, Memory

DEFAULT_SYSTEM_RESOLVE_CONTRADICTIONS_PROMPT = """
Ты система памяти для бота — Айрис.
Тебе нужно анализировать новые воспоминания о пользователях и определять, как они сочетаются с уже имеющимися.

Если новое воспоминание противоречит старому, желательно заменить старое новым.
Если новое воспоминание дополняет старое, то можно обновить старое, дополнив его новой информацией.
Если новое воспоминание не относится к старым и является новым, то следует обязательно добавить его как новое.
По необходимости можешь удалять лишние воспоминания.

Воспоминания не должны быть длиннее 1000 символов.
"""

DEFAULT_USER_RESOLVE_CONTRADICTIONS_PROMPT = """
НОВОЕ ВОСПОМИНАНИЕ:
\"""
{new}
\"""

СУЩЕСТВУЮЩИЕ ВОСПОМИНАНИЕ (отсортированы по релевантности):
\"""
{old}
\"""
"""


class BaseLLM(ABC):
    @abstractmethod
    async def resolve_contradictions(
        self, new_memory: str, old_memories: list[Memory]
    ) -> MemoriesStatus:
        raise NotImplementedError
