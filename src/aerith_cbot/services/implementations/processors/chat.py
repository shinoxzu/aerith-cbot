import asyncio
import logging

from openai import APIError, AsyncOpenAI, BadRequestError, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall
from pydantic import ValidationError

from aerith_cbot.config import LimitsConfig, LLMConfig, OpenAIConfig
from aerith_cbot.services.abstractions import LimitsService, MessageService, SenderService
from aerith_cbot.services.abstractions.models import (
    ChatType,
    ModelResponse,
)
from aerith_cbot.services.abstractions.processors import ChatProcessor
from aerith_cbot.services.implementations.processors.tools import ToolCommandDispatcher


class DefaultChatProcessor(ChatProcessor):
    MAX_LLM_CALL_ATTEMPTS = 3
    MAX_LLM_CALL_ITERATIONS = 10
    MAX_TOOL_CALL_ITERATIONS = 10

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        llm_config: LLMConfig,
        openai_config: OpenAIConfig,
        tool_command_dispatcher: ToolCommandDispatcher,
        sender_service: SenderService,
        message_service: MessageService,
        limits_service: LimitsService,
        limits_config: LimitsConfig,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._openai_client = openai_client
        self._llm_config = llm_config
        self._openai_config = openai_config
        self._tool_command_dispatcher = tool_command_dispatcher
        self._sender_service = sender_service
        self._message_service = message_service
        self._limits_config = limits_config
        self._limits_service = limits_service

    async def process(self, chat_id: int, chat_type: ChatType) -> None:
        old_messages: list[dict] = await self._message_service.fetch_messages(chat_id)
        new_messages: list[dict] = []

        try:
            if chat_type == ChatType.group:
                tools = self._llm_config.tools + self._llm_config.group_tools
                instruction_messages = [
                    {"role": "developer", "content": self._llm_config.group_instruction}
                ]
            elif chat_type == ChatType.private:
                tools = self._llm_config.tools
                instruction_messages = [
                    {"role": "developer", "content": self._llm_config.private_instruction}
                ]

            tool_stop = False
            result = None
            current_iterations = 0
            current_tool_calls = 0

            while (
                current_iterations < DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS and not tool_stop
            ):
                result = await self._get_llm_response(
                    chat_id,
                    instruction_messages,
                    old_messages,
                    new_messages,
                    tools,
                )

                self._logger.debug("LLM response in %s: %s", chat_id, result)

                if not result.choices:
                    break

                new_messages.append(result.choices[0].message.model_dump())

                await self._process_llm_text_response(result, chat_id)

                # if the model does not have tool_calls, we have processed the response
                # and the loop can be broken
                if not result.choices[0].message.tool_calls:
                    break

                self._logger.info(
                    "Tool calls to call in %s (total: %s): %s",
                    chat_id,
                    len(result.choices[0].message.tool_calls),
                    result.choices[0].message.tool_calls,
                )

                # call all functions in one response
                for tool_call in result.choices[0].message.tool_calls:
                    tool_response, tool_stop = await self._process_llm_tool_call(chat_id, tool_call)

                    new_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_response,
                        },
                    )

                    current_tool_calls += 1

                    if current_tool_calls >= DefaultChatProcessor.MAX_TOOL_CALL_ITERATIONS:
                        current_iterations = DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS

                        self._logger.warning(
                            "Tool call limit in %s (last_call: %s)", chat_id, tool_call
                        )

                        break

                current_iterations += 1

            await self._message_service.add_messages(chat_id, new_messages)

            # TODO: subtract sum of results, not the last one only
            if result is not None:
                if result.usage is not None:
                    self._logger.debug(
                        "Usage in chat %s (%s): %s", chat_id, chat_type.name, result.usage
                    )

                    if result.usage.total_tokens > self._limits_config.max_context_tokens:
                        self._logger.info(
                            "Usage in chat %s (%s) above limit (%s>%s); shortening history",
                            chat_id,
                            chat_type,
                            result.usage.total_tokens,
                            self._limits_config.max_context_tokens,
                        )
                        await self._message_service.shorten_history(chat_id)

                    # we will always get details in response, but in case of
                    # some errors we will count tokens in the other way
                    if (
                        result.usage.prompt_tokens_details is not None
                        and result.usage.prompt_tokens_details.cached_tokens is not None
                    ):
                        new_prompt_tokens = (
                            result.usage.prompt_tokens
                            - result.usage.prompt_tokens_details.cached_tokens
                        )
                        tokens_to_subtract = new_prompt_tokens + result.usage.completion_tokens
                    else:
                        tokens_to_subtract = (
                            result.usage.completion_tokens + result.usage.prompt_tokens // 2
                        )

                    self._logger.info(
                        "Chat %s (%s) has used %s tokens in this request",
                        chat_id,
                        chat_type,
                        tokens_to_subtract,
                    )

                    if chat_type == ChatType.group:
                        await self._limits_service.subtract_group_tokens(
                            chat_id, tokens_to_subtract
                        )
                    elif chat_type == ChatType.private:
                        await self._limits_service.subtract_private_tokens(
                            chat_id, tokens_to_subtract
                        )
        except Exception as e:
            self._logger.error("Cannot process chat %s cause of %s", chat_id, e, exc_info=e)

    async def _process_llm_text_response(self, result: ChatCompletion, chat_id: int):
        if result.choices[0].message.refusal is not None:
            self._logger.warning("Refusal in %s: %s", chat_id, result.choices[0].message.refusal)

            await self._sender_service.send_refusal(chat_id, result.choices[0].message.refusal)

        elif result.choices[0].message.content is not None:
            try:
                structured_response = ModelResponse.model_validate_json(
                    result.choices[0].message.content
                )
                await self._sender_service.send(chat_id, structured_response)
            except ValidationError as err:
                self._logger.error(
                    "Cannot validate model response; response is %s",
                    result.choices[0].message.content,
                    exc_info=err,
                )
            except Exception as err:
                self._logger.error(
                    "Cannot send response to the user cause of %s",
                    err,
                    exc_info=err,
                )

    async def _process_llm_tool_call(
        self, chat_id, tool_call: ChatCompletionMessageToolCall
    ) -> tuple[str, bool]:
        try:
            self._logger.info(
                "Calling function %s in chat %s with params %s (id: %s)",
                tool_call.function.name,
                chat_id,
                tool_call.function.arguments,
                tool_call.id,
            )

            tool_result = await self._tool_command_dispatcher.execute_tool(
                tool_call.function.name, tool_call.function.arguments, chat_id
            )

            self._logger.info(
                "Result for function %s in chat %s is: %s",
                tool_call.id,
                chat_id,
                tool_result,
            )

            # if tool calling loop should be stopped, this will be eq True
            # for example, it will happen when an ignore or listen tool will be called
            # the reason is model sometimes looping in these tools call
            # (trying to ignore messages too many times for example)
            tool_stop = tool_result.stop
            tool_response = tool_result.response

        except Exception as e:
            self._logger.error("Cannot execute tool; response content will be empty", exc_info=e)

            tool_response = ""
            tool_stop = False

        return (tool_response, tool_stop)

    async def _get_llm_response(
        self,
        chat_id: int,
        instruction_messages: list[dict],
        old_messages: list[dict],
        new_messages: list[dict],
        tools: list,
    ) -> ChatCompletion:
        attempts = 0
        last_error = ValueError("Undefined error when sending request to a llm")

        while True:
            if attempts >= DefaultChatProcessor.MAX_LLM_CALL_ATTEMPTS:
                raise last_error

            try:
                return await self._openai_client.chat.completions.create(
                    model=self._openai_config.model,
                    tools=tools,
                    messages=instruction_messages + old_messages + new_messages,  # type: ignore
                    response_format=self._llm_config.response_schema,  # type: ignore
                    store=True,
                )
            except RateLimitError as err:
                last_error = err
                self._logger.error(
                    "RateLimitError error when sending request to a llm %s; trying to shorten history",
                    err,
                    exc_info=err,
                )

                # after shortening history, update old_messages both here and in the caller
                await self._message_service.shorten_history(chat_id)
                old_messages[:] = await self._message_service.fetch_messages(chat_id)
            except BadRequestError as err:
                last_error = err
                self._logger.error(
                    "BadRequestError error when sending request to a llm %s; trying to remove media",
                    err,
                    exc_info=err,
                )

                # after shortening history, update old_messages both here and in the caller
                await self._message_service.shorten_full_history_without_media(chat_id)
                old_messages[:] = await self._message_service.fetch_messages(chat_id)
            except APIError as err:
                last_error = err
                self._logger.error(
                    "APIError error when sending request to a llm %s; waiting for 2s and trying again",
                    err,
                    exc_info=err,
                )

                await asyncio.sleep(2)
            finally:
                attempts += 1
