"""Analytics summary (both admin and mama can view)."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends

from app.api.auth import require_any
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin/stats", dependencies=[Depends(require_any)])


@router.get("/overview")
def overview(days: int = 30) -> dict[str, Any]:
    sb = get_supabase()
    since = datetime.now(tz=UTC) - timedelta(days=days)
    since_iso = since.isoformat()

    users_resp = sb.table("bot_users").select("telegram_id", count="exact").execute()
    new_users_resp = (
        sb.table("bot_users")
        .select("telegram_id", count="exact")
        .gte("first_seen_at", since_iso)
        .execute()
    )
    events_resp = (
        sb.table("bot_events")
        .select("event_type, created_at")
        .gte("created_at", since_iso)
        .limit(5000)
        .execute()
    )
    bookings_resp = (
        sb.table("bookings")
        .select("id, is_read, created_at", count="exact")
        .gte("created_at", since_iso)
        .execute()
    )

    events = events_resp.data or []
    by_type = Counter(e.get("event_type") for e in events)
    by_day: dict[str, int] = {}
    for e in events:
        if (e.get("event_type") or "") != "message":
            continue
        ts = e.get("created_at") or ""
        day = ts[:10]
        if day:
            by_day[day] = by_day.get(day, 0) + 1

    return {
        "since": since_iso,
        "users_total": users_resp.count or 0,
        "users_new": new_users_resp.count or 0,
        "bookings_total": bookings_resp.count or 0,
        "bookings_unread": sum(1 for b in (bookings_resp.data or []) if not b.get("is_read")),
        "events_by_type": dict(by_type),
        "messages_per_day": sorted(by_day.items()),
        "pdf_generated": by_type.get("pdf_generated", 0),
    }


@router.get("/events")
def recent_events(limit: int = 100) -> list[dict[str, Any]]:
    sb = get_supabase()
    resp = (
        sb.table("bot_events")
        .select("*")
        .order("created_at", desc=True)
        .limit(min(limit, 500))
        .execute()
    )
    return resp.data or []
