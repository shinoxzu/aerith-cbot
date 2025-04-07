import pytest

from aerith_cbot.config import LimitsConfig, LLMConfig
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


@pytest.fixture
def default_limits_config() -> LimitsConfig:
    return LimitsConfig(
        group_cooldown=1,
        group_generic_tokens_limit=500,
        group_per_user_tokens_limit=500,
        group_per_user_max_other_usage_coeff=0.5,
        private_cooldown=1,
        private_tokens_limit=1,
        max_context_tokens=1,
        group_per_support_user_tokens_limit=1,
        private_support_tokens_limit=1,
    )
