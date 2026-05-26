"""FastAPI admin API.

Two roles share the same API surface:

* ``admin`` (Denis) - bot constructor (flows CRUD + publish + preview),
  outfits, courses, bookings, stats.
* ``mama``  (Marina) - outfits, courses, bookings, stats only.

Each route picks a dependency (``require_admin`` / ``require_mama`` /
``require_any``) to declare which role it allows.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.auth import make_token, verify_password
from app.api.routes import bookings, courses, flows, outfits, stats
from app.core.config import settings


def _origins() -> list[str]:
    return [o.strip() for o in settings.cors_origins.split(",") if o.strip()]


app = FastAPI(title="Marina Photo Admin API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginIn(BaseModel):
    password: str
    role: Literal["admin", "mama"] = "admin"


class TokenOut(BaseModel):
    token: str
    role: Literal["admin", "mama"]


_login_router = APIRouter(prefix="/api/admin")


@_login_router.post("/login", response_model=TokenOut)
def login(payload: LoginIn) -> TokenOut:
    if not verify_password(payload.role, payload.password):
        raise HTTPException(401, "Bad password")
    return TokenOut(token=make_token(payload.role), role=payload.role)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(_login_router)
app.include_router(flows.router)
app.include_router(outfits.router)
app.include_router(courses.router)
app.include_router(bookings.router)
app.include_router(stats.router)
