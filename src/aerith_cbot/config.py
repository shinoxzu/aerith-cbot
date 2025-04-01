import json
import tomllib

from pydantic import BaseModel


class LLMConfig(BaseModel):
    response_schema: dict
    group_tools: list
    tools: list
    group_instruction: str
    private_instruction: str
    summarize_instruction: str


class OpenAIConfig(BaseModel):
    token: str
    model: str
    summarizer_model: str
    memory_llm_model: str
    memory_embedder_model: str


class QdrantConfig(BaseModel):
    collection_name: str
    host: str
    port: int


class DbConfig(BaseModel):
    connection_string: str


class BotConfig(BaseModel):
    token: str
    api_id: int
    api_hash: str


class Config(BaseModel):
    db: DbConfig
    bot: BotConfig
    qdrant: QdrantConfig
    openai: OpenAIConfig
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
    )
