import logging
import time

from aiogram import F, Router, types
from aiogram.filters import Command
from dishka import FromDishka

from aerith_cbot.config import SupportConfig
from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import SupportService

support_router = Router()
support_router.message.filter()

logger = logging.getLogger(__name__)


@support_router.message(~ChatTypeFilter("private"), Command("support", "s"))
async def group_message_handler(message: types.Message):
    await message.answer("используй, пожалуйста, эту команду в личных сообщениях!!!!!!")


@support_router.message(ChatTypeFilter("private"), Command("support", "s"))
async def private_message_handler(
    message: types.Message,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
):
    if message.from_user is None:
        return

    user_supporter = await support_service.fetch_supporter(message.from_user.id)

    if user_supporter is None or user_supporter.end_timestamp < int(time.time()):
        await message.answer_invoice(
            title="Месячная поддержка Айрис",
            description=(
                "привет!!! ты хочешь поддержать Айрис? спасибо! вот, что я предлагаю:\n\n"
                "— больше времени на общение в личных и групповых чатах\n\n"
                "— возможность загружать картинки"
            ),
            payload="support_1m",
            currency="RUB",
            prices=[types.LabeledPrice(label="Поддержка", amount=support_config.price * 100)],
            start_parameter="support",
            provider_token="1744374395:TEST:d725ee2fa45592ee8b1a"
        )
    else:
        end_date = time.strftime("%d.%m.%Y", time.gmtime(user_supporter.end_timestamp))
        await message.answer(f"приветы! ты поддерживаешь Айрис до {end_date} по UTC. спасибо!!!")


@support_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: types.PreCheckoutQuery):
    logger.info("pre-payment from %s: %s", pre_checkout_query.from_user.id, pre_checkout_query)
    await pre_checkout_query.answer(True)


@support_router.message(ChatTypeFilter("private"), F.successful_payment)
async def successful_payment_handler(
    message: types.Message,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
):
    await support_service.prolong_support(1, 1)
    await message.answer("спасибо!!!!!!")
