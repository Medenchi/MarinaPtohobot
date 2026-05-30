"""Дополнительные 30+ блоков для движка.

Категории:
* Текст (форматирование, ссылки на товары, чек-листы, цитаты, заголовки)
* Медиа (стикеры, аудио, voice, video_note, location, contact, dice, poll)
* Интерактив (copy-text кнопки, web app, share, рейтинг, лайк-счётчик)
* Логика (random_branch, switch, math, regex, schedule, time-window)
* Данные (db_update, db_count, increment_var, append_to_list)
* Интеграции (mini-app launcher, telegram-stars invoice, business reply)

Использует aiogram 3.28.x (CopyTextButton, business_message, и т.д.)
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from aiogram.enums import ChatAction
from aiogram.types import (
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    LinkPreviewOptions,
    URLInputFile,
    WebAppInfo,
)

from app.bot.runtime.middleware import clear as msgid_clear
from app.bot.runtime.middleware import get_recent, pop_last
from app.bot.runtime.vars import render
from app.core.config import settings
from app.core.supabase import get_supabase

if TYPE_CHECKING:
    from aiogram import Bot

    from app.bot.runtime.engine import ExecutionContext

log = logging.getLogger(__name__)


def _advance(node: dict[str, Any]) -> str | None:
    return node.get("next")


# ============================================================================
# ТЕКСТ И ФОРМАТИРОВАНИЕ
# ============================================================================


async def send_heading(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Большой заголовок: эмодзи + жирный + декоративная линия."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    icon = str(p.get("icon") or "✨")
    level = int(p.get("level") or 1)
    if level == 1:
        msg = f"{icon} <b>{text}</b>\n━━━━━━━━━━━━━━━━━━━"
    elif level == 2:
        msg = f"{icon} <b>{text}</b>\n─────────────"
    else:
        msg = f"{icon} <b>{text}</b>"
    await bot.send_message(chat_id=ctx.chat_id, text=msg, parse_mode="HTML")
    return _advance(node)


async def send_quote(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Цитата: использует expandable blockquote из Bot API 7.5+."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    author = str(render(p.get("author") or "", ctx.template_ctx))
    expandable = bool(p.get("expandable", False))
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    msg = f"{tag}{text}</blockquote>"
    if author:
        msg += f"\n<i>— {author}</i>"
    await bot.send_message(chat_id=ctx.chat_id, text=msg, parse_mode="HTML")
    return _advance(node)


async def send_checklist(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Маркированный чек-лист с галочками."""
    p = node.get("params") or {}
    title = str(render(p.get("title") or "", ctx.template_ctx))
    items = p.get("items") or []
    checked = p.get("checked") or []  # индексы или значения
    lines: list[str] = []
    if title:
        lines.append(f"<b>{title}</b>\n")
    for i, item in enumerate(items):
        rendered = render(item, ctx.template_ctx)
        mark = "✅" if i in checked or rendered in checked else "▫️"
        lines.append(f"{mark} {rendered}")
    await bot.send_message(chat_id=ctx.chat_id, text="\n".join(lines), parse_mode="HTML")
    return _advance(node)


