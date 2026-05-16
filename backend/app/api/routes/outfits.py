"""Admin CRUD for outfits + image uploads."""

from __future__ import annotations

import logging
import mimetypes
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.auth import require_admin
from app.core.config import settings
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class OutfitIn(BaseModel):
    title: str
    description: str | None = None
    colors: str = ""
    styles: str = ""
    seasons: str = ""
    occasions: str = ""
    body_types: str = ""
    budgets: str = ""
    shoot_types: str = ""
    price_hint: str | None = None
    external_url: str | None = None
    sort_order: int = 0
    is_published: bool = True


class OutfitPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    colors: str | None = None
    styles: str | None = None
    seasons: str | None = None
    occasions: str | None = None
    body_types: str | None = None
    budgets: str | None = None
    shoot_types: str | None = None
    price_hint: str | None = None
    external_url: str | None = None
    sort_order: int | None = None
    is_published: bool | None = None


@router.get("/outfits")
def list_outfits() -> list[dict[str, Any]]:
    sb = get_supabase()
    resp = sb.table("outfits").select("*, outfit_images(*)").order("sort_order").execute()
    return resp.data or []


@router.post("/outfits", status_code=201)
def create_outfit(payload: OutfitIn) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("outfits").insert(payload.model_dump()).execute()
    if not resp.data:
        raise HTTPException(500, "Insert failed")
    return resp.data[0]


@router.patch("/outfits/{outfit_id}")
def update_outfit(outfit_id: int, payload: OutfitPatch) -> dict[str, Any]:
    sb = get_supabase()
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    resp = sb.table("outfits").update(update).eq("id", outfit_id).execute()
    if not resp.data:
        raise HTTPException(404, "Outfit not found")
    return resp.data[0]


@router.delete("/outfits/{outfit_id}", status_code=204)
def delete_outfit(outfit_id: int) -> None:
    sb = get_supabase()
    images = (
        sb.table("outfit_images").select("storage_path").eq("outfit_id", outfit_id).execute().data
        or []
    )
    paths = [r["storage_path"] for r in images]
    if paths:
        try:
            sb.storage.from_(settings.storage_bucket_outfits).remove(paths)
        except Exception:
            log.exception("Failed to delete outfit images from storage")
    sb.table("outfits").delete().eq("id", outfit_id).execute()


@router.post("/outfits/{outfit_id}/images", status_code=201)
async def upload_image(
    outfit_id: int,
    file: Annotated[UploadFile, File()],
    caption: Annotated[str, Form()] = "",
) -> dict[str, Any]:
    sb = get_supabase()
    # Verify outfit exists
    outfit = sb.table("outfits").select("id").eq("id", outfit_id).execute().data
    if not outfit:
        raise HTTPException(404, "Outfit not found")

    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    path = f"{outfit_id}/{uuid.uuid4().hex}{suffix}"

    content = await file.read()
    content_type = (
        file.content_type
        or mimetypes.guess_type(file.filename or "")[0]
        or "application/octet-stream"
    )

    try:
        sb.storage.from_(settings.storage_bucket_outfits).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type, "upsert": "false"},
        )
    except Exception as exc:
        log.exception("Upload failed")
        raise HTTPException(500, f"Upload failed: {exc}") from exc

    resp = (
        sb.table("outfit_images")
        .insert({"outfit_id": outfit_id, "storage_path": path, "caption": caption or None})
        .execute()
    )
    if not resp.data:
        raise HTTPException(500, "Insert image record failed")
    return resp.data[0]


@router.delete("/outfit-images/{image_id}", status_code=204)
def delete_image(image_id: int) -> None:
    sb = get_supabase()
    row = (
        sb.table("outfit_images").select("storage_path").eq("id", image_id).single().execute().data
    )
    if not row:
        raise HTTPException(404, "Image not found")
    try:
        sb.storage.from_(settings.storage_bucket_outfits).remove([row["storage_path"]])
    except Exception:
        log.exception("Storage delete failed")
    sb.table("outfit_images").delete().eq("id", image_id).execute()
