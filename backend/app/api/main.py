"""FastAPI admin API — password JWT auth + Supabase service-role proxy."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.auth import make_token, verify_password
from app.api.routes import courses, outfits
from app.core.config import settings


def _origins() -> list[str]:
    return [o.strip() for o in settings.cors_origins.split(",") if o.strip()]


app = FastAPI(title="Marina Photo Admin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginIn(BaseModel):
    password: str


class TokenOut(BaseModel):
    token: str


_login_router = APIRouter(prefix="/api/admin")


@_login_router.post("/login", response_model=TokenOut)
def login(payload: LoginIn) -> TokenOut:
    if not verify_password(payload.password):
        raise HTTPException(401, "Bad password")
    return TokenOut(token=make_token())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(_login_router)
app.include_router(outfits.router)
app.include_router(courses.router)
