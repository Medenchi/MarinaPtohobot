"""Cached access to the published bot flow.

The flow lives in Supabase ``bot_flows`` and is fetched lazily. The constructor
calls :func:`invalidate` after publishing so the bot picks up the new graph on
the next update without restarting.

The cache is also TTL-protected (``_CACHE_TTL_SEC``) — иначе ситуация, когда
flow удалили прямо в БД, может «зависнуть» в боте до рестарта.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 30  # автопросрочка кеша, чтобы поймать удаление/переключение
_cache: dict[str, Any] | None = None
_cache_at: float = 0.0


def invalidate() -> None:
    global _cache, _cache_at
    _cache = None
    _cache_at = 0.0
    log.info("Flow cache invalidated")


def published_flow() -> dict[str, Any] | None:
    """Return the latest published flow as ``{id, name, graph}`` or ``None``."""
    global _cache, _cache_at
    now = time.monotonic()
    if _cache is not None and (now - _cache_at) < _CACHE_TTL_SEC:
        return _cache
    sb = get_supabase()
    resp = (
        sb.table("bot_flows")
        .select("id, name, graph, version")
        .eq("is_published", True)
        .order("published_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        _cache = None
        _cache_at = now
        return None
    _cache = rows[0]
    _cache_at = now
    return _cache


def flow_exists(flow_id: str) -> bool:
    """Cheap existence check used to validate stale session.flow_id."""
    if not flow_id:
        return False
    sb = get_supabase()
    try:
        resp = sb.table("bot_flows").select("id").eq("id", flow_id).limit(1).execute()
        return bool(resp.data)
    except Exception:
        log.exception("flow_exists check failed for %s", flow_id)
        return False


def flow_by_id(flow_id: str) -> dict[str, Any] | None:
    """Fetch any flow (draft or published) by id. Bypasses cache."""
    sb = get_supabase()
    resp = (
        sb.table("bot_flows")
        .select("id, name, graph, version")
        .eq("id", flow_id)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def index_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return id->node map for fast lookup."""
    nodes = graph.get("nodes") or []
    return {n["id"]: n for n in nodes if isinstance(n, dict) and "id" in n}


def find_trigger(
    graph: dict[str, Any],
    *,
    command: str | None = None,
    text: str | None = None,
) -> dict[str, Any] | None:
    """Find the first trigger node matching the user input."""
    for n in graph.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        ntype = n.get("type")
        p = n.get("params") or {}
        if (
            command is not None
            and ntype == "command"
            and (p.get("command") or "").lstrip("/") == command.lstrip("/")
        ):
            return n
        if text is not None and ntype == "text_match":
            mode = p.get("mode") or "exact"
            patt = p.get("pattern") or ""
            if mode == "exact" and text.strip() == patt:
                return n
            if mode == "contains" and patt and patt in text:
                return n
            if mode == "starts_with" and patt and text.startswith(patt):
                return n
    return None
