"""Per-user session storage backed by Supabase.

One row per Telegram user in ``bot_sessions``. The engine loads it at the start
of every update and persists it at the end.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any

from aiogram.types import User as TgUser

from app.core.supabase import get_supabase


@dataclass(slots=True)
class Session:
    telegram_id: int
    flow_id: str | None = None
    current_node_id: str | None = None
    vars: dict[str, Any] = field(default_factory=dict)
    awaiting_input: bool = False

    def to_row(self) -> dict[str, Any]:
        return {
            "telegram_id": self.telegram_id,
            "flow_id": self.flow_id,
            "current_node_id": self.current_node_id,
            "vars": self.vars,
            "awaiting_input": self.awaiting_input,
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
    )


def save(session: Session) -> None:
    sb = get_supabase()
    sb.table("bot_sessions").upsert(session.to_row(), on_conflict="telegram_id").execute()


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
