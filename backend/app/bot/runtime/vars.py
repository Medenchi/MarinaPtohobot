"""Variable substitution for block params.

A flow text like ``"Привет, {{user.first_name}}! Любишь {{vars.colors}}?"`` is
rendered against a context dict containing ``vars`` (user-collected) and
``user`` (Telegram-supplied). Anything missing renders as an empty string.

Only ``{{a.b.c}}`` style lookups are supported. No expressions, no filters.
This is intentional — flows are user-authored data, not code.
"""

from __future__ import annotations

import re
from typing import Any

_TOKEN_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _lookup(ctx: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = ctx
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return ""
    return cur


def render(template: Any, ctx: dict[str, Any]) -> Any:
    """Recursively render strings inside dicts/lists, leaving non-strings alone.

    If ``template`` is a string that is *exactly* one ``{{x}}`` token, the
    looked-up value is returned as-is (preserving lists / dicts / numbers).
    Otherwise it's stringified with ``str()``.
    """
    if isinstance(template, str):
        match = _TOKEN_RE.fullmatch(template.strip())
        if match:
            return _lookup(ctx, match.group(1))
        return _TOKEN_RE.sub(lambda m: str(_lookup(ctx, m.group(1))), template)
    if isinstance(template, list):
        return [render(item, ctx) for item in template]
    if isinstance(template, dict):
        return {k: render(v, ctx) for k, v in template.items()}
    return template


def build_context(*, vars_: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    return {"vars": vars_, "user": user}
