"""Booking requests (Marina-only)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import require_mama
from app.core.supabase import get_supabase

router = APIRouter(prefix="/api/admin/bookings", dependencies=[Depends(require_mama)])


@router.get("")
def list_bookings(
    only_unread: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]]:
    sb = get_supabase()
    q = sb.table("bookings").select("*")
    if only_unread:
        q = q.eq("is_read", False)
    resp = q.order("created_at", desc=True).limit(limit).execute()
    return resp.data or []


@router.post("/{booking_id}/read")
def mark_read(booking_id: int) -> dict[str, Any]:
    sb = get_supabase()
    resp = sb.table("bookings").update({"is_read": True}).eq("id", booking_id).execute()
    if not resp.data:
        raise HTTPException(404, "Booking not found")
    return resp.data[0]


@router.delete("/{booking_id}", status_code=204)
def delete_booking(booking_id: int) -> None:
    sb = get_supabase()
    sb.table("bookings").delete().eq("id", booking_id).execute()
