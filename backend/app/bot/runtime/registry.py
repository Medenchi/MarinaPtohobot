"""Cached access to the published bot flow.

The flow lives in Supabase ``bot_flows`` and is fetched lazily. The constructor
calls :func:`invalidate` after publishing so the bot picks up the new graph on
the next update without restarting.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

_cache: dict[str, Any] | None = None


def invalidate() -> None:
    global _cache
    _cache = None
    log.info("Flow cache invalidated")


def published_flow() -> dict[str, Any] | None:
    """Return the latest published flow as ``{id, name, graph}`` or ``None``."""
    global _cache
    if _cache is not None:
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
        return None
    _cache = rows[0]
    return _cache


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
    """Find the first trigger node matching the user input.

    * ``command``: /start, /help, ...  (without the leading slash)
    * ``text``:    raw text the user sent
    """
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
