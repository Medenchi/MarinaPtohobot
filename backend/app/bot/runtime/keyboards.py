"""Build aiogram keyboards from block params.

A ``send_message`` block can declare either:

* ``buttons``:        inline-buttons (rows of clickable options that advance
                      to a target node or open a URL)
* ``reply_keyboard``: reply keyboard (visible under the text input) — useful
                      for "Yes/No" style answers and command-like shortcuts
"""

from __future__ import annotations

import re
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


# Bot API 9.4+ цвета стилей кнопок.
# ВНИМАНИЕ: Telegram принимает их ТОЛЬКО для:
#   - Direct Messages admin keyboards в каналах
#   - Business inline buttons
# В обычных чатах юзер-бота → 'Bad Request: invalid button style specified'.
# Поэтому по умолчанию мы их ВЫРЕЗАЕМ. Включи только если знаешь, что делаешь:
#   export ALLOW_INLINE_BUTTON_STYLES=1

# Telegram Bot API: только 4 валидных значения style.
# warning/secondary НЕ существуют в TG — он вернёт invalid button style.
ALLOWED_STYLES = {"default", "primary", "success", "danger"}
# Алиасы для совместимости со старыми JSON или интуитивными синонимами
STYLE_ALIASES = {
    "warning": "danger",  # жёлтого нет — даём красный
    "secondary": "default",  # серый = default
    "blue": "primary",
    "green": "success",
    "red": "danger",
    "grey": "default",
    "gray": "default",
}


def _make_button(b: dict[str, Any], ctx: dict[str, Any]) -> InlineKeyboardButton | None:
    """Создать InlineKeyboardButton с поддержкой всех современных полей aiogram 3.28:

    text (обяз.), url | callback_data | copy_text | web_app | switch_inline_query,
    style ("primary"|"success"|"danger"|"warning"|"secondary") — Bot API 9.4+,
    icon_custom_emoji_id — premium-эмодзи. ВЛАДЕЛЕЦ бота должен иметь TG Premium, тогда видят ВСЕ юзеры (и с Premium, и без). Без Premium у владельца — никто не увидит.
    color (наша эмуляция через эмодзи-кружок — оставлена для обратной совместимости).
    """
    from aiogram.types import CopyTextButton, WebAppInfo

    if not isinstance(b, dict):
        return None
    text = str(render(b.get("text") or "", ctx))
    if not text:
        return None
    # Совместимость: префикс-эмодзи через color (для send_colored_buttons)
    color_map = {
        "green": "🟢",
        "red": "🔴",
        "yellow": "🟡",
        "blue": "🔵",
        "purple": "🟣",
        "orange": "🟠",
        "black": "⚫",
        "white": "⚪",
    }
    if b.get("color") in color_map and not b.get("style"):
        text = f"{color_map[b['color']]} {text}"

    kwargs: dict[str, Any] = {"text": text}
    # Стиль кнопки (Telegram Bot API: 4 валидных значения: default/primary/success/danger)
    raw_style = b.get("style")
    if isinstance(raw_style, str):
        style_norm = STYLE_ALIASES.get(raw_style.lower().strip(), raw_style.lower().strip())
        if style_norm in ALLOWED_STYLES and style_norm != "default":
            kwargs["style"] = style_norm
    # Премиум-иконка. ВНИМАНИЕ: text уже прошёл light_to_html (~emoji:..~ → <tg-emoji>),
    # поэтому ищем именно отрендеренный тег <tg-emoji emoji-id="...">fallback</tg-emoji>.
    icon = b.get("icon_custom_emoji_id") or b.get("icon")
    if not icon:
        m = re.search(r'<tg-emoji emoji-id="(\d+)">([^<]+)</tg-emoji>\s*', text)
        if m:
            icon = m.group(1)
            fallback = m.group(2).strip()
            # В text кнопки оставляем чистый fallback (Telegram не парсит HTML в кнопках)
            text = re.sub(
                r'<tg-emoji emoji-id="\d+">[^<]+</tg-emoji>\s*', fallback + " ", text
            ).strip()
            kwargs["text"] = text
    if icon and str(icon).isdigit():
        kwargs["icon_custom_emoji_id"] = str(icon)
    # color — старая эмуляция через эмодзи (только если нативный style не задан)
    if not kwargs.get("style") and b.get("color"):
        color_map = {
            "green": "🟢",
            "red": "🔴",
            "yellow": "🟡",
            "blue": "🔵",
            "purple": "🟣",
            "orange": "🟠",
            "black": "⚫",
            "white": "⚪",
        }
        prefix = color_map.get(str(b["color"]).lower())
        if prefix and not text.startswith(prefix):
            kwargs["text"] = f"{prefix} {text}"

    # Действие — взаимоисключающие
    if b.get("url"):
        kwargs["url"] = str(b["url"])
    elif b.get("web_app"):
        kwargs["web_app"] = WebAppInfo(url=str(b["web_app"]))
    elif b.get("copy_text"):
        kwargs["copy_text"] = CopyTextButton(text=str(b["copy_text"]))
    elif b.get("switch_inline_query") is not None:
        kwargs["switch_inline_query"] = str(b["switch_inline_query"])
    else:
        target = b.get("next") or b.get("target")
        value = b.get("value")
        kwargs["callback_data"] = cb_for(
            str(target or ""), str(value) if value is not None else None
        )
    try:
        return InlineKeyboardButton(**kwargs)
    except Exception:
        # Откат: если TG/aiogram ругнётся на неподдерживаемое поле (например, старая
        # версия Telegram-клиента у юзера) — повторяем без style/icon
        for k in ("style", "icon_custom_emoji_id"):
            kwargs.pop(k, None)
        return InlineKeyboardButton(**kwargs)


def build_inline(
    buttons: list[Any] | None,
    ctx: dict[str, Any],
) -> InlineKeyboardMarkup | None:
    """``buttons``: list of button dicts ИЛИ list-of-button dicts (рядов).

    Поля кнопки (см. _make_button): text, next/target, url, web_app,
    copy_text, switch_inline_query, value, style, icon_custom_emoji_id, color.
    """
    if not buttons:
        return None
    rows: list[list[InlineKeyboardButton]] = []
    for entry in buttons:
        row_entries = entry if isinstance(entry, list) else [entry]
        row: list[InlineKeyboardButton] = []
        for b in row_entries:
            btn = _make_button(b, ctx)
            if btn is not None:
                row.append(btn)
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
