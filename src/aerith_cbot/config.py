import json
import tomllib

from pydantic import BaseModel


class BotConfig(BaseModel):
    token: str
    admin_ids: list[int]


class DbConfig(BaseModel):
    connection_string: str


class OpenAIConfig(BaseModel):
    token: str
    model: str
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

    max_context_tokens: int


class SupportConfig(BaseModel):
    price: int
    duration: int
    provider_token: str


class QdrantConfig(BaseModel):
    collection_name: str
    host: str
    port: int


class AdditionalInstructions(BaseModel):
    descr_edited: str
    user_hasnt_desc_rights: str
    name_changed: str
    user_hasnt_name_rights: str
    info_not_found: str
    msg_ignored: str
    user_kicked: str
    user_hasnt_rights_kick: str
    msg_pinned: str
    info_saved: str
    too_long_listening: str
    user_not_completed_thought: str
    aerith_has_mentioned: str
    limit_in_group: str
    limit_in_private: str
    info_about_user: str


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
    qdrant: QdrantConfig
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
