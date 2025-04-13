from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Request, Response
from openai import APIError, RateLimitError
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call_param import Function

from aerith_cbot.config import LimitsConfig
from aerith_cbot.services.abstractions import SupportService
from aerith_cbot.services.abstractions.models import ChatType
from aerith_cbot.services.implementations import DefaultLimitsService, DefaultUserContextProvider
from aerith_cbot.services.implementations.processors import DefaultChatProcessor
from aerith_cbot.services.implementations.processors.tools import ToolExecutionResult


@pytest.fixture
def mock_dependencies(default_limits_config: LimitsConfig):
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create = AsyncMock()

    mock_llm_config = MagicMock()
    mock_llm_config.tools = [{"type": "function", "function": {"name": "test_tool"}}]
    mock_llm_config.group_tools = [{"type": "function", "function": {"name": "group_tool"}}]
    mock_llm_config.response_schema = {"type": "json_object"}
    mock_llm_config.group_instruction = "Be helpful and concise."

    mock_openai_config = MagicMock()
    mock_openai_config.model = "gpt-4"

    mock_tool_dispatcher = MagicMock()
    mock_tool_dispatcher.execute_tool = AsyncMock()

    mock_model_response_processor = MagicMock()
    mock_model_response_processor.process = AsyncMock()
    mock_model_response_processor.process_refusal = AsyncMock()

    mock_message_service = MagicMock()
    mock_message_service.fetch_messages = AsyncMock(return_value=[])
    mock_message_service.add_messages = AsyncMock()
    mock_message_service.shorten_history = AsyncMock()
    mock_message_service.shorten_full_history_without_media = AsyncMock()

    mock_limits_service = MagicMock(spec=DefaultLimitsService)
    mock_limits_service.subtract_private_tokens = AsyncMock()
    mock_limits_service.subtract_group_tokens = AsyncMock()

    mock_context_provider = MagicMock(spec=DefaultUserContextProvider)
    mock_context_provider.provide_context = AsyncMock()

    mock_support_service = MagicMock(spec=SupportService)

    return {
        "openai_client": mock_openai_client,
        "llm_config": mock_llm_config,
        "openai_config": mock_openai_config,
        "tool_dispatcher": mock_tool_dispatcher,
        "message_service": mock_message_service,
        "limits_serivce": mock_limits_service,
        "limits_config": default_limits_config,
        "context_provider": mock_context_provider,
        "model_response_processor": mock_model_response_processor,
        "support_service": mock_support_service,
    }


@pytest.fixture
def mock_chat_completion():
    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = (
        '{"text": ["Hello, this is a test response"], "reply_to_message_id": null, "sticker": null}'
    )
    mock_message.refusal = None
    mock_message.tool_calls = None
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": mock_message.content,
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message

    mock_completion.usage = MagicMock(spec=CompletionUsage)
    mock_completion.usage.prompt_tokens = 100
    mock_completion.usage.completion_tokens = 50
    mock_completion.usage.total_tokens = 150
    mock_completion.usage.prompt_tokens_details = None

    return mock_completion


@pytest.mark.asyncio
async def test_basic_chat_processing(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies
    deps["openai_client"].chat.completions.create.return_value = mock_chat_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["message_service"].fetch_messages.assert_called_once_with(123)

    deps["openai_client"].chat.completions.create.assert_called_once()

    call_args = deps["openai_client"].chat.completions.create.call_args
    assert call_args[1]["tools"] == deps["llm_config"].tools

    deps["model_response_processor"].process.assert_called_once()
    deps["message_service"].add_messages.assert_called_once()
    deps["tool_dispatcher"].execute_tool.assert_not_called()


@pytest.mark.asyncio
async def test_group_chat_uses_group_tools(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies
    deps["openai_client"].chat.completions.create.return_value = mock_chat_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.group)

    call_args = deps["openai_client"].chat.completions.create.call_args
    assert call_args[1]["tools"] == deps["llm_config"].tools + deps["llm_config"].group_tools


@pytest.mark.asyncio
async def test_processing_with_refusal(mock_dependencies):
    deps = mock_dependencies

    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = None
    mock_message.refusal = "I cannot help with illegal activities."
    mock_message.tool_calls = None
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "refusal": "I cannot help with illegal activities.",
        "content": None,
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=100)

    deps["openai_client"].chat.completions.create.return_value = mock_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["model_response_processor"].process_refusal.assert_called_once()
    deps["model_response_processor"].send_model_response.assert_not_called()


@pytest.mark.asyncio
async def test_tool_stops_processing(mock_dependencies):
    deps = mock_dependencies

    mock_function = MagicMock(spec=Function)
    mock_function.name = "ignore_message"
    mock_function.arguments = "{}"

    mock_tool_call = MagicMock(spec=ChatCompletionMessageToolCall)
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function

    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = None
    mock_message.refusal = None
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "ignore_message", "arguments": "{}"},
            }
        ],
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=200)

    deps["openai_client"].chat.completions.create.return_value = mock_completion
    deps["tool_dispatcher"].execute_tool.return_value = ToolExecutionResult(
        response="Ignoring message",
        stop=True,
    )

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    assert deps["openai_client"].chat.completions.create.call_count == 1


