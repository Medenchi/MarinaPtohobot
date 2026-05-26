"""Two-role password auth issuing short-lived JWTs.

Roles:
  * ``admin`` - Denis, manages the bot constructor (graph editor, preview, stats).
  * ``mama``  - Marina, manages content (outfits, courses, bookings).

Both call the same FastAPI; each route declares which role(s) it allows.
"""

from __future__ import annotations

import hmac
import time
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_ALG = "HS256"
_security = HTTPBearer(auto_error=False)

Role = Literal["admin", "mama"]


def _password_for(role: Role) -> str:
    return settings.admin_password if role == "admin" else settings.mama_password


def verify_password(role: Role, plain: str) -> bool:
    expected = _password_for(role)
    if not expected:
        return False
    return hmac.compare_digest(plain.encode("utf-8"), expected.encode("utf-8"))


def make_token(role: Role) -> str:
    payload = {
        "sub": role,
        "iat": int(time.time()),
        "exp": int(time.time() + settings.jwt_ttl_hours * 3600),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALG)


def _decode(creds: HTTPAuthorizationCredentials | None) -> Role:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[_ALG])
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    sub = payload.get("sub")
    if sub not in ("admin", "mama"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bad role")
    return sub  # type: ignore[return-value]


def require_admin(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> Role:
    role = _decode(creds)
    if role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return role


def require_mama(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> Role:
    role = _decode(creds)
    # Admin can do anything Marina can.
    if role not in ("mama", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mama role required")
    return role


def require_any(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> Role:
    return _decode(creds)
