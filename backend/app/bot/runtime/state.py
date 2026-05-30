"""Per-user session storage backed by Supabase.

One row per Telegram user in ``bot_sessions``. The engine loads it at the start
of every update and persists it at the end.

Robustness: если flow_id, хранящийся в сессии, уже удалён из ``bot_flows``,
Postgres возвращает ``23503`` (FK violation). Мы перехватываем эту ошибку,
сбрасываем ``flow_id`` в ``NULL`` и инвалидируем кеш реестра, чтобы бот сам
перетянул актуальный published-флоу при следующем апдейте.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass, field
from typing import Any

from aiogram.types import User as TgUser

from app.core.supabase import get_supabase

log = logging.getLogger(__name__)


@dataclass(slots=True)
class Session:
    telegram_id: int
    flow_id: str | None = None
    current_node_id: str | None = None
    vars: dict[str, Any] = field(default_factory=dict)
    awaiting_input: bool = False
    bot_message_ids: list[int] = field(default_factory=list)

    def to_row(self) -> dict[str, Any]:
        return {
            "telegram_id": self.telegram_id,
            "flow_id": self.flow_id,
            "current_node_id": self.current_node_id,
            "vars": self.vars,
            "awaiting_input": self.awaiting_input,
            "bot_message_ids": self.bot_message_ids,
        }


def load(telegram_id: int) -> Session:
    sb = get_supabase()
    resp = sb.table("bot_sessions").select("*").eq("telegram_id", telegram_id).limit(1).execute()
    rows = resp.data or []
    if not rows:
        return Session(telegram_id=telegram_id)
    r = rows[0]
    return Session(
        telegram_id=r["telegram_id"],
        flow_id=r.get("flow_id"),
        current_node_id=r.get("current_node_id"),
        vars=r.get("vars") or {},
        awaiting_input=bool(r.get("awaiting_input")),
        bot_message_ids=r.get("bot_message_ids") or [],
    )


def _is_fk_violation(exc: Exception, constraint_hint: str = "bot_sessions_flow_id_fkey") -> bool:
    # postgrest.exceptions.APIError exposes .code / .message; supabase-py wraps it.
    code = getattr(exc, "code", None) or ""
    msg = (getattr(exc, "message", "") or "") + " " + str(exc)
    return code == "23503" or "23503" in msg or constraint_hint in msg


def _is_missing_column(exc: Exception) -> bool:
    """PGRST204 — postgrest не нашёл колонки в schema cache."""
    code = getattr(exc, "code", None) or ""
    msg = (getattr(exc, "message", "") or "") + " " + str(exc)
    return code == "PGRST204" or "PGRST204" in msg or "Could not find the" in msg


def save(session: Session) -> None:
    """Upsert the session, healing stale ``flow_id`` references on the fly.

    Если миграция 0011 не применена и колонки `bot_message_ids` нет —
    стираем её из payload и пробуем заново.
    """
    sb = get_supabase()
    row = session.to_row()

    def _do_upsert(r: dict) -> None:
        sb.table("bot_sessions").upsert(r, on_conflict="telegram_id").execute()

    try:
        _do_upsert(row)
        return
    except Exception as exc:
        if _is_missing_column(exc):
            log.warning(
                "bot_sessions: missing column — retrying without bot_message_ids. "
                "Apply migration 0011_bot_sessions_message_ids.sql in Supabase."
            )
            row.pop("bot_message_ids", None)
            try:
                _do_upsert(row)
                return
            except Exception as exc2:
                if _is_fk_violation(exc2):
                    exc = exc2
                else:
                    raise
        if not _is_fk_violation(exc):
            raise
        # Stale published-flow id (was deleted from bot_flows). Reset & retry.
        log.warning(
            "bot_sessions FK violation for tg=%s flow=%s — clearing flow_id and retrying",
            session.telegram_id,
            session.flow_id,
        )
        # Tell the registry cache it's lying.
        try:
            from app.bot.runtime import registry  # local import to avoid cycle

            registry.invalidate()
        except Exception:
            log.exception("Failed to invalidate registry cache")
        session.flow_id = None
        session.current_node_id = None
        session.awaiting_input = False
        # Retry once. If it still fails — let it bubble; better to see it.
        sb.table("bot_sessions").upsert(
            session.to_row(),
            on_conflict="telegram_id",
        ).execute()


def clear(telegram_id: int) -> None:
    sb = get_supabase()
    sb.table("bot_sessions").delete().eq("telegram_id", telegram_id).execute()


def upsert_bot_user(user: TgUser) -> None:
    sb = get_supabase()
    full_name = user.full_name or (user.first_name or "")
    sb.table("bot_users").upsert(
        {
            "telegram_id": user.id,
            "username": user.username,
            "full_name": full_name,
            "is_premium": bool(getattr(user, "is_premium", False)),
            "language_code": user.language_code,
        },
        on_conflict="telegram_id",
    ).execute()


def user_to_vars(user: TgUser) -> dict[str, Any]:
    """Subset of TG user exposed to flow templates as ``{{user.*}}``."""
    return {
        "id": user.id,
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "full_name": user.full_name or "",
        "language_code": user.language_code or "",
        "is_premium": bool(getattr(user, "is_premium", False)),
    }


def log_event(
    *,
    telegram_id: int | None,
    telegram_username: str | None,
    flow_id: str | None,
    node_id: str | None,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> None:
    sb = get_supabase()
    # Analytics must never break the bot.
    with contextlib.suppress(Exception):
        sb.table("bot_events").insert(
            {
                "telegram_id": telegram_id,
                "telegram_username": telegram_username,
                "flow_id": flow_id,
                "node_id": node_id,
                "event_type": event_type,
                "payload": payload or {},
            },
        ).execute()
