"""Aiogram bot setup. Owned by the runtime — no static handlers."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.runtime.engine import make_router
from app.core.config import settings

log = logging.getLogger(__name__)


def build_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(make_router())
    return dp


async def run() -> None:
    bot = build_bot()
    dp = build_dispatcher()
    log.info("Bot polling started (constructor runtime)")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


# Allow other modules (the FastAPI preview endpoint) to share one Bot instance.
_shared_bot: Bot | None = None


def shared_bot() -> Bot:
    global _shared_bot
    if _shared_bot is None:
        _shared_bot = build_bot()
    return _shared_bot
