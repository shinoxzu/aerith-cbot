from aiogram import Bot, types


async def setup_commands(bot: Bot) -> None:
    commands = [
        types.BotCommand(command="support", description="Поддержать Айрис"),
        types.BotCommand(command="clear", description="Очищает историю чата для Айрис"),
    ]
    await bot.set_my_commands(commands, scope=types.BotCommandScopeAllPrivateChats())
