"""Лёгкая разметка для текстов в блоках. Конвертируется в Telegram HTML.

Синтаксис (всё закрывается ``~``):

    ~b:жирный~                  → <b>жирный</b>
    ~i:курсив~                  → <i>курсив</i>
    ~u:подчёркнутый~            → <u>подчёркнутый</u>
    ~s:зачёркнутый~             → <s>зачёркнутый</s>
    ~code:моноширинный~         → <code>моноширинный</code>
    ~spoiler:скрытый~           → <tg-spoiler>скрытый</tg-spoiler>
    ~q:цитата~                  → <blockquote>цитата</blockquote>
    ~qx:раскрывающаяся цитата~  → <blockquote expandable>...</blockquote>
    ~link:https://x.com|текст~  → <a href="https://x.com">текст</a>
    ~emoji:5368324170671202286|⭐~ → <tg-emoji emoji-id="5368324170671202286">⭐</tg-emoji>

Можно вкладывать (но Telegram ругается на вложенный <a>): `~b:текст ~i:курсивом~ внутри~`

Применяется автоматически в render() для всех строк-параметров (см. vars.py).
"""

from __future__ import annotations

import html
import re

# Один токен: ~TAG:CONTENT~ (без вложенных ~)
# CONTENT может содержать |, разделяющий аргументы (для link и emoji).
# Используем не-жадный матч и допускаем рекурсию через многократный проход.
_TAG_RE = re.compile(r"~(\w+):([^~]+)~")

# Простые однопараметровые теги
_SIMPLE = {
    "b": "<b>{}</b>",
    "i": "<i>{}</i>",
    "u": "<u>{}</u>",
    "s": "<s>{}</s>",
    "code": "<code>{}</code>",
    "spoiler": "<tg-spoiler>{}</tg-spoiler>",
    "q": "<blockquote>{}</blockquote>",
    "qx": "<blockquote expandable>{}</blockquote>",
}


def _replace(match: re.Match[str]) -> str:
    tag = match.group(1).lower()
    raw = match.group(2)
    if tag in _SIMPLE:
        return _SIMPLE[tag].format(raw)
    if tag == "link":
        # ~link:url|текст~
        if "|" in raw:
            url, text = raw.split("|", 1)
        else:
            url, text = raw, raw
        url = url.strip()
        text = text.strip() or url
        # Безопасные схемы
        if not (url.startswith(("https://", "http://", "tg://")) or url.startswith("t.me/")):
            return text  # пропускаем как обычный текст
        return f'<a href="{html.escape(url, quote=True)}">{text}</a>'
    if tag == "emoji":
        # ~emoji:ID|fallback~
        if "|" in raw:
            eid, fallback = raw.split("|", 1)
        else:
            eid, fallback = raw, "⭐"
        eid = eid.strip()
        fallback = fallback.strip() or "⭐"
        if not eid.isdigit():
            return fallback
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    # Неизвестный тег — оставить как есть
    return match.group(0)


def light_to_html(text: str) -> str:
    """Конвертирует ``~b:...~`` синтаксис в HTML. Проходит до 4 итераций для вложений."""
    if not isinstance(text, str) or "~" not in text:
        return text
    out = text
    for _ in range(4):
        new = _TAG_RE.sub(_replace, out)
        if new == out:
            break
        out = new
    return out


# ---- Валидация (для AI-валидатора) ----

# Допустимые теги
ALLOWED_TAGS = set(_SIMPLE.keys()) | {"link", "emoji"}


def find_format_issues(text: str) -> list[str]:
    """Возвращает список текстовых описаний ошибок в разметке (для подсветки)."""
    if not isinstance(text, str) or "~" not in text:
        return []
    issues: list[str] = []
    # Сначала выжмем все валидные теги (поддерживает вложение через многопроходную замену)
    stripped = text
    for _ in range(8):
        new_stripped = _TAG_RE.sub("X", stripped)
        if new_stripped == stripped:
            break
        stripped = new_stripped
    # И только теперь проверяем оставшиеся ~ — если их нечётное число, что-то не закрыто
    remaining = stripped.count("~")
    if remaining % 2 != 0:
        issues.append(f"Нечётное число «~» ({remaining} остались) — где-то не закрыта разметка")
    # Неизвестные теги
    for m in _TAG_RE.finditer(text):
        tag = m.group(1).lower()
        if tag not in ALLOWED_TAGS:
            issues.append(
                f"Неизвестный тег ~{tag}:...~ (допустимы: {', '.join(sorted(ALLOWED_TAGS))})"
            )
    # link без url-схемы
    for m in re.finditer(r"~link:([^~|]+)(?:\|[^~]+)?~", text):
        url = m.group(1).strip()
        if not (url.startswith(("https://", "http://", "tg://")) or url.startswith("t.me/")):
            issues.append(
                f"~link: «{url}» — недопустимая схема (нужно https://, http://, tg:// или t.me/)"
            )
    # emoji без id
    for m in re.finditer(r"~emoji:([^~|]+)(?:\|[^~]+)?~", text):
        eid = m.group(1).strip()
        if not eid.isdigit():
            issues.append(f"~emoji: «{eid}» — id должен быть числовым (custom_emoji_id)")
    return issues
