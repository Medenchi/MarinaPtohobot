"""Simple password-based admin auth issuing short-lived JWTs."""

from __future__ import annotations

import hmac
import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_ALG = "HS256"
_security = HTTPBearer(auto_error=False)


def verify_password(plain: str) -> bool:
    if not settings.admin_password:
        return False
    return hmac.compare_digest(plain.encode("utf-8"), settings.admin_password.encode("utf-8"))


def make_token() -> str:
    payload = {
        "sub": "admin",
        "iat": int(time.time()),
        "exp": int(time.time() + settings.jwt_ttl_hours * 3600),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALG)


def require_admin(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> str:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[_ALG])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    if payload.get("sub") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not admin")
    return "admin"
