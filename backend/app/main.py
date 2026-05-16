"""Entry point — runs the aiogram bot AND the admin FastAPI concurrently."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.api.main import app as fastapi_app
from app.bot.handlers import courses, quiz, start
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def _run_bot() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(courses.router)
    log.info("Bot polling started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def _run_api() -> None:
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    config = uvicorn.Config(fastapi_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    log.info("API listening on %s:%s", host, port)
    await server.serve()


async def main() -> None:
    if not settings.bot_token:
        log.error("BOT_TOKEN is not set. Exiting.")
        sys.exit(1)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        log.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set. Exiting.")
        sys.exit(1)
    if not settings.admin_password:
        log.warning(
            "ADMIN_PASSWORD is empty — admin login will reject all requests.",
        )

    await asyncio.gather(_run_bot(), _run_api())


if __name__ == "__main__":
    asyncio.run(main())
