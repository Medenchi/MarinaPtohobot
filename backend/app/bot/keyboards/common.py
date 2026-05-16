"""Keyboard builders with premium icon support.

Every helper accepts ``icon_id`` — a Telegram custom emoji ID.
When set and the bot owner has Premium, buttons render with a colour
icon; otherwise they fall back to a plain unicode emoji prefix.
"""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from app.core.config import settings

# ---------- Style constants (Bot API 9.4) ---------------------
# ButtonStyle enum values from aiogram / Telegram:
#   "default" | "constructive" | "destructive"
STYLE_DEFAULT = "default"
STYLE_GREEN = "constructive"
STYLE_RED = "destructive"


def _icon(emoji_id: str, fallback: str) -> dict:
    """Build kwargs for icon_custom_emoji_id if available."""
    if emoji_id:
        return {"icon_custom_emoji_id": emoji_id}
    return {}


def _text(emoji_id: str, fallback_emoji: str, label: str) -> str:
    if emoji_id:
        return label
    return f"{fallback_emoji} {label}"


# ---------- Quiz keyboards ------------------------------------


def quiz_multi_select(
    options: list[tuple[str, str]],
    selected: set[str],
    callback_prefix: str,
    done_label: str = "Далее",
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for value, label in options:
        mark = "[•]" if value in selected else "[ ]"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {label}",
                    callback_data=f"{callback_prefix}:{value}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_sparkles, "", done_label),
                callback_data=f"{callback_prefix}:done",
                style=STYLE_GREEN,
                **_icon(settings.emoji_sparkles, ""),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_single_select(
    options: list[tuple[str, str]],
    callback_prefix: str,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for value, label in options:
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{callback_prefix}:{value}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- Result / navigation keyboards ---------------------


def results_keyboard(session_id: str) -> InlineKeyboardMarkup:
    web_url = f"{settings.public_web_url}/app?s={session_id}"
    rows = [
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_obraz, "", "Посмотреть образы"),
                web_app=WebAppInfo(url=web_url),
                **_icon(settings.emoji_obraz, ""),
            )
        ],
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_website, "", "Заказать съёмку"),
                url=settings.photographer_website_url,
                style=STYLE_GREEN,
                **_icon(settings.emoji_website, ""),
            )
        ],
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_reset, "", "Пройти заново"),
                callback_data="quiz:restart",
                **_icon(settings.emoji_reset, ""),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def courses_list_keyboard(
    courses: list[dict],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for c in courses:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_text(settings.emoji_book, "", c["title"]),
                    callback_data=f"course:{c['id']}",
                    **_icon(settings.emoji_book, ""),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_detail_keyboard(course_id: int, files: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for f in files:
        is_pdf = f.get("mime_type", "").startswith("application/pdf")
        if is_pdf:
            url = f"{settings.public_web_url}/reader?course={course_id}&file={f['id']}"
            rows.append(
                [
                    InlineKeyboardButton(
                        text=_text(settings.emoji_play, "", f["title"]),
                        web_app=WebAppInfo(url=url),
                        **_icon(settings.emoji_play, ""),
                    )
                ]
            )
        else:
            storage_url = (
                f"{settings.supabase_url}/storage/v1/object/public/"
                f"{settings.storage_bucket_courses}/{f['storage_path']}"
            )
            rows.append(
                [
                    InlineKeyboardButton(
                        text=_text(settings.emoji_download, "", f["title"]),
                        url=storage_url,
                        **_icon(settings.emoji_download, ""),
                    )
                ]
            )
    rows.append(
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_back, "", "Назад к курсам"),
                callback_data="courses:back",
                **_icon(settings.emoji_back, ""),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def start_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_obraz, "", "Подобрать образ"),
                callback_data="start:obraz",
                style=STYLE_GREEN,
                **_icon(settings.emoji_obraz, ""),
            )
        ],
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_pint, "", "Бесплатные материалы"),
                callback_data="start:pint",
                **_icon(settings.emoji_pint, ""),
            )
        ],
        [
            InlineKeyboardButton(
                text=_text(settings.emoji_website, "", "Заказать съёмку"),
                url=settings.photographer_website_url,
                **_icon(settings.emoji_website, ""),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
