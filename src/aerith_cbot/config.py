import json
import tomllib

from pydantic import BaseModel


class BotConfig(BaseModel):
    token: str
    admin_ids: list[int]
    help_article: str


class DbConfig(BaseModel):
    connection_string: str


class OpenAIConfig(BaseModel):
    token: str
    group_model: str
    private_model: str
    private_support_model: str
    summarizer_model: str
    memory_llm_model: str
    memory_embedder_model: str


class LimitsConfig(BaseModel):
    # лимиты на группу
    group_cooldown: int
    group_generic_tokens_limit: int
    group_per_user_tokens_limit: int
    group_per_support_user_tokens_limit: int
    group_per_user_max_other_usage_coeff: float

    # лимиты на ЛС
    private_cooldown: int
    private_tokens_limit: int
    private_support_tokens_limit: int

    group_max_context_tokens: int
    private_max_context_tokens: int
    private_support_max_context_tokens: int


class SupportConfig(BaseModel):
    price: int
    price_for_telegram: int
    currency: str
    duration: int
    nearest_buy_interval: int
    provider_token: str


class ChromaConfig(BaseModel):
    host: str
    port: int


class AdditionalInstructions(BaseModel):
    msg_pinned: str
    descr_edited: str
    name_changed: str
    user_kicked: str
    user_hasnt_rights: str
    aerith_hasnt_rights: str
    info_not_found: str
    info_saved: str
    aerith_has_mentioned: str
    limit_in_group: str
    limit_in_private: str
    limit_in_private_end: str
    chat_unfocused_by_request: str
    you_call_too_many_tools: str
    aerith_chat_join: str


class LLMConfig(BaseModel):
    response_schema: dict
    group_tools: list
    tools: list
    group_instruction: str
    private_instruction: str
    summarize_instruction: str
    additional_instructions: AdditionalInstructions


class Config(BaseModel):
    bot: BotConfig
    db: DbConfig
    openai: OpenAIConfig
    limits: LimitsConfig
    support: SupportConfig
    chroma: ChromaConfig
    llm: LLMConfig


def load_config(path: str, llm_path: str) -> Config:
    with open(path, encoding="utf-8") as f:
        config_dict = tomllib.loads(f.read())

    config_dict["llm"] = load_llm_config(llm_path)

    return Config.model_validate(config_dict)


def load_llm_config(path: str) -> LLMConfig:
    with open(path + "/response_schema.json", encoding="utf-8") as f:
        response_schema = json.loads(f.read())

    with open(path + "/instructions/group_instruction.md", encoding="utf-8") as f:
        group_instruction = f.read()

    with open(path + "/instructions/private_instruction.md", encoding="utf-8") as f:
        private_instruction = f.read()

    with open(path + "/instructions/summarize_instruction.md", encoding="utf-8") as f:
        summarize_instruction = f.read()

    with open(path + "/instructions/additional_instructions.json", encoding="utf-8") as f:
        additional_instructions = f.read()

    with open(path + "/tools/group_tools.json", encoding="utf-8") as f:
        group_tools = json.loads(f.read())["tools"]

    with open(path + "/tools/tools.json", encoding="utf-8") as f:
        tools = json.loads(f.read())["tools"]

    return LLMConfig(
        response_schema=response_schema,
        group_instruction=group_instruction,
        private_instruction=private_instruction,
        group_tools=group_tools,
        tools=tools,
        summarize_instruction=summarize_instruction,
        additional_instructions=AdditionalInstructions.model_validate_json(additional_instructions),
    )
