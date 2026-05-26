"""Build aiogram keyboards from block params.

A ``send_message`` block can declare either:

* ``buttons``:        inline-buttons (rows of clickable options that advance
                      to a target node or open a URL)
* ``reply_keyboard``: reply keyboard (visible under the text input) — useful
                      for "Yes/No" style answers and command-like shortcuts
"""

from __future__ import annotations

from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.bot.runtime.vars import render

CB_PREFIX = "n:"


def cb_for(node_id: str, value: str | None = None) -> str:
    """callback_data the engine recognises (max 64 bytes, see TG API)."""
    if value:
        return f"{CB_PREFIX}{node_id}|{value}"[:64]
    return f"{CB_PREFIX}{node_id}"[:64]


def parse_cb(data: str) -> tuple[str, str | None] | None:
    if not data.startswith(CB_PREFIX):
        return None
    rest = data[len(CB_PREFIX) :]
    if "|" in rest:
        node, value = rest.split("|", 1)
        return node, value
    return rest, None


def build_inline(
    buttons: list[dict[str, Any]] | None,
    ctx: dict[str, Any],
) -> InlineKeyboardMarkup | None:
    """``buttons``: list of either button dicts or list-of-button dicts (rows).

    Each button dict supports:
      * ``text``      (required, template-rendered)
      * ``next``      (node id to advance to when clicked)
      * ``value``     (optional, stored in the variable of the *current* ask_question)
      * ``url``       (open external URL instead of advancing)
    """
    if not buttons:
        return None
    rows: list[list[InlineKeyboardButton]] = []
    for entry in buttons:
        row_entries = entry if isinstance(entry, list) else [entry]
        row: list[InlineKeyboardButton] = []
        for b in row_entries:
            if not isinstance(b, dict):
                continue
            text = str(render(b.get("text") or "", ctx))
            if b.get("url"):
                row.append(InlineKeyboardButton(text=text, url=str(b["url"])))
                continue
            target = b.get("next") or b.get("target")
            value = b.get("value")
            data = cb_for(str(target or ""), str(value) if value is not None else None)
            row.append(InlineKeyboardButton(text=text, callback_data=data))
        if row:
            rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def build_reply(
    rows: list[Any] | None,
    ctx: dict[str, Any],
    *,
    one_time: bool = True,
) -> ReplyKeyboardMarkup | ReplyKeyboardRemove | None:
    if rows is None:
        return None
    if rows == [] or rows == "remove":
        return ReplyKeyboardRemove()
    kb_rows: list[list[KeyboardButton]] = []
    for entry in rows:
        row_entries = entry if isinstance(entry, list) else [entry]
        row: list[KeyboardButton] = []
        for b in row_entries:
            label = str(render(b if isinstance(b, str) else b.get("text") or "", ctx))
            if label:
                row.append(KeyboardButton(text=label))
        if row:
            kb_rows.append(row)
    if not kb_rows:
        return None
    return ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True, one_time_keyboard=one_time)
