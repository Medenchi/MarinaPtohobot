"""Поддержка мультибота: один процесс поллит много токенов параллельно.

Логика:
* На старте читаем child_bots из Supabase (is_enabled=true)
* Создаём Bot для каждого + подключаем тот же Dispatcher
* dp.start_polling(*bots) — aiogram 3.x умеет это нативно
* Контекст текущего бота автоматически прокидывается в bot: Bot хендлера

Создание новых дочерних ботов — через мини-конструктор /builder в Telegram
или через REST API (фронт админки). Они появятся при следующем рестарте
или при горячей подгрузке (см. reload_child_bots()).
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.runtime.middleware import install as install_msgid_middleware
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)


def list_active_child_bots() -> list[dict[str, Any]]:
    sb = get_supabase()
    try:
        r = (
            sb.table("child_bots")
            .select("id, token, bot_username, display_name, is_enabled")
            .eq("is_enabled", True)
            .execute()
        )
        return r.data or []
    except Exception as exc:
        log.warning("child_bots load failed (table missing?): %s", exc)
        return []


def build_child_bots() -> list[Bot]:
    rows = list_active_child_bots()
    bots: list[Bot] = []
    for row in rows:
        token = row.get("token")
        if not token:
            continue
        try:
            b = Bot(
                token=token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
            install_msgid_middleware(b)
            bots.append(b)
        except Exception as exc:
            log.warning(
                "child bot %s init failed: %s",
                row.get("bot_username") or row.get("id"),
                exc,
            )
    log.info("Loaded %d child bots", len(bots))
    return bots


def register_child_bot(
    token: str,
    *,
    owner_telegram_id: int | None = None,
    display_name: str | None = None,
    flow_id: str | None = None,
) -> dict[str, Any]:
    """Зарегистрировать новый дочерний бот в БД. Возвращает строку."""
    sb = get_supabase()
    row = {
        "token": token,
        "owner_telegram_id": owner_telegram_id,
        "display_name": display_name,
        "flow_id": flow_id,
        "is_enabled": True,
    }
    try:
        resp = sb.table("child_bots").insert(row).execute()
        return (resp.data or [{}])[0]
    except Exception as exc:
        log.warning("register_child_bot failed: %s", exc)
        return {}


async def fetch_and_set_username(bot: Bot, child_id: int) -> None:
    """Поднимает username из getMe и пишет в БД."""
    try:
        me = await bot.get_me()
        sb = get_supabase()
        sb.table("child_bots").update({"bot_username": me.username}).eq("id", child_id).execute()
    except Exception as exc:
        log.warning("fetch_and_set_username failed for %s: %s", child_id, exc)
