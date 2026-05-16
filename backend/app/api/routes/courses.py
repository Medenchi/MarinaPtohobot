"""Admin CRUD for courses + file uploads."""

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


class CourseIn(BaseModel):
    slug: str
    title: str
    short_description: str | None = None
    description: str | None = None
    cover_path: str | None = None
    sort_order: int = 0
    is_published: bool = True


class CoursePatch(BaseModel):
    slug: str | None = None
    title: str | None = None
    short_description: str | None = None
    description: str | None = None
    cover_path: str | None = None
    sort_order: int | None = None
    is_published: bool | None = None


@router.get("/courses")
def list_courses() -> list[dict[str, Any]]:
    sb = get_supabase()
    resp = sb.table("courses").select("*, course_files(*)").order("sort_order").execute()
    return resp.data or []


@router.post("/courses", status_code=201)
def create_course(payload: CourseIn) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("courses").insert(payload.model_dump()).execute()
    if not resp.data:
        raise HTTPException(500, "Insert failed")
    return resp.data[0]


@router.patch("/courses/{course_id}")
def update_course(course_id: int, payload: CoursePatch) -> dict[str, Any]:
    sb = get_supabase()
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    resp = sb.table("courses").update(update).eq("id", course_id).execute()
    if not resp.data:
        raise HTTPException(404, "Course not found")
    return resp.data[0]


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int) -> None:
    sb = get_supabase()
    files = (
        sb.table("course_files").select("storage_path").eq("course_id", course_id).execute().data
        or []
    )
    paths = [r["storage_path"] for r in files]
    if paths:
        try:
            sb.storage.from_(settings.storage_bucket_courses).remove(paths)
        except Exception:
            log.exception("Failed to delete course files from storage")
    sb.table("courses").delete().eq("id", course_id).execute()


@router.post("/courses/{course_id}/files", status_code=201)
async def upload_file(
    course_id: int,
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
) -> dict[str, Any]:
    sb = get_supabase()
    course = sb.table("courses").select("id").eq("id", course_id).execute().data
    if not course:
        raise HTTPException(404, "Course not found")

    suffix = ""
    if file.filename and "." in file.filename:
        suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    path = f"{course_id}/{uuid.uuid4().hex}{suffix}"

    content = await file.read()
    content_type = (
        file.content_type
        or mimetypes.guess_type(file.filename or "")[0]
        or "application/octet-stream"
    )

    try:
        sb.storage.from_(settings.storage_bucket_courses).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type, "upsert": "false"},
        )
    except Exception as exc:
        log.exception("Upload failed")
        raise HTTPException(500, f"Upload failed: {exc}") from exc

    resp = (
        sb.table("course_files")
        .insert(
            {
                "course_id": course_id,
                "title": title or file.filename or "file",
                "storage_path": path,
                "mime_type": content_type,
                "size_bytes": len(content),
            },
        )
        .execute()
    )
    if not resp.data:
        raise HTTPException(500, "Insert file record failed")
    return resp.data[0]


@router.delete("/course-files/{file_id}", status_code=204)
def delete_file(file_id: int) -> None:
    sb = get_supabase()
    row = sb.table("course_files").select("storage_path").eq("id", file_id).single().execute().data
    if not row:
        raise HTTPException(404, "File not found")
    try:
        sb.storage.from_(settings.storage_bucket_courses).remove([row["storage_path"]])
    except Exception:
        log.exception("Storage delete failed")
    sb.table("course_files").delete().eq("id", file_id).execute()
