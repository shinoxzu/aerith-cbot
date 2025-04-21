import asyncio
import logging

from openai import APIError, AsyncOpenAI, BadRequestError, RateLimitError
from openai.types.chat import ChatCompletion

from aerith_cbot.config import LimitsConfig, LLMConfig, OpenAIConfig
from aerith_cbot.services.abstractions import (
    LimitsService,
    MessageService,
    SupportService,
    UserContextProvider,
)
from aerith_cbot.services.abstractions.models import (
    ChatType,
)
from aerith_cbot.services.abstractions.processors import ChatProcessor, ModelResponseProcessor
from aerith_cbot.services.implementations.processors.tools import ToolCommandDispatcher


class DefaultChatProcessor(ChatProcessor):
    MAX_LLM_CALL_ATTEMPTS = 3
    MAX_LLM_CALL_ITERATIONS = 10
    MAX_TOOL_CALL_ITERATIONS = 5

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        llm_config: LLMConfig,
        openai_config: OpenAIConfig,
        tool_command_dispatcher: ToolCommandDispatcher,
        message_service: MessageService,
        limits_config: LimitsConfig,
        context_provider: UserContextProvider,
        limits_service: LimitsService,
        model_response_processor: ModelResponseProcessor,
        support_service: SupportService,
    ) -> None:
        super().__init__()

        self._openai_client = openai_client
        self._llm_config = llm_config
        self._openai_config = openai_config
        self._tool_command_dispatcher = tool_command_dispatcher
        self._message_service = message_service
        self._limits_config = limits_config
        self._limits_service = limits_service
        self._context_provider = context_provider
        self._model_response_processor = model_response_processor
        self._support_service = support_service
        self._logger = logging.getLogger(__name__)

    async def process(self, chat_id: int, chat_type: ChatType) -> None:
        old_messages: list[dict] = await self._message_service.fetch_messages(chat_id)
        new_messages: list[dict] = []

        if chat_type == ChatType.group:
            tools = self._llm_config.tools + self._llm_config.group_tools
            instruction_messages = [
                {"role": "developer", "content": self._llm_config.group_instruction}
            ]
            model_to_use = self._openai_config.group_model
            max_context_tokens = self._limits_config.group_max_context_tokens
        elif chat_type == ChatType.private:
            tools = self._llm_config.tools
            instruction_messages = [
                {"role": "developer", "content": self._llm_config.private_instruction}
            ]

            if await self._support_service.is_active_supporter(chat_id):
                model_to_use = self._openai_config.private_support_model
                max_context_tokens = self._limits_config.private_support_max_context_tokens
            else:
                model_to_use = self._openai_config.private_model
                max_context_tokens = self._limits_config.private_max_context_tokens

        self._logger.info("Used model for chat %s: %s", chat_id, model_to_use)
        self._logger.info("max_context_tokens for chat %s: %s", chat_id, max_context_tokens)

        tokens_to_subtract = 0

        current_iterations = 0
        current_tool_calls = 0

        while (
            current_iterations < DefaultChatProcessor.MAX_LLM_CALL_ITERATIONS
            and current_tool_calls < DefaultChatProcessor.MAX_TOOL_CALL_ITERATIONS
        ):
            result = await self._get_llm_response(
                chat_id,
                model_to_use,
                instruction_messages,
                old_messages,
                new_messages,
                tools,
            )

            self._logger.debug("LLM response in %s: %s", chat_id, result)

            tokens_to_subtract += await self._process_token_usage(
                chat_id, max_context_tokens, result
            )

            if not result.choices:
                break

            # TODO: append only used fields
            new_messages.append(result.choices[0].message.model_dump())

            try:
                # if the model has refused to answer, we have processed the response
                if result.choices[0].message.refusal is not None:
                    await self._model_response_processor.process_refusal(
                        chat_id, result.choices[0].message.refusal
                    )
                    break

                # here we assume that the model will generate exactly one text response
                # so we will continue to call tools even if text response was generated
                if result.choices[0].message.content is not None:
                    await self._model_response_processor.process(
                        chat_id, result.choices[0].message.content
                    )
            except Exception as err:
                self._logger.error("Error processing model response", exc_info=err)

            # if the model does not have tool_calls, we have processed the response also
            if not result.choices[0].message.tool_calls:
                break

            self._logger.debug(
                "Tool calls in %s (total: %s): %s",
                chat_id,
                len(result.choices[0].message.tool_calls),
                result.choices[0].message.tool_calls,
            )

            # call all functions in one response
            for tool_call in result.choices[0].message.tool_calls:
                tool_response = await self._tool_command_dispatcher.execute_tool(
                    tool_call.function.name, tool_call.function.arguments, chat_id
                )

                new_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_response.response,
                    },
                )

                current_tool_calls += 1

                if current_tool_calls >= DefaultChatProcessor.MAX_TOOL_CALL_ITERATIONS:
                    self._logger.warning(
                        "Tool call limit in %s (last_call: %s)", chat_id, tool_call
                    )

                    new_messages.append(
                        {
                            "role": "system",
                            "content": self._llm_config.additional_instructions.you_call_too_many_tools,
                        }
                    )

                    break

            current_iterations += 1

        self._logger.info(
            "Chat %s (%s) has used %s tokens in this messages",
            chat_id,
            chat_type,
            tokens_to_subtract,
        )

        if chat_type == ChatType.group:
            await self._limits_service.subtract_group_tokens(chat_id, tokens_to_subtract)
        elif chat_type == ChatType.private:
            await self._limits_service.subtract_private_tokens(chat_id, tokens_to_subtract)

        await self._message_service.add_messages(chat_id, new_messages)

    async def _get_llm_response(
        self,
        chat_id: int,
        model_to_use: str,
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
                    model=model_to_use,
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

    async def _process_token_usage(
        self, chat_id: int, max_context_tokens: int, result: ChatCompletion
    ) -> int:
        # idk when this is possible
        if result.usage is None:
            self._logger.warn("Usage is none in chat %s")
            return 0

        self._logger.info("Usage in chat %s : %s", chat_id, result.usage)

        if result.usage.total_tokens > max_context_tokens:
            self._logger.info(
                "Usage in chat %s above limit (%s>%s); shortening history",
                chat_id,
                result.usage.total_tokens,
                max_context_tokens,
            )
            await self._message_service.shorten_history(chat_id)

        # we will always get details in response, but in case of
        # some errors we will count tokens in the other way
        if (
            result.usage.prompt_tokens_details is not None
            and result.usage.prompt_tokens_details.cached_tokens is not None
        ):
            new_prompt_tokens = (
                result.usage.prompt_tokens - result.usage.prompt_tokens_details.cached_tokens
            )
            tokens_to_subtract = (
                result.usage.prompt_tokens_details.cached_tokens // 4
                + new_prompt_tokens // 2
                + result.usage.completion_tokens * 2
            )
        else:
            tokens_to_subtract = (
                result.usage.completion_tokens * 2 + result.usage.prompt_tokens // 3
            )

        return tokens_to_subtract
