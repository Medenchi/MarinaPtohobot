"""Bot flow CRUD + publish + preview endpoints (admin only)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.auth import require_admin
from app.bot.runtime import registry
from app.bot.runtime.preview import default_flow_graph, run_preview
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/flows", dependencies=[Depends(require_admin)])


class FlowIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    graph: dict[str, Any] = Field(default_factory=lambda: {"nodes": [], "edges": []})


class FlowPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    graph: dict[str, Any] | None = None


@router.get("")
def list_flows() -> list[dict[str, Any]]:
    sb = get_supabase()
    resp = (
        sb.table("bot_flows")
        .select(
            "id, name, description, is_published, version, published_at, created_at, updated_at"
        )
        .order("updated_at", desc=True)
        .execute()
    )
    return resp.data or []


@router.post("", status_code=201)
def create_flow(payload: FlowIn) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("bot_flows").insert(payload.model_dump()).execute()
    if not resp.data:
        raise HTTPException(500, "Insert failed")
    return resp.data[0]


@router.post("/seed", status_code=201)
def seed_flow() -> dict[str, Any]:
    """Insert the starter graph (color quiz -> outfit PDF) as a new draft."""
    sb = get_supabase()
    resp = (
        sb.table("bot_flows")
        .insert(
            {
                "name": "Подбор образов — стартовая",
                "description": "Сгенерированный пример: цветовой квиз → подборка → PDF → запись на съёмку.",
                "graph": default_flow_graph(),
            },
        )
        .execute()
    )
    if not resp.data:
        raise HTTPException(500, "Seed failed")
    return resp.data[0]


@router.get("/{flow_id}")
def get_flow(flow_id: str) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("bot_flows").select("*").eq("id", flow_id).limit(1).execute()
    rows = resp.data or []
    if not rows:
        raise HTTPException(404, "Flow not found")
    return rows[0]


@router.patch("/{flow_id}")
def update_flow(flow_id: str, payload: FlowPatch) -> dict[str, Any]:
    sb = get_supabase()
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not upd:
        raise HTTPException(400, "Empty patch")
    resp = sb.table("bot_flows").update(upd).eq("id", flow_id).execute()
    if not resp.data:
        raise HTTPException(404, "Flow not found")
    return resp.data[0]


@router.delete("/{flow_id}", status_code=204)
def delete_flow(flow_id: str) -> None:
    sb = get_supabase()
    sb.table("bot_flows").delete().eq("id", flow_id).execute()
    registry.invalidate()


@router.post("/{flow_id}/publish")
def publish_flow(flow_id: str) -> dict[str, Any]:
    sb = get_supabase()
    target = sb.table("bot_flows").select("*").eq("id", flow_id).limit(1).execute().data
    if not target:
        raise HTTPException(404, "Flow not found")
    sb.table("bot_flows").update({"is_published": False}).neq("id", flow_id).execute()
    resp = (
        sb.table("bot_flows")
        .update(
            {
                "is_published": True,
                "published_at": datetime.now(tz=UTC).isoformat(),
                "version": (target[0].get("version") or 1) + 1,
            },
        )
        .eq("id", flow_id)
        .execute()
    )
    registry.invalidate()
    return resp.data[0] if resp.data else target[0]


@router.post("/{flow_id}/unpublish")
def unpublish_flow(flow_id: str) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("bot_flows").update({"is_published": False}).eq("id", flow_id).execute()
    registry.invalidate()
    if not resp.data:
        raise HTTPException(404, "Flow not found")
    return resp.data[0]


@router.post("/{flow_id}/preview")
async def preview_flow(flow_id: str) -> dict[str, Any]:
    """Send the draft graph to the bot owner's Telegram chat."""
    from app.bot.main import shared_bot

    ok, msg = await run_preview(bot=shared_bot(), flow_id=flow_id)
    if not ok:
        raise HTTPException(400, msg)
    return {"ok": True, "message": msg}


@router.post("/{flow_id}/duplicate", status_code=201)
def duplicate_flow(flow_id: str) -> dict[str, Any]:
    sb = get_supabase()
    src = sb.table("bot_flows").select("*").eq("id", flow_id).limit(1).execute().data
    if not src:
        raise HTTPException(404, "Flow not found")
    s = src[0]
    resp = (
        sb.table("bot_flows")
        .insert(
            {
                "name": (s.get("name") or "Flow") + " (copy)",
                "description": s.get("description"),
                "graph": s.get("graph") or {"nodes": [], "edges": []},
            },
        )
        .execute()
    )
    if not resp.data:
        raise HTTPException(500, "Duplicate failed")
    return resp.data[0]


@router.get("/{flow_id}/export")
def export_flow(flow_id: str) -> dict[str, Any]:
    sb = get_supabase()
    rows = sb.table("bot_flows").select("name, description, graph").eq("id", flow_id).execute().data
    if not rows:
        raise HTTPException(404, "Flow not found")
    return rows[0]


class FlowImport(BaseModel):
    name: str | None = None
    description: str | None = None
    graph: dict[str, Any]


@router.post("/import", status_code=201)
def import_flow(payload: Annotated[FlowImport, ...]) -> dict[str, Any]:
    sb = get_supabase()
    name = payload.name or "Imported flow"
    resp = (
        sb.table("bot_flows")
        .insert({"name": name, "description": payload.description, "graph": payload.graph})
        .execute()
    )
    if not resp.data:
        raise HTTPException(500, "Import failed")
    return resp.data[0]
