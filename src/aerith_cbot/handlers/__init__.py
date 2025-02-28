from aiogram import Router

from aerith_cbot.filters import SenderFilter

from .group import group_router
from .private import private_router
from .utils import utils_router

handlers_router = Router()
handlers_router.message.filter(SenderFilter("user"))

handlers_router.include_routers(utils_router, private_router, group_router)  # order is important!

__all__ = ("handlers_router",)
