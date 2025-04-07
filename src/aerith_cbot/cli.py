import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.methods import DeleteWebhook
from dishka.integrations.aiogram import setup_dishka

from .config import load_config
from .container import init_dishka_container
from .handlers import handlers_router


async def main():
    config = load_config(os.environ["CONFIG_PATH"], os.environ["LLM_CONFIG_PATH"])

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        force=True,
        encoding="utf-8",
    )

    bot = Bot(token=config.bot.token)
    dp = Dispatcher()

    container = await init_dishka_container(config, bot)
    setup_dishka(container=container, router=dp, auto_inject=True)

    dp.include_router(handlers_router)

    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


def cli():
    """Wrapper for command line"""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")


if __name__ == "__main__":
    cli()
