from aiogram import F, Router, types
from dishka import FromDishka

from aerith_cbot.filters import ChatTypeFilter
from aerith_cbot.services.abstractions import ChatMigrationService

migrate_router = Router()
migrate_router.message.filter(ChatTypeFilter("group"))


@migrate_router.message(F.migrate_to_chat_id)
async def chat_message_handler(
    message: types.Message, chat_migration_service: FromDishka[ChatMigrationService]
):
    if message.migrate_to_chat_id:
        await chat_migration_service.update(message.chat.id, message.migrate_to_chat_id)
