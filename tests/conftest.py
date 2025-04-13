import pytest

from aerith_cbot.config import AdditionalInstructions, LimitsConfig, LLMConfig
from aerith_cbot.services.abstractions.models import InputChat, InputMessage, InputUser


@pytest.fixture
def default_message_to_process() -> InputMessage:
    return InputMessage(
        id=1,
        chat=InputChat(id=1, name="чат друзей"),
        sender=InputUser(id=1, name="Петя"),
        reply_message=None,
        photo_url=None,
        voice_url=None,
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
        additional_instructions=AdditionalInstructions(
            descr_edited="",
            name_changed="",
            user_hasnt_rights="",
            aerith_hasnt_rights="",
            info_not_found="",
            user_kicked="",
            msg_pinned="",
            info_saved="",
            aerith_has_mentioned="",
            limit_in_group="",
            limit_in_private="",
            chat_unfocused_by_request="",
        ),
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
        group_per_support_user_tokens_limit=1,
        private_support_tokens_limit=1,
        group_max_context_tokens=1,
        private_max_context_tokens=1,
        private_support_max_context_tokens=1,
    )
