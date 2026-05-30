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

from app.bot.runtime.format import light_to_html

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

        # 1) подставляем {{vars.x}} / {{user.x}}
        def _stringify(val):
            # Защита: если в vars лежит dict {text:..,value:..} (старый баг),
            # берём value. Если list — join через запятую.
            if isinstance(val, dict):
                if "value" in val:
                    return str(val["value"])
                if "text" in val:
                    return str(val["text"])
                return ""
            if isinstance(val, list):
                return ", ".join(_stringify(x) for x in val)
            return str(val) if val is not None else ""

        substituted = _TOKEN_RE.sub(
            lambda m: _stringify(_lookup(ctx, m.group(1))),
            template,
        )
        # 2) конвертируем лёгкую разметку ~b:текст~ → HTML
        return light_to_html(substituted)
    if isinstance(template, list):
        return [render(item, ctx) for item in template]
    if isinstance(template, dict):
        return {k: render(v, ctx) for k, v in template.items()}
    return template


def _current_season() -> str:
    from datetime import datetime

    m = datetime.now().month
    if m in (12, 1, 2):
        return "зима"
    if m in (3, 4, 5):
        return "весна"
    if m in (6, 7, 8):
        return "лето"
    return "осень"


def build_context(*, vars_: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime

    now = datetime.now()
    system = {
        "season": _current_season(),
        "month": now.month,
        "year": now.year,
        "date": now.strftime("%d.%m.%Y"),
        "weekday": now.weekday(),  # 0=Mon
    }
    return {"vars": vars_, "user": user, "system": system}
