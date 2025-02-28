import logging

from aiogram import Bot, types
from openai import AsyncOpenAI, BadRequestError
from openai.types.chat import ChatCompletion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.database.models import ChatState, Message
from aerith_cbot.services.abstractions import PrivateMessageProcessor, SenderService
from aerith_cbot.services.abstractions.models import ModelResponse
from aerith_cbot.services.abstractions.tools import tg_msg_to_model_input

from .tools import ToolCommandDispatcher


class OpenAIPrivateMessageProcessor(PrivateMessageProcessor):
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        db_session: AsyncSession,
        bot: Bot,
        llm_config: LLMConfig,
        tool_command_dispatcher: ToolCommandDispatcher,
        sender_service: SenderService,
    ) -> None:
        super().__init__()

        self._logger = logging.getLogger(__name__)
        self._openai_client = openai_client
        self._db_session = db_session
        self._bot = bot
        self._llm_config = llm_config
        self._tool_command_dispatcher = tool_command_dispatcher
        self._sender_service = sender_service

    async def process(self, message: types.Message) -> None:
        chat_state = await self._db_session.get(ChatState, message.chat.id)

        if chat_state is None:
            self._logger.info("Adding new chat_state: %s", message.chat.id)

            chat_state = ChatState(chat_id=message.chat.id, is_focused=True)
            self._db_session.add(chat_state)
            await self._db_session.commit()

        stmt = select(Message).where(Message.chat_id == message.chat.id)
        old_messages_raw = await self._db_session.execute(stmt)

        old_messages: list[dict] = [om.data for om in old_messages_raw.scalars()]
        new_messages: list[dict] = []

        if not old_messages:
            new_messages.append(
                {"role": "developer", "content": self._llm_config.group_instruction},
            )

        try:
            new_messages.append(
                {
                    "role": "user",
                    "content": tg_msg_to_model_input(message).model_dump_json(),
                },
            )

            result = await self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                tools=self._llm_config.group_tools,
                messages=old_messages + new_messages,  # type: ignore
                response_format=self._llm_config.response_schema,  # type: ignore
            )
            await self._process_llm_text_response(result, new_messages, message)

            # until there are tool calls, we call them, pass response to a llm,
            # and we try to send llm text response to the user
            # there is no operation limit because I dont think there will be situations where
            # OpenAI will call so many tools in a loop
            while result.choices[0].message.tool_calls:
                for tool_call in result.choices[0].message.tool_calls:
                    try:
                        tool_result = await self._tool_command_dispatcher.execute_tool(
                            tool_call.function.name, tool_call.function.arguments, message
                        )
                    except Exception as e:
                        self._logger.error(
                            "Cannot execute tool; response content will be empty", exc_info=e
                        )

                        tool_result = ""

                    new_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        },
                    )

                result = await self._openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    tools=self._llm_config.group_tools,
                    messages=old_messages + new_messages,  # type: ignore
                    response_format=self._llm_config.response_schema,  # type: ignore
                )
                await self._process_llm_text_response(result, new_messages, message)

            self._db_session.add_all(
                [Message(chat_id=message.chat.id, data=md) for md in new_messages]
            )
        except BadRequestError as e:
            self._logger.error("Cannot process openai request cause of %s", e, exc_info=e)
        finally:
            await self._db_session.commit()

    async def _process_llm_text_response(
        self, result: ChatCompletion, new_messages: list[dict], message: types.Message
    ):
        new_messages.append(result.choices[0].message.model_dump())

        if result.choices[0].message.content is not None:
            # TODO: add error handling here, because model can produce an incorrect response
            # or a refusal
            structured_response = ModelResponse.model_validate_json(
                result.choices[0].message.content
            )
            await self._sender_service.send(message, structured_response)
