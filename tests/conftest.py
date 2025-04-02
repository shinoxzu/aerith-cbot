import pytest

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser


@pytest.fixture
def default_message_to_process() -> InputMessage:
    return InputMessage(
        id=1,
        chat=InputChat(id=1, name="чат друзей"),
        sender=InputUser(id=1, name="Петя"),
        reply_message=None,
        photo_url=None,
        text="привет",
        date="1 января, 2025",
        contains_aerith_mention=False,
    )


@pytest.fixture
def default_llm_config() -> LLMConfig:
    return LLMConfig(
        response_schema={},
        group_tools=[],
        tools=[],
        group_instruction="",
        private_instruction="",
        summarize_instruction="",
    )
