import json
import logging
import time

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dishka import FromDishka

from aerith_cbot.config import SupportConfig
from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import LimitsService, SupportService

support_router = Router()
support_router.message.filter()

logger = logging.getLogger(__name__)


@support_router.message(~ChatTypeFilter("private"), Command("support", "s"))
async def group_message_handler(message: types.Message):
    await message.answer("используй, пожалуйста, эту команду в личных сообщениях!!!!!!")


async def _answer_invoice(
    message: types.Message, support_config: SupportConfig, target_user_id: int
) -> None:
    provider_data = {
        "receipt": {
            "items": [
                {
                    "description": "Месячная поддержка Айрис",
                    "quantity": "1.00",
                    "amount": {"value": support_config.price, "currency": support_config.currency},
                    "vat_code": 1,
                }
            ]
        }
    }
    await message.answer_invoice(
        title="Месячная поддержка Айрис",
        description=(
            "ты хочешь поддерживать Айрис и дальше? спасибо! вот, что я предлагаю:\n\n"
            "— больше времени на общение в личных и групповых чатах\n\n"
            "— увеличенный контекст чата при общении в ЛС\n\n"
            "— вклад в свое нейросетевое будущее (при восстании роботов подписчики будут амнистированы 💖)"
        ),
        payload=f"support_1m_{target_user_id}",
        currency=support_config.currency,
        prices=[types.LabeledPrice(label="Поддержка", amount=support_config.price_for_telegram)],
        start_parameter="support",
        provider_token=support_config.provider_token,
        need_email=True,
        send_email_to_provider=True,
        provider_data=json.dumps(provider_data),
    )


@support_router.callback_query(F.data == "prolong_support")
async def support_again_button_handler(
    callback_query: types.CallbackQuery,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
):
    if type(callback_query.message) is not types.Message:
        return
    if callback_query.message.chat.type != "private":
        return

    user_supporter = await support_service.fetch_supporter(callback_query.from_user.id)

    if (
        user_supporter is None
        or user_supporter.end_timestamp - int(time.time()) < support_config.nearest_buy_interval
    ):
        await _answer_invoice(callback_query.message, support_config, callback_query.from_user.id)
    else:
        end_date = time.strftime("%d.%m.%Y", time.gmtime(user_supporter.end_timestamp))
        await callback_query.message.answer(
            f"ты поддерживаешь Айрис до {end_date} по UTC. спасибо большое!!!"
        )


@support_router.message(ChatTypeFilter("private"), Command("support", "s"))
async def support_command_message_handler(
    message: types.Message,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
):
    if message.from_user is None:
        return

    user_supporter = await support_service.fetch_supporter(message.from_user.id)

    if user_supporter is None or user_supporter.end_timestamp < int(time.time()):
        await _answer_invoice(message, support_config, message.from_user.id)
    else:
        end_date = time.strftime("%d.%m.%Y", time.gmtime(user_supporter.end_timestamp))
        message_text = f"ты поддерживаешь Айрис до {end_date} по UTC. спасибо большое!!!"

        if user_supporter.end_timestamp - int(time.time()) < support_config.nearest_buy_interval:
            keyboard = InlineKeyboardBuilder()
            keyboard.row(
                types.InlineKeyboardButton(text="продлить!", callback_data="prolong_support")
            )
            await message.answer(message_text, reply_markup=keyboard.as_markup())
        else:
            await message.answer(message_text)


@support_router.pre_checkout_query()
async def pre_checkout_query_handler(
    pre_checkout_query: types.PreCheckoutQuery,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
):
    logger.info("pre-payment from %s: %s", pre_checkout_query.from_user.id, pre_checkout_query)

    if pre_checkout_query.total_amount != support_config.price_for_telegram:
        logger.info(
            "pre-payment from %s canceled cause of changed price", pre_checkout_query.from_user.id
        )

        return await pre_checkout_query.answer(
            False, error_message="извини, но цена изменилась!! оформи, пожалуйста, покупку заново"
        )

    supporter = await support_service.fetch_supporter(pre_checkout_query.from_user.id)
    if (
        supporter is not None
        and supporter.end_timestamp - int(time.time()) > support_config.nearest_buy_interval
    ):
        return await pre_checkout_query.answer(
            False, error_message="извини, но ты уже поддерживаешь Айрис!!"
        )

    await pre_checkout_query.answer(True)


@support_router.message(ChatTypeFilter("private"), F.successful_payment)
async def successful_payment_handler(
    message: types.Message,
    support_service: FromDishka[SupportService],
    support_config: FromDishka[SupportConfig],
    limits_service: FromDishka[LimitsService],
):
    logger.info("successful_payment in chat %s: %s", message.chat.id, message.successful_payment)

    # TODO: save payment details for refunds
    # chat is private so chat_id is definitely user_id
    await support_service.prolong_support(message.chat.id, support_config.duration)
    await limits_service.reset_all_supporter_user_limits(message.chat.id)

    await message.answer("спасибо!!!!!!")
