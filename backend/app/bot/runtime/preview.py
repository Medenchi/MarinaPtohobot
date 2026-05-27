"""Preview poller — renders draft flows for the constructor.

The admin constructor (``/admin``) writes a row to ``bot_preview_requests``
when Denis hits "Preview". This module continuously polls that table and,
for each pending row, executes the embedded graph against the target
Telegram user (Denis) using the same runtime as a published flow.

Communication is one-way: the frontend never talks to this process; it just
writes a row in Supabase and the bot picks it up.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from aiogram import Bot

from app.bot.runtime import registry, state
from app.bot.runtime.engine import ExecutionContext, _execute_from
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2.0


def _find_start_node(graph: dict[str, Any]) -> str | None:
    """Return the first node id reachable from a /start command trigger."""
    for n in graph.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        if n.get("type") != "command":
            continue
        params = n.get("params") or {}
        cmd = str(params.get("command") or "").lstrip("/")
        if cmd == "start":
            return n.get("next") or n["id"]
    return None


async def _render_preview(
    bot: Bot,
    *,
    graph: dict[str, Any],
    target_telegram_id: int,
    flow_id: str | None,
) -> tuple[bool, str]:
    """Execute the graph for ``target_telegram_id``. Returns (ok, message)."""
    start_id = _find_start_node(graph)
    if not start_id:
        return False, "Flow has no /start trigger"

    nodes = registry.index_nodes(graph)
    tg_user = {
        "id": target_telegram_id,
        "username": "preview",
        "first_name": "Preview",
        "last_name": "",
        "full_name": "Preview",
        "language_code": "ru",
        "is_premium": False,
    }
    session = state.Session(
        telegram_id=target_telegram_id,
        flow_id=flow_id,
        current_node_id=None,
        vars={},
        awaiting_input=False,
    )
    ctx = ExecutionContext(
        chat_id=target_telegram_id,
        session=session,
        tg_user=tg_user,
        flow_id=flow_id,
        graph=graph,
        nodes=nodes,
    )
    try:
        await bot.send_message(
            chat_id=target_telegram_id,
            text="🧪 Превью флоу",
        )
    except Exception as exc:
        return False, f"Не получилось отправить сообщение: {exc}. Сначала /start в боте."

    await _execute_from(bot, ctx, start_id)
    state.save(session)
    return True, "Preview sent"


async def _process_one(bot: Bot, row: dict[str, Any]) -> None:
    rid = row["id"]
    sb = get_supabase()
    try:
        ok, message = await _render_preview(
            bot,
            graph=row.get("graph") or {},
            target_telegram_id=int(row["target_telegram_id"]),
            flow_id=row.get("flow_id"),
        )
        sb.table("bot_preview_requests").update(
            {
                "status": "sent" if ok else "error",
                "error": None if ok else message,
                "processed_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", rid).execute()
        if not ok:
            log.warning("Preview %s failed: %s", rid, message)
    except Exception as exc:
        log.exception("Preview %s crashed", rid)
        try:
            sb.table("bot_preview_requests").update(
                {
                    "status": "error",
                    "error": str(exc),
                    "processed_at": datetime.now(UTC).isoformat(),
                }
            ).eq("id", rid).execute()
        except Exception:
            log.exception("Could not even mark preview %s as error", rid)


async def poll_preview_requests(bot: Bot) -> None:
    """Forever-loop. Fetches one pending row at a time and renders it."""
    sb = get_supabase()
    while True:
        try:
            resp = (
                sb.table("bot_preview_requests")
                .select("id, flow_id, graph, target_telegram_id")
                .eq("status", "pending")
                .order("created_at")
                .limit(1)
                .execute()
            )
            rows = resp.data or []
            if rows:
                row = rows[0]
                # Best-effort claim: flip to "processing" before doing work.
                # If two pollers ever run, the second will simply find nothing.
                claim = (
                    sb.table("bot_preview_requests")
                    .update({"status": "processing"})
                    .eq("id", row["id"])
                    .eq("status", "pending")
                    .execute()
                )
                if claim.data:
                    await _process_one(bot, row)
                    continue  # check immediately for more
        except Exception:
            log.exception("preview poller loop iteration crashed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