async def send_numbered_list(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Нумерованный список 1. 2. 3."""
    p = node.get("params") or {}
    title = str(render(p.get("title") or "", ctx.template_ctx))
    items = p.get("items") or []
    lines: list[str] = []
    if title:
        lines.append(f"<b>{title}</b>\n")
    for i, item in enumerate(items, 1):
        lines.append(f"<b>{i}.</b> {render(item, ctx.template_ctx)}")
    await bot.send_message(chat_id=ctx.chat_id, text="\n".join(lines), parse_mode="HTML")
    return _advance(node)


async def send_kv_table(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Таблица ключ-значение: «Имя: Анна\nТелефон: ...»"""
    p = node.get("params") or {}
    title = str(render(p.get("title") or "", ctx.template_ctx))
    rows = p.get("rows") or {}
    lines: list[str] = []
    if title:
        lines.append(f"<b>{title}</b>\n")
    for k, v in rows.items():
        lines.append(f"<b>{k}:</b> {render(v, ctx.template_ctx)}")
    await bot.send_message(chat_id=ctx.chat_id, text="\n".join(lines), parse_mode="HTML")
    return _advance(node)


async def send_with_preview(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Сообщение с большим превью ссылки сверху (link_preview_options)."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    url = str(render(p.get("url") or "", ctx.template_ctx))
    above = bool(p.get("above_text", True))
    large = bool(p.get("large", True))
    options = LinkPreviewOptions(
        url=url or None,
        prefer_large_media=large,
        prefer_small_media=not large,
        show_above_text=above,
        is_disabled=False,
    )
    await bot.send_message(
        chat_id=ctx.chat_id,
        text=text,
        parse_mode="HTML",
        link_preview_options=options,
    )
    return _advance(node)


# ============================================================================
# МЕДИА
# ============================================================================


async def send_sticker(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    sticker_id = str(render(p.get("sticker_id") or "", ctx.template_ctx))
    if not sticker_id:
        return _advance(node)
    await bot.send_sticker(chat_id=ctx.chat_id, sticker=sticker_id)
    return _advance(node)


async def send_voice(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    url = str(render(p.get("url") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    await bot.send_voice(chat_id=ctx.chat_id, voice=URLInputFile(url))
    return _advance(node)


async def send_audio(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    url = str(render(p.get("url") or "", ctx.template_ctx))
    title = str(render(p.get("title") or "", ctx.template_ctx)) or None
    performer = str(render(p.get("performer") or "", ctx.template_ctx)) or None
    if not url:
        return _advance(node)
    await bot.send_audio(
        chat_id=ctx.chat_id,
        audio=URLInputFile(url),
        title=title,
        performer=performer,
    )
    return _advance(node)


async def send_video_note(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Круглое видео-сообщение."""
    p = node.get("params") or {}
    url = str(render(p.get("url") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    await bot.send_video_note(chat_id=ctx.chat_id, video_note=URLInputFile(url))
    return _advance(node)


async def send_location(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    lat = float(p.get("latitude") or 0)
    lng = float(p.get("longitude") or 0)
    await bot.send_location(chat_id=ctx.chat_id, latitude=lat, longitude=lng)
    return _advance(node)


async def send_venue(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Точка на карте с названием и адресом."""
    p = node.get("params") or {}
    await bot.send_venue(
        chat_id=ctx.chat_id,
        latitude=float(p.get("latitude") or 0),
        longitude=float(p.get("longitude") or 0),
        title=str(render(p.get("title") or "", ctx.template_ctx)),
        address=str(render(p.get("address") or "", ctx.template_ctx)),
    )
    return _advance(node)


async def send_contact(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    await bot.send_contact(
        chat_id=ctx.chat_id,
        phone_number=str(render(p.get("phone") or "", ctx.template_ctx)),
        first_name=str(render(p.get("first_name") or "", ctx.template_ctx)),
        last_name=str(render(p.get("last_name") or "", ctx.template_ctx)) or None,
    )
    return _advance(node)


async def send_dice(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Бросок 🎲🎯🏀⚽🎳🎰. Результат пишет в vars[save_to]."""
    p = node.get("params") or {}
    emoji = str(p.get("emoji") or "🎲")
    msg = await bot.send_dice(chat_id=ctx.chat_id, emoji=emoji)
    save_to = str(p.get("save_to") or "dice_value")
    if msg.dice:
        ctx.vars[save_to] = msg.dice.value
    return _advance(node)


async def send_poll(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Опрос в чате."""
    p = node.get("params") or {}
    question = str(render(p.get("question") or "", ctx.template_ctx))
    options = [str(render(o, ctx.template_ctx)) for o in (p.get("options") or [])]
    if not options:
        return _advance(node)
    await bot.send_poll(
        chat_id=ctx.chat_id,
        question=question,
        options=options,
        is_anonymous=bool(p.get("anonymous", False)),
        allows_multiple_answers=bool(p.get("multiple", False)),
    )
    return _advance(node)


async def send_chat_action(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Любое chat_action: typing/upload_photo/record_voice/..."""
    p = node.get("params") or {}
    action_name = str(p.get("action") or "typing")
    try:
        action = ChatAction(action_name)
    except ValueError:
        action = ChatAction.TYPING
    await bot.send_chat_action(chat_id=ctx.chat_id, action=action)
    secs = float(p.get("seconds") or 0)
    if secs > 0:
        await asyncio.sleep(min(secs, 8.0))
    return _advance(node)


# ============================================================================
# ИНТЕРАКТИВ
# ============================================================================


async def send_copy_button(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Сообщение с кнопкой «📋 Скопировать» (CopyTextButton из aiogram 3.17+)."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    button_text = str(render(p.get("button_text") or "📋 Скопировать", ctx.template_ctx))
    copy_text = str(render(p.get("copy_text") or "", ctx.template_ctx))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=button_text, copy_text=CopyTextButton(text=copy_text)),
            ]
        ]
    )
    await bot.send_message(chat_id=ctx.chat_id, text=text, reply_markup=kb, parse_mode="HTML")
    return _advance(node)


async def send_webapp_button(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Кнопка, открывающая Mini App."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    btn = str(render(p.get("button_text") or "🚀 Открыть", ctx.template_ctx))
    url = str(render(p.get("url") or "", ctx.template_ctx))
    if not url.startswith("https://"):
        return _advance(node)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=btn, web_app=WebAppInfo(url=url))]]
    )
    await bot.send_message(chat_id=ctx.chat_id, text=text, reply_markup=kb, parse_mode="HTML")
    return _advance(node)


async def send_share_button(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Кнопка «Поделиться ботом» — t.me share."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    btn = str(render(p.get("button_text") or "📤 Рассказать друзьям", ctx.template_ctx))
    bot_username = settings.bot_username or "marina_bot"
    share_text = str(render(p.get("share_text") or "Посмотри какой крутой бот!", ctx.template_ctx))
    bot_link = f"https://t.me/{bot_username.lstrip('@')}"
    url = f"https://t.me/share/url?url={quote(bot_link, safe='')}&text={quote(share_text, safe='')}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=btn, url=url)]])
    await bot.send_message(chat_id=ctx.chat_id, text=text, reply_markup=kb, parse_mode="HTML")
    return _advance(node)


async def send_rating(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Звёздочный рейтинг ⭐⭐⭐⭐⭐ кнопками. Результат → vars[save_to]."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "Оцени:", ctx.template_ctx))
    scale = int(p.get("scale") or 5)
    save_to = str(p.get("save_to") or "rating")
    next_id = node.get("next") or ""
    row = []
    for i in range(1, scale + 1):
        row.append(
            InlineKeyboardButton(text="⭐" * i, callback_data=f"n:{next_id}|rate:{save_to}:{i}")
        )
    kb = InlineKeyboardMarkup(inline_keyboard=[row])
    await bot.send_message(chat_id=ctx.chat_id, text=text, reply_markup=kb, parse_mode="HTML")
    ctx.session.awaiting_input = False
    return None  # ждём клика — обрабатывается в engine


# ============================================================================
# ЛОГИКА
# ============================================================================


async def random_branch(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Случайно выбирает один из вариантов в params.choices."""
    p = node.get("params") or {}
    choices = p.get("choices") or []
    if not choices:
        return _advance(node)
    pick = random.choice(choices)
    if isinstance(pick, dict):
        return pick.get("next") or _advance(node)
    return str(pick)


async def switch_block(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """switch-case по vars[var]. cases: {"love": "node_love", "family": "node_fam"}."""
    p = node.get("params") or {}
    var = str(p.get("variable") or "").strip()
    value = str(ctx.vars.get(var, "")).strip()
    cases = p.get("cases") or {}
    if value in cases:
        return str(cases[value])
    return p.get("default") or _advance(node)


async def increment_var(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Прибавить число к переменной (для счётчиков и накопления баллов)."""
    p = node.get("params") or {}
    name = str(p.get("name") or "").strip()
    if not name:
        return _advance(node)
    delta = float(p.get("delta") or 1)
    cur = ctx.vars.get(name, 0)
    try:
        ctx.vars[name] = float(cur) + delta
        if delta == int(delta) and isinstance(cur, int):
            ctx.vars[name] = int(ctx.vars[name])
    except (TypeError, ValueError):
        ctx.vars[name] = delta
    return _advance(node)


async def append_to_list(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Добавить значение в список в vars."""
    p = node.get("params") or {}
    name = str(p.get("name") or "").strip()
    if not name:
        return _advance(node)
    value = render(p.get("value"), ctx.template_ctx)
    arr = ctx.vars.get(name)
    if not isinstance(arr, list):
        arr = []
    arr.append(value)
    ctx.vars[name] = arr
    return _advance(node)


async def regex_extract(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Достать кусок из текста по регулярке. Например, телефон из последнего ответа."""
    p = node.get("params") or {}
    source = str(render(p.get("source") or "", ctx.template_ctx))
    pattern = str(p.get("pattern") or "")
    save_to = str(p.get("save_to") or "extracted")
    if not pattern:
        return _advance(node)
    try:
        m = re.search(pattern, source)
        ctx.vars[save_to] = m.group(0) if m else ""
    except re.error:
        ctx.vars[save_to] = ""
    return _advance(node)


async def math_eval(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Простая арифметика: a + b, a * b, и т.п. (только +-*/ и числа)."""
    p = node.get("params") or {}
    expr = str(render(p.get("expression") or "", ctx.template_ctx))
    save_to = str(p.get("save_to") or "result")
    # Очень узкий sanitize: только цифры, скобки, точки, +-*/
    if not re.fullmatch(r"[\d\s\.\+\-\*\/\(\)]+", expr):
        ctx.vars[save_to] = 0
    else:
        try:
            ctx.vars[save_to] = eval(expr, {"__builtins__": {}}, {})
        except Exception:
            ctx.vars[save_to] = 0
    return _advance(node)


async def time_window(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Branch по текущему времени: внутри окна (например 9:00-21:00) или нет."""
    p = node.get("params") or {}
    start = int(p.get("start_hour") or 9)
    end = int(p.get("end_hour") or 21)
    now_h = datetime.now().hour
    inside = start <= now_h < end
    if inside:
        return p.get("inside_next") or _advance(node)
    return p.get("outside_next") or _advance(node)


async def schedule_branch(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Branch по дню недели: weekdays vs weekends vs конкретный день."""
    p = node.get("params") or {}
    weekday = datetime.now().weekday()  # 0=Mon, 6=Sun
    if weekday >= 5:
        return p.get("weekend_next") or _advance(node)
    return p.get("weekday_next") or _advance(node)


# ============================================================================
# ДАННЫЕ
# ============================================================================


async def db_update(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """UPDATE по таблице."""
    p = node.get("params") or {}
    table = str(p.get("table") or "")
    if not table:
        return _advance(node)
    where = p.get("where") or {}
    fields = p.get("fields") or {}
    rendered_fields = {k: render(v, ctx.template_ctx) for k, v in fields.items()}
    sb = get_supabase()
    try:
        q = sb.table(table).update(rendered_fields)
        for col, val in where.items():
            q = q.eq(col, render(val, ctx.template_ctx))
        q.execute()
    except Exception as exc:
        log.warning("db_update failed: %s", exc)
    return _advance(node)


async def db_count(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """COUNT(*) с фильтрами в vars[save_to]."""
    p = node.get("params") or {}
    table = str(p.get("table") or "")
    if not table:
        return _advance(node)
    save_to = str(p.get("save_to") or "count")
    sb = get_supabase()
    try:
        q = sb.table(table).select("id", count="exact")
        for f in p.get("filters") or []:
            col = f.get("column")
            op = f.get("op") or "eq"
            val = render(f.get("value"), ctx.template_ctx)
            method = getattr(q, op, None)
            if method:
                q = method(col, val)
        resp = q.execute()
        ctx.vars[save_to] = resp.count or 0
    except Exception as exc:
        log.warning("db_count failed: %s", exc)
        ctx.vars[save_to] = 0
    return _advance(node)


# ============================================================================
# КОНТЕНТ-СПЕЦИФИКА (для Марины)
# ============================================================================


async def send_outfit_card(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Карточка одного образа: фото + заголовок + теги + кнопки купить/ещё."""
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    idx = int(p.get("index") or 0)
    if not isinstance(items, list) or idx >= len(items):
        return _advance(node)
    item = items[idx]
    if not isinstance(item, dict):
        return _advance(node)
    title = str(item.get("title") or "Образ")
    tags = ", ".join(
        [
            t.strip()
            for t in (str(item.get("colors") or "") + "," + str(item.get("styles") or "")).split(
                ","
            )
            if t.strip()
        ][:5]
    )
    caption = f"<b>{title}</b>\n<i>{tags}</i>"
    imgs = item.get("outfit_images") or []
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    kb_rows = []
    if item.get("external_url"):
        kb_rows.append([InlineKeyboardButton(text="🛍 Купить", url=str(item["external_url"]))])
    if imgs and imgs[0].get("storage_path"):
        url = f"{base}/storage/v1/object/public/{bucket}/{imgs[0]['storage_path']}"
        await bot.send_photo(
            chat_id=ctx.chat_id,
            photo=URLInputFile(url),
            caption=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None,
        )
    else:
        await bot.send_message(
            chat_id=ctx.chat_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None,
        )
    return _advance(node)


async def send_outfit_grid(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Медиа-группа из vars[items_var] (видео+фото вперемешку поддерживается)."""
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not items:
        return _advance(node)
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    media: list[Any] = []
    for item in items[:10]:
        if not isinstance(item, dict):
            continue
        imgs = item.get("outfit_images") or []
        if not imgs:
            continue
        path = imgs[0].get("storage_path")
        if not path:
            continue
        cap = str(item.get("title") or "")[:100]
        media.append(
            InputMediaPhoto(
                media=URLInputFile(f"{base}/storage/v1/object/public/{bucket}/{path}"),
                caption=cap if not media else None,  # подпись только на первом
            )
        )
    if media:
        await bot.send_media_group(chat_id=ctx.chat_id, media=media)
    return _advance(node)


async def show_random_outfit(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Показать случайный образ из items_var."""
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not items:
        return _advance(node)
    item = random.choice(items)
    if not isinstance(item, dict):
        return _advance(node)
    imgs = item.get("outfit_images") or []
    if not imgs:
        return _advance(node)
    path = imgs[0].get("storage_path")
    if not path:
        return _advance(node)
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    await bot.send_photo(
        chat_id=ctx.chat_id,
        photo=URLInputFile(f"{base}/storage/v1/object/public/{bucket}/{path}"),
        caption=f"<b>{item.get('title') or 'Образ'}</b>",
        parse_mode="HTML",
    )
    return _advance(node)


# ============================================================================
# Реестр (импортируется в blocks.BLOCKS)
# ============================================================================


EXTRA_BLOCKS: dict[str, Any] = {
    # Текст
    "send_heading": send_heading,
    "send_quote": send_quote,
    "send_checklist": send_checklist,
    "send_numbered_list": send_numbered_list,
    "send_kv_table": send_kv_table,
    "send_with_preview": send_with_preview,
    # Медиа
    "send_sticker": send_sticker,
    "send_voice": send_voice,
    "send_audio": send_audio,
    "send_video_note": send_video_note,
    "send_location": send_location,
    "send_venue": send_venue,
    "send_contact": send_contact,
    "send_dice": send_dice,
    "send_poll": send_poll,
    "send_chat_action": send_chat_action,
    # Интерактив
    "send_copy_button": send_copy_button,
    "send_webapp_button": send_webapp_button,
    "send_share_button": send_share_button,
    "send_rating": send_rating,
    # Логика
    "random_branch": random_branch,
    "switch": switch_block,
    "increment_var": increment_var,
    "append_to_list": append_to_list,
    "regex_extract": regex_extract,
    "math_eval": math_eval,
    "time_window": time_window,
    "schedule_branch": schedule_branch,
    # Данные
    "db_update": db_update,
    "db_count": db_count,
    # Контент-специфика
    "send_outfit_card": send_outfit_card,
    "send_outfit_grid": send_outfit_grid,
    "show_random_outfit": show_random_outfit,
}


# ============================================================================
# УПРАВЛЕНИЕ СООБЩЕНИЯМИ (удаление, авто-очистка)
# ============================================================================


async def remember_message_id(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """No-op: для совместимости. На самом деле движок и так сохраняет
    последний message_id в session.last_message_id (см. engine.py).
    """
    return _advance(node)


async def delete_last_message(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Удалить последние N сообщений бота. Защита от наслоения карточек."""
    p = node.get("params") or {}
    count = int(p.get("count") or 1)
    # Берём из RAM-кэша middleware (актуальнее, чем session)
    ram = pop_last(ctx.chat_id, count)
    persisted = ctx.session.bot_message_ids or []
    to_delete = list(dict.fromkeys(ram + persisted[-count:]))[:count]
    for mid in to_delete:
        try:
            await bot.delete_message(chat_id=ctx.chat_id, message_id=mid)
        except Exception as exc:
            log.debug("delete_message %s failed: %s", mid, exc)
    if persisted:
        ctx.session.bot_message_ids = persisted[:-count] if count <= len(persisted) else []
    return _advance(node)


async def clear_chat(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Удалить ВСЕ сообщения бота за текущую сессию. TG-лимит: 48 ч."""
    all_ids = list(dict.fromkeys(get_recent(ctx.chat_id) + (ctx.session.bot_message_ids or [])))
    for mid in all_ids:
        try:
            await bot.delete_message(chat_id=ctx.chat_id, message_id=mid)
        except Exception as exc:
            log.debug("delete_message %s failed: %s", mid, exc)
    msgid_clear(ctx.chat_id)
    ctx.session.bot_message_ids = []
    return _advance(node)


# ============================================================================
# POLL КАК ВОПРОС (с сохранением ответа в vars)
# ============================================================================


async def ask_poll(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Telegram-опрос, который ставит флоу на паузу.

    Когда юзер голосует, приходит update poll_answer — engine ловит и
    пишет результат в vars[variable], потом advance.
    """
    p = node.get("params") or {}
    question = str(render(p.get("question") or "?", ctx.template_ctx))
    options = [str(render(o, ctx.template_ctx)) for o in (p.get("options") or [])]
    variable = str(p.get("variable") or "").strip()
    if not options or not variable:
        return _advance(node)

    msg = await bot.send_poll(
        chat_id=ctx.chat_id,
        question=question,
        options=options,
        is_anonymous=False,  # обязательно False — иначе poll_answer не придёт
        allows_multiple_answers=bool(p.get("multiple", False)),
    )
    # Сохраняем poll_id → (variable, node_id, options) для последующего матчинга
    poll_map = ctx.vars.setdefault("_pending_polls", {})
    if msg.poll:
        poll_map[msg.poll.id] = {
            "variable": variable,
            "node_id": node["id"],
            "options": options,
            "multiple": bool(p.get("multiple", False)),
            "chat_id": ctx.chat_id,
            "telegram_id": ctx.session.telegram_id,
        }
    ctx.session.awaiting_input = True
    return None


# ============================================================================
# БОТ УПРАВЛЯЕТ СОБОЙ (имя, описание, аватарка)
# ============================================================================


async def set_bot_name(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    p = node.get("params") or {}
    name = str(render(p.get("name") or "", ctx.template_ctx))[:64]
    lang = str(p.get("language_code") or "")
    if name:
        try:
            await bot.set_my_name(name=name, language_code=lang or None)
        except Exception as exc:
            log.warning("set_my_name failed: %s", exc)
    return _advance(node)


async def set_bot_description(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    p = node.get("params") or {}
    desc = str(render(p.get("description") or "", ctx.template_ctx))[:512]
    lang = str(p.get("language_code") or "")
    try:
        await bot.set_my_description(description=desc, language_code=lang or None)
    except Exception as exc:
        log.warning("set_my_description failed: %s", exc)
    return _advance(node)


async def set_bot_short_description(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    p = node.get("params") or {}
    desc = str(render(p.get("short_description") or "", ctx.template_ctx))[:120]
    lang = str(p.get("language_code") or "")
    try:
        await bot.set_my_short_description(
            short_description=desc,
            language_code=lang or None,
        )
    except Exception as exc:
        log.warning("set_my_short_description failed: %s", exc)
    return _advance(node)


async def set_bot_avatar(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """aiogram 3.27+: bot.set_my_profile_photo(photo=URLInputFile(url))."""
    p = node.get("params") or {}
    url = str(render(p.get("url") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    try:
        await bot.set_my_profile_photo(photo=URLInputFile(url))
    except Exception as exc:
        log.warning("set_my_profile_photo failed: %s", exc)
    return _advance(node)


# ============================================================================
# КНОПКИ С «ЦВЕТОМ» (эмулируется через эмодзи-индикатор)
# ============================================================================


async def send_colored_buttons(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Сообщение со стилизованными кнопками.

    Каждая кнопка может иметь:
      style: primary | success | danger | warning | secondary (Bot API 9.4+)
      icon_custom_emoji_id: <id> (премиум-эмодзи; ВЛАДЕЛЕЦ бота должен иметь TG Premium → видят ВСЕ юзеры включая без Premium)
      color: green/red/yellow/... (старая эмуляция через эмодзи-кружок —
             используется ТОЛЬКО если style не задан, для обратной совместимости)
    """
    from app.bot.runtime.keyboards import build_inline

    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    kb = build_inline(p.get("buttons"), ctx.template_ctx)
    await bot.send_message(
        chat_id=ctx.chat_id,
        text=text,
        reply_markup=kb,
        parse_mode="HTML",
    )
    return _advance(node)


# ============================================================================
# Registry — расширяем EXTRA_BLOCKS
# ============================================================================

EXTRA_BLOCKS.update(
    {
        # Управление сообщениями
        "remember_message_id": remember_message_id,
        "delete_last_message": delete_last_message,
        "clear_chat": clear_chat,
        # Poll-вопрос
        "ask_poll": ask_poll,
        # Бот меняет себя
        "set_bot_name": set_bot_name,
        "set_bot_description": set_bot_description,
        "set_bot_short_description": set_bot_short_description,
        "set_bot_avatar": set_bot_avatar,
        # Цветные кнопки (через эмодзи)
        "send_colored_buttons": send_colored_buttons,
    }
)