@pytest.mark.asyncio
async def test_validation_error_handling(mock_dependencies):
    deps = mock_dependencies

    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = "This is not a valid JSON"
    mock_message.refusal = None
    mock_message.tool_calls = None
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": "This is not a valid JSON",
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=200)

    deps["openai_client"].chat.completions.create.return_value = mock_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["message_service"].add_messages.assert_called_once()
    deps["model_response_processor"].process.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_retry(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies

    rate_limit_error = RateLimitError(
        message="", response=Response(status_code=0, request=Request(method="", url="")), body=None
    )

    deps["openai_client"].chat.completions.create.side_effect = [
        rate_limit_error,
        mock_chat_completion,
    ]

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    assert deps["openai_client"].chat.completions.create.call_count == 2

    # call in _get_llm_response and main loop
    deps["message_service"].shorten_history.assert_called_with(123)
    assert deps["message_service"].shorten_history.call_count == 2

    deps["model_response_processor"].process.assert_called_once()


@pytest.mark.asyncio
async def test_api_error_retry(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies

    api_error = APIError(message="", request=Request(method="", url=""), body=None)

    deps["openai_client"].chat.completions.create.side_effect = [api_error, mock_chat_completion]

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    with patch("asyncio.sleep", AsyncMock()) as sleep_mock:
        await processor.process(chat_id=123, chat_type=ChatType.private)

        sleep_mock.assert_called_once()
        deps["model_response_processor"].process.assert_called_once()
        assert deps["openai_client"].chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_max_token_usage_triggers_shortening(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies

    mock_chat_completion.usage.prompt_tokens = deps["limits_config"].group_max_context_tokens + 100
    deps["openai_client"].chat.completions.create.return_value = mock_chat_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.group)

    deps["message_service"].shorten_history.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_max_iterations_limit(mock_dependencies):
    deps = mock_dependencies

    mock_function = MagicMock(spec=Function)
    mock_function.name = "test_tool"
    mock_function.arguments = "{}"

    mock_tool_call = MagicMock(spec=ChatCompletionMessageToolCall)
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function

    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = None
    mock_message.refusal = None
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_tool", "arguments": "{}"},
            }
        ],
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=200)

    deps["openai_client"].chat.completions.create.return_value = mock_completion
    deps["tool_dispatcher"].execute_tool.return_value = ToolExecutionResult(
        response="Tool executed",
        stop=False,
    )

    original_max_iterations = DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS

    DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS = 3  # type: ignore

    try:
        processor = DefaultChatProcessor(
            deps["openai_client"],
            deps["llm_config"],
            deps["openai_config"],
            deps["tool_dispatcher"],
            deps["message_service"],
            deps["limits_config"],
            deps["context_provider"],
            deps["limits_serivce"],
            deps["model_response_processor"],
            deps["support_service"],
        )

        await processor.process(chat_id=123, chat_type=ChatType.private)

        assert deps["openai_client"].chat.completions.create.call_count == 3
        assert deps["tool_dispatcher"].execute_tool.call_count == 3
    finally:
        DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS = original_max_iterations


@pytest.mark.asyncio
async def test_exception_in_tool_execution(mock_dependencies):
    deps = mock_dependencies

    mock_function = MagicMock(spec=Function)
    mock_function.name = "test_tool"
    mock_function.arguments = "{}"

    mock_tool_call = MagicMock(spec=ChatCompletionMessageToolCall)
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_tool_call.function = mock_function

    mock_message = MagicMock(spec=ChatCompletionMessage)
    mock_message.content = None
    mock_message.refusal = None
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_tool", "arguments": "{}"},
            }
        ],
    }

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message = mock_message
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=200)

    deps["openai_client"].chat.completions.create.return_value = mock_completion

    deps["tool_dispatcher"].execute_tool.side_effect = Exception("Tool execution failed")

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["message_service"].add_messages.assert_called_once()

    add_messages_call_args = deps["message_service"].add_messages.call_args
    messages = add_messages_call_args[0][1]

    tool_response_message = messages[2]
    assert tool_response_message["role"] == "tool"
    assert tool_response_message["tool_call_id"] == "call_123"
    assert tool_response_message["content"] == ""


@pytest.mark.asyncio
async def test_exception_in_response_processor_service(mock_dependencies, mock_chat_completion):
    deps = mock_dependencies
    deps["openai_client"].chat.completions.create.return_value = mock_chat_completion

    deps["model_response_processor"].process.side_effect = Exception("Failed to send message")

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["message_service"].add_messages.assert_called_once()


@pytest.mark.asyncio
async def test_retry_limit_exceeded(mock_dependencies):
    deps = mock_dependencies

    rate_limit_error = RateLimitError(
        message="", response=Response(status_code=0, request=Request(method="", url="")), body=None
    )
    deps["openai_client"].chat.completions.create.side_effect = rate_limit_error

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    try:
        await processor.process(chat_id=123, chat_type=ChatType.private)
    except Exception:
        pass

    assert (
        deps["openai_client"].chat.completions.create.call_count
        == DefaultChatProcessor.MAX_LLM_CALL_ATTEMPTS
    )

    assert (
        deps["message_service"].shorten_history.call_count
        == DefaultChatProcessor.MAX_LLM_CALL_ATTEMPTS
    )

    deps["message_service"].add_messages.assert_not_called()


@pytest.mark.asyncio
async def test_no_choices_in_completion(mock_dependencies):
    deps = mock_dependencies

    mock_completion = MagicMock(spec=ChatCompletion)
    mock_completion.choices = []
    mock_completion.usage = MagicMock(prompt_tokens=100, total_tokens=200)

    deps["openai_client"].chat.completions.create.return_value = mock_completion

    processor = DefaultChatProcessor(
        deps["openai_client"],
        deps["llm_config"],
        deps["openai_config"],
        deps["tool_dispatcher"],
        deps["message_service"],
        deps["limits_config"],
        deps["context_provider"],
        deps["limits_serivce"],
        deps["model_response_processor"],
        deps["support_service"],
    )

    await processor.process(chat_id=123, chat_type=ChatType.private)

    deps["message_service"].add_messages.assert_called_once()

    deps["model_response_processor"].process.assert_not_called()
    deps["model_response_processor"].process_refusal.assert_not_called()
