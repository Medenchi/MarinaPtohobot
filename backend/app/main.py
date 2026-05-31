"""Entry point — runs the aiogram bot and a background preview poller.

The frontend (admin constructor + mama content panels) talks to Supabase
directly via supabase-js and an Edge Function for login, so we no longer
host an HTTP server here. This process now does just two things:

1. Polls Telegram and runs the published flow (``app.bot.runtime`` engine).
2. Polls ``bot_preview_requests`` so when Denis hits "Preview" in the
   constructor, the draft graph is rendered for him in Telegram.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Dispatcher

from app.bot.main import shared_bot
from app.bot.runtime.engine import make_router
from app.bot.runtime.preview import poll_preview_requests
from app.bot.runtime.pinterest import poll_pinterest_imports
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def _run_bot() -> None:
    bot = shared_bot()
    dp = Dispatcher()
    dp.include_router(make_router())
    log.info("Bot polling started (constructor runtime)")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


async def _run_preview_poller() -> None:
    bot = shared_bot()
    log.info("Preview poller started (bot_preview_requests)")
    await poll_preview_requests(bot)

async def _run_pinterest_poller() -> None:
    log.info("Pinterest poller started (pinterest_imports)")
    await poll_pinterest_imports()

async def main() -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN is not set. Exiting.")
        sys.exit(1)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        log.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set. Exiting.")
        sys.exit(1)

    await asyncio.gather(_run_bot(), _run_preview_poller(), _run_pinterest_poller())


if __name__ == "__main__":
    asyncio.run(main())
