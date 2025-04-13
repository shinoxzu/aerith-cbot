import logging

from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState
from aerith_cbot.services.abstractions import SenderService
from aerith_cbot.services.abstractions.models import ModelResponse
from aerith_cbot.services.abstractions.processors import ModelResponseProcessor


class DefaultModelResponseProcessor(ModelResponseProcessor):
    IGNORING_STREAK_LIMIT = 10

    def __init__(self, sender_service: SenderService, db_session: AsyncSession) -> None:
        super().__init__()

        self._sender_service = sender_service
        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def process(self, chat_id: int, response_raw: str) -> None:
        try:
            response = ModelResponse.model_validate_json(response_raw)
        except ValidationError as err:
            self._logger.error(
                "Cannot validate model response; response is %s",
                response_raw,
                exc_info=err,
            )
            return

        if response.text or response.sticker:
            try:
                await self._sender_service.send_model_response(chat_id, response)
            except Exception as err:
                self._logger.error(
                    "Failed to send model response in chat %s",
                    chat_id,
                    exc_info=err,
                )
                return

            await self._db_session.execute(
                update(ChatState).where(ChatState.chat_id == chat_id).values(ignoring_streak=0)
            )
            await self._db_session.commit()
        else:
            chat_state = await self._db_session.get_one(ChatState, chat_id)

            if chat_state.ignoring_streak >= DefaultModelResponseProcessor.IGNORING_STREAK_LIMIT:
                self._logger.info("Ignoring streak in chat %s reached limit; unfocusing", chat_id)

                chat_state.ignoring_streak = 0
                chat_state.is_focused = False
            else:
                chat_state.ignoring_streak += 1

                self._logger.info(
                    "Ignoring streak in chat %s is %s now",
                    chat_id,
                    chat_state.ignoring_streak,
                )

            await self._db_session.commit()

    async def process_refusal(self, chat_id: int, refusal: str) -> None:
        self._logger.info("Processing refusal in chat %s: %s", chat_id, refusal)

        try:
            await self._sender_service.send_model_refusal(chat_id, refusal)
        except Exception as err:
            self._logger.error(
                "Failed to send model refusal in chat %s",
                chat_id,
                exc_info=err,
            )
            return

        await self._db_session.execute(
            update(ChatState).where(ChatState.chat_id == chat_id).values(ignoring_streak=0)
        )
        await self._db_session.commit()
