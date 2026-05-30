"""Aiogram bot setup. Owned by the runtime — no static handlers.

Можно запускать двумя способами, оба корректные:

* ``python -m app.main``  — main + preview-поллер вместе (рекомендуется).
* ``python backend/app/bot/main.py``  — только бот, без поллера превью
  (так стартует Wispbyte по умолчанию).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.runtime.engine import make_router
from app.bot.runtime.middleware import install as install_msgid_middleware
from app.bot.runtime.mini_constructor import make_router as make_mini_router
from app.bot.runtime.multibot import build_child_bots
from app.core.config import settings

log = logging.getLogger(__name__)


def build_bot() -> Bot:
    b = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    install_msgid_middleware(b)
    return b


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # Сначала владельческие /builder-команды — потом основной runtime
    dp.include_router(make_mini_router())
    dp.include_router(make_router())
    return dp


async def run() -> None:
    bot = build_bot()
    dp = build_dispatcher()
    child_bots = build_child_bots()
    all_bots = [bot, *child_bots]
    log.info(
        "Bot polling started: 1 main + %d child bots",
        len(child_bots),
    )
    try:
        await dp.start_polling(*all_bots, allowed_updates=dp.resolve_used_update_types())
    finally:
        for b in all_bots:
            with contextlib.suppress(Exception):
                await b.session.close()


# Allow other modules (the FastAPI preview endpoint) to share one Bot instance.
_shared_bot: Bot | None = None


def shared_bot() -> Bot:
    global _shared_bot
    if _shared_bot is None:
        _shared_bot = build_bot()
    return _shared_bot


def _bootstrap_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


def _main() -> None:
    """Entrypoint when started as ``python backend/app/bot/main.py``."""
    _bootstrap_logging()
    if not settings.bot_token:
        log.error("BOT_TOKEN is not set. Exiting.")
        sys.exit(1)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        log.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set. Exiting.")
        sys.exit(1)
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped")


if __name__ == "__main__":
    _main()
