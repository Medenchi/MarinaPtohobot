"""Block implementations. Each takes ``(bot, ctx, node)`` and returns the
id of the next node to execute, or ``None`` to suspend the flow.

If a block performs a side-effect (sends a message, queries the DB, etc) and
then naturally advances, it returns ``node['next']`` or whatever the routing
rules dictate. ``ask_question``-style blocks return ``None`` so the engine
pauses until the user replies, at which point the engine routes by looking at
the *current* node when input arrives.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
from typing import TYPE_CHECKING, Any

import httpx
from aiogram.enums import ChatAction
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    URLInputFile,
)

from app.bot.runtime.keyboards import build_inline, build_reply
from app.bot.runtime.pdf import generate_pdf, generate_pdf_sections, upload_pdf
from app.bot.runtime.state import log_event
from app.bot.runtime.vars import render
from app.core.config import settings
from app.core.supabase import get_supabase

if TYPE_CHECKING:
    from aiogram import Bot

    from app.bot.runtime.engine import ExecutionContext

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sending content
# ---------------------------------------------------------------------------


def _normalize_parse_mode(mode: str | None) -> str:
    """Markdown/md/null → HTML. Тексты с ~tag:..~ через light_to_html всегда дают HTML."""
    if not mode:
        return "HTML"
    m = str(mode).strip().lower()
    if m in ("html", "htm"):
        return "HTML"
    if m in ("markdown", "md"):
        # У нас вся разметка в HTML — Markdown сломается на наших тегах
        return "HTML"
    if m in ("markdownv2", "markdown_v2", "markdown-v2"):
        return "MarkdownV2"
    return "HTML"


def _strip_invalid_emoji(text: str) -> str:
    """Убирает <tg-emoji emoji-id="...">fb</tg-emoji>, оставляя только fb."""
    return re.sub(r"<tg-emoji emoji-id=\"\d+\">([^<]+)</tg-emoji>", r"\1", text)


def _strip_invalid_emoji_kb(kb):
    """Убирает icon_custom_emoji_id из всех кнопок клавиатуры (на случай retry)."""
    if kb is None or not hasattr(kb, "inline_keyboard"):
        return kb
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    new_rows = []
    for row in kb.inline_keyboard:
        new_row = []
        for b in row:
            data = b.model_dump(exclude_none=True)
            data.pop("icon_custom_emoji_id", None)
            data.pop("style", None)
            new_row.append(InlineKeyboardButton(**data))
        new_rows.append(new_row)
    return InlineKeyboardMarkup(inline_keyboard=new_rows)


async def send_message(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    from aiogram.exceptions import TelegramBadRequest

    p = node.get("params") or {}
    text = str(render(p.get("text") or "", ctx.template_ctx))
    if not text:
        text = "…"
    parse_mode = _normalize_parse_mode(p.get("parse_mode"))
    kb = build_inline(p.get("buttons"), ctx.template_ctx)
    if kb is None:
        kb = build_reply(p.get("reply_keyboard"), ctx.template_ctx)
    try:
        await bot.send_message(
            chat_id=ctx.chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=kb,
            disable_web_page_preview=bool(p.get("disable_preview", True)),
        )
    except TelegramBadRequest as exc:
        msg = str(exc).lower()
        # DOCUMENT_INVALID / MEDIA_EMPTY / CUSTOM_EMOJI_INVALID — premium-эмодзи невалиден
        # Retry без premium-emoji: чистим текст и кнопки
        if any(
            k in msg
            for k in (
                "document_invalid",
                "media_empty",
                "custom_emoji",
                "invalid button style",
                "tg-emoji",
            )
        ):
            log.warning("send_message retry without premium emojis: %s", str(exc)[:120])
            await bot.send_message(
                chat_id=ctx.chat_id,
                text=_strip_invalid_emoji(text),
                parse_mode=parse_mode,
                reply_markup=_strip_invalid_emoji_kb(kb),
                disable_web_page_preview=bool(p.get("disable_preview", True)),
            )
        else:
            raise
    return _advance(node)


async def send_photo(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    url = str(render(p.get("url") or p.get("photo") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
    kb = build_inline(p.get("buttons"), ctx.template_ctx)
    await bot.send_photo(
        chat_id=ctx.chat_id,
        photo=URLInputFile(url),
        caption=caption,
        reply_markup=kb,
    )
    return _advance(node)


async def send_album(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list) or not items:
        # Nothing to send, just advance.
        return _advance(node)
    caption_t = p.get("caption_template") or ""
    media: list[InputMediaPhoto] = []
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    for item in items[:10]:  # Telegram limit
        if not isinstance(item, dict):
            continue
        imgs = item.get("outfit_images") or []
        if not imgs:
            continue
        path = imgs[0].get("storage_path")
        if not path:
            continue
        cap_ctx = {**ctx.template_ctx, "outfit": item}
        cap = str(render(caption_t, cap_ctx)) if caption_t else (item.get("title") or "")
        media.append(
            InputMediaPhoto(
                media=URLInputFile(f"{base}/storage/v1/object/public/{bucket}/{path}"),
                caption=cap[:1024] if cap else None,
            ),
        )
    if media:
        await bot.send_media_group(chat_id=ctx.chat_id, media=media)
    return _advance(node)


async def send_document(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    src = str(render(p.get("file") or p.get("url") or "", ctx.template_ctx))
    caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
    filename = str(render(p.get("filename") or "", ctx.template_ctx)) or None
    if not src:
        return _advance(node)
    if src.startswith("http"):
        document: Any = URLInputFile(src, filename=filename)
    else:
        document = src  # already a file_id
    await bot.send_document(chat_id=ctx.chat_id, document=document, caption=caption)
    return _advance(node)


async def send_video(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    url = str(render(p.get("url") or p.get("video") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
    await bot.send_video(chat_id=ctx.chat_id, video=URLInputFile(url), caption=caption)
    return _advance(node)


async def typing(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    secs = float(p.get("seconds") or 1.5)
    await bot.send_chat_action(chat_id=ctx.chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(min(max(secs, 0.1), 8.0))
    return _advance(node)


async def delay(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    await asyncio.sleep(min(max(float(p.get("seconds") or 1.0), 0.1), 30.0))
    return _advance(node)


# ---------------------------------------------------------------------------
# Asking the user / suspending
# ---------------------------------------------------------------------------


async def ask_question(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    """Send a prompt and suspend the flow until the user replies."""
    p = node.get("params") or {}
    text = str(render(p.get("text") or "?", ctx.template_ctx))
    options = p.get("options") or []
    inline = bool(p.get("inline", True))
    kb: Any = None
    if options and inline:
        buttons = []
        for opt in options:
            if isinstance(opt, str):
                buttons.append({"text": opt, "next": node["id"], "value": opt})
            elif isinstance(opt, dict):
                buttons.append(
                    {
                        "text": opt.get("text") or opt.get("value"),
                        "next": node["id"],
                        "value": opt.get("value") or opt.get("text"),
                    }
                )
        kb = build_inline(buttons, ctx.template_ctx)
    elif options:
        kb = build_reply(
            [[o if isinstance(o, str) else o.get("text", "")] for o in options],
            ctx.template_ctx,
        )
    await bot.send_message(
        chat_id=ctx.chat_id,
        text=text,
        reply_markup=kb,
        parse_mode=p.get("parse_mode") or "HTML",
    )
    # Suspend.
    ctx.session.awaiting_input = True
    return None


# ---------------------------------------------------------------------------
# Logic / variables / branching
# ---------------------------------------------------------------------------


async def set_variable(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    name = str(p.get("name") or "").strip()
    if not name:
        return _advance(node)
    value = render(p.get("value"), ctx.template_ctx)
    ctx.vars[name] = value
    return _advance(node)


async def branch(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    left = render(p.get("variable") or p.get("left"), ctx.template_ctx)
    right = render(p.get("value") or p.get("right"), ctx.template_ctx)
    op = (p.get("op") or "eq").lower()
    if _compare(left, right, op):
        return p.get("true_next") or node.get("next")
    return p.get("false_next") or node.get("else") or None


def _compare(left: Any, right: Any, op: str) -> bool:
    if op == "eq":
        return str(left) == str(right)
    if op == "neq":
        return str(left) != str(right)
    if op == "contains":
        if isinstance(left, list):
            return any(str(x) == str(right) for x in left)
        return str(right) in str(left)
    if op == "not_contains":
        if isinstance(left, list):
            return all(str(x) != str(right) for x in left)
        return str(right) not in str(left)
    if op == "in":
        if isinstance(right, list):
            return any(str(x) == str(left) for x in right)
        return str(left) in str(right)
    if op == "gt":
        try:
            return float(left) > float(right)
        except (TypeError, ValueError):
            return False
    if op == "lt":
        try:
            return float(left) < float(right)
        except (TypeError, ValueError):
            return False
    if op == "empty":
        if isinstance(left, list | dict | str):
            return len(left) == 0
        return left in (None, "")
    if op == "not_empty":
        if isinstance(left, list | dict | str):
            return len(left) > 0
        return left not in (None, "")
    return False


async def goto(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    return p.get("next") or node.get("next")


async def end(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    ctx.session.awaiting_input = False
    ctx.session.current_node_id = None
    return None


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


async def db_query(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    table = str(p.get("table") or "")
    if not table:
        return _advance(node)
    select = str(p.get("select") or "*")
    filters = p.get("filters") or []
    limit = int(p.get("limit") or 50)
    order = p.get("order_by")
    save_to = str(p.get("save_to") or "result")

    sb = get_supabase()
    q = sb.table(table).select(select)
    for f in filters:
        if not isinstance(f, dict):
            continue
        col = f.get("column")
        op = (f.get("op") or "eq").lower()
        val = render(f.get("value"), ctx.template_ctx)
        if col is None or val in (None, ""):
            continue
        # Защита: ilike "%%" или "%   %" — фильтр бессмысленный, скипаем
        if (f.get("op") or "").lower() == "ilike":
            stripped = str(val).strip().strip("%").strip()
            if not stripped:
                continue
        if op == "eq":
            q = q.eq(col, val)
        elif op == "neq":
            q = q.neq(col, val)
        elif op == "in":
            vals = val if isinstance(val, list) else [val]
            q = q.in_(col, vals)
        elif op == "contains_any":
            vals = val if isinstance(val, list) else [val]
            ors = ",".join(f"{col}.ilike.%{v}%" for v in vals if v)
            if ors:
                q = q.or_(ors)
        elif op == "ilike":
            q = q.ilike(col, f"%{val}%")
        elif op == "is_true":
            q = q.eq(col, True)
        elif op == "is_published":
            q = q.eq("is_published", True)
    if order:
        # order может быть "col" или "col desc" или "col asc" — парсим оба варианта
        order_str = str(order).strip()
        order_desc = bool(p.get("descending", False))
        if " desc" in order_str.lower():
            order_str = order_str.lower().replace(" desc", "").strip()
            order_desc = True
        elif " asc" in order_str.lower():
            order_str = order_str.lower().replace(" asc", "").strip()
            order_desc = False
        q = q.order(order_str, desc=order_desc)
    q = q.limit(limit)
    try:
        resp = q.execute()
        rows = resp.data or []
    except Exception as exc:
        log.warning("db_query failed: %s", exc)
        rows = []
    ctx.vars[save_to] = rows
    ctx.vars[f"{save_to}_count"] = len(rows)
    return _advance(node)


async def db_insert(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    table = str(p.get("table") or "")
    if not table:
        return _advance(node)
    raw_fields = p.get("fields") or {}
    row = {k: render(v, ctx.template_ctx) for k, v in raw_fields.items()}
    # Auto-fill telegram fields for bookings convenience.
    if table == "bookings":
        row.setdefault("telegram_id", ctx.tg_user.get("id"))
        row.setdefault("telegram_username", ctx.tg_user.get("username") or "")
    sb = get_supabase()
    try:
        resp = sb.table(table).insert(row).execute()
        if resp.data and p.get("save_to"):
            ctx.vars[str(p["save_to"])] = resp.data[0]
    except Exception as exc:
        log.warning("db_insert into %s failed: %s", table, exc)
    return _advance(node)


# ---------------------------------------------------------------------------
# Specials
# ---------------------------------------------------------------------------


async def generate_pdf_block(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list):
        items = []

    blob = generate_pdf(
        outfits=items,
        client_username=str(
            ctx.tg_user.get("username") or ctx.tg_user.get("first_name") or "клиент"
        ),
        bot_username=settings.bot_username or "bot",
    )

    # Persist to Storage for the record (and so /mama can re-download).
    try:
        url = upload_pdf(blob, telegram_id=int(ctx.tg_user.get("id") or 0))
    except Exception as exc:
        log.warning("PDF upload failed: %s", exc)
        url = ""

    file_name = str(render(p.get("filename") or "podbor_obrazov.pdf", ctx.template_ctx))
    save_to = str(p.get("save_to") or "pdf")
    ctx.vars[save_to] = {"url": url, "filename": file_name, "size": len(blob)}

    # Optional immediate send.
    if p.get("send_now", True):
        caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
        await bot.send_document(
            chat_id=ctx.chat_id,
            document=BufferedInputFile(blob, filename=file_name),
            caption=caption,
        )
    log_event(
        telegram_id=ctx.tg_user.get("id"),
        telegram_username=ctx.tg_user.get("username"),
        flow_id=ctx.flow_id,
        node_id=node.get("id"),
        event_type="pdf_generated",
        payload={"items_count": len(items), "url": url},
    )
    return _advance(node)


async def http_request(bot: Bot, ctx: ExecutionContext, node: dict[str, Any]) -> str | None:
    p = node.get("params") or {}
    url = str(render(p.get("url") or "", ctx.template_ctx))
    if not url:
        return _advance(node)
    method = (p.get("method") or "GET").upper()
    headers = render(p.get("headers") or {}, ctx.template_ctx) or {}
    body = render(p.get("body"), ctx.template_ctx)
    save_to = str(p.get("save_to") or "")
    try:
        async with httpx.AsyncClient(timeout=15.0) as cli:
            resp = await cli.request(
                method=method,
                url=url,
                headers={str(k): str(v) for k, v in headers.items()},
                json=body if method != "GET" else None,
                params=body if method == "GET" and isinstance(body, dict) else None,
            )
            try:
                data: Any = resp.json()
            except Exception:
                data = resp.text
            if save_to:
                ctx.vars[save_to] = data
                ctx.vars[f"{save_to}_status"] = resp.status_code
    except Exception as exc:
        log.warning("http_request failed: %s", exc)
        if save_to:
            ctx.vars[save_to] = None
            ctx.vars[f"{save_to}_status"] = 0
    return _advance(node)


async def handoff_to_admin(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    p = node.get("params") or {}
    if not settings.bot_owner_telegram_id:
        return _advance(node)
    summary = str(
        render(p.get("message") or "Новая заявка от {{user.full_name}}", ctx.template_ctx)
    )
    # Compact vars dump for the admin
    dump_lines = [f"{k}: {v}" for k, v in ctx.vars.items() if not k.startswith("_")]
    body = io.StringIO()
    body.write(summary + "\n\n")
    if dump_lines:
        body.write("Данные:\n" + "\n".join(dump_lines))
    try:
        await bot.send_message(
            chat_id=settings.bot_owner_telegram_id,
            text=body.getvalue()[:4000],
        )
    except Exception as exc:
        log.warning("handoff_to_admin send failed: %s", exc)
    return _advance(node)


# ---------------------------------------------------------------------------
# Registry / helpers
# ---------------------------------------------------------------------------


async def show_outfits_voting(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Карусель образов с лайками.

    Отправляет N карточек (фото + название + кнопки 👍/💔). Каждое нажатие
    записывает outfit_id в vars[liked_var] / vars[disliked_var]. Это
    one-shot блок — после отправки сразу advance, кнопки работают в фоне
    через стандартный callback-механизм.
    """
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list) or not items:
        return _advance(node)

    liked_var = p.get("liked_var") or "liked_ids"
    disliked_var = p.get("disliked_var") or "disliked_ids"
    next_id = node.get("next") or ""

    # Инициализируем коллекции в vars (если ещё нет)
    ctx.vars.setdefault(liked_var, [])
    ctx.vars.setdefault(disliked_var, [])

    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits

    intro = str(render(p.get("intro") or "", ctx.template_ctx))
    if intro:
        await bot.send_message(chat_id=ctx.chat_id, text=intro, parse_mode="HTML")

    max_count = int(p.get("limit") or 10)
    for item in items[:max_count]:
        if not isinstance(item, dict):
            continue
        imgs = item.get("outfit_images") or []
        if not imgs:
            continue
        path = imgs[0].get("storage_path")
        if not path:
            continue
        title = str(item.get("title") or "Образ")
        oid = item.get("id")
        if oid is None:
            continue
        # Кнопки 👍/💔 — callback'и идут на ЭТОТ ЖЕ узел, value = "like:{id}" / "skip:{id}"
        # Финальная кнопка «Готово» ведёт к node.next
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💔",
                        callback_data=f"n:{node['id']}|skip:{oid}",
                    ),
                    InlineKeyboardButton(
                        text="👍",
                        callback_data=f"n:{node['id']}|like:{oid}",
                    ),
                ]
            ]
        )
        try:
            await bot.send_photo(
                chat_id=ctx.chat_id,
                photo=URLInputFile(f"{base}/storage/v1/object/public/{bucket}/{path}"),
                caption=title[:1024],
                reply_markup=kb,
            )
        except Exception:
            log.exception("voting photo failed for outfit %s", oid)

    done_text = str(render(p.get("done_text") or "Когда отметишь — нажми сюда:", ctx.template_ctx))
    done_btn = str(render(p.get("done_button") or "✅ Готово, дальше", ctx.template_ctx))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=done_btn, callback_data=f"n:{next_id}|done"),
            ]
        ]
    )
    await bot.send_message(
        chat_id=ctx.chat_id,
        text=done_text,
        reply_markup=kb,
        parse_mode="HTML",
    )
    # Блок «застывает» — пользователь сам решает, когда дальше
    ctx.session.awaiting_input = False
    return None


async def collect_vote(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Невидимый блок — обрабатывает 'like:<id>' / 'skip:<id>' callbacks.

    На самом деле логику сбора лайков выполняет engine при разборе callback'а
    через специальный префикс. Этот блок-обработчик не нужен — оставлен для
    совместимости со старыми флоу. NO-OP.
    """
    return _advance(node)


async def generate_pdf_voted(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """PDF c двумя секциями: «Понравилось» (liked_ids) + «Может подойти» (остальные).

    Если ни одного лайка не было — отправляет PDF без секций, все подряд.
    """
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    liked_var = p.get("liked_var") or "liked_ids"
    items = ctx.vars.get(items_key) or []
    liked_ids = ctx.vars.get(liked_var) or []
    if not isinstance(items, list) or not items:
        return _advance(node)

    liked_set = {int(x) for x in liked_ids if str(x).isdigit()}
    liked_outfits = [o for o in items if isinstance(o, dict) and int(o.get("id") or 0) in liked_set]
    other_outfits = [
        o for o in items if isinstance(o, dict) and int(o.get("id") or 0) not in liked_set
    ]

    if liked_outfits or (len(items) > 0 and liked_set):
        sections = [
            {"title": "Понравилось", "outfits": liked_outfits},
            {"title": "Может подойти", "outfits": other_outfits},
        ]
        blob = generate_pdf_sections(
            sections=sections,
            client_username=str(
                ctx.tg_user.get("username") or ctx.tg_user.get("first_name") or "клиент"
            ),
            bot_username=settings.bot_username or "bot",
        )
    else:
        # Не отмечал ничего — без категорий
        blob = generate_pdf(
            outfits=items,
            client_username=str(
                ctx.tg_user.get("username") or ctx.tg_user.get("first_name") or "клиент"
            ),
            bot_username=settings.bot_username or "bot",
        )

    try:
        url = upload_pdf(blob, telegram_id=int(ctx.tg_user.get("id") or 0))
    except Exception as exc:
        log.warning("PDF upload failed: %s", exc)
        url = ""
    save_to = str(p.get("save_to") or "pdf")
    file_name = str(render(p.get("filename") or "podbor_obrazov.pdf", ctx.template_ctx))
    ctx.vars[save_to] = {"url": url, "filename": file_name, "size": len(blob)}

    if p.get("send_now", True):
        caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
        await bot.send_document(
            chat_id=ctx.chat_id,
            document=BufferedInputFile(blob, filename=file_name),
            caption=caption,
        )
    log_event(
        telegram_id=ctx.tg_user.get("id"),
        telegram_username=ctx.tg_user.get("username"),
        flow_id=ctx.flow_id,
        node_id=node.get("id"),
        event_type="pdf_generated",
        payload={"total": len(items), "liked": len(liked_outfits)},
    )
    return _advance(node)


def _advance(node: dict[str, Any]) -> str | None:
    return node.get("next")


BLOCKS = {
    "send_message": send_message,
    "send_photo": send_photo,
    "send_album": send_album,
    "send_document": send_document,
    "send_video": send_video,
    "typing": typing,
    "delay": delay,
    "ask_question": ask_question,
    "set_variable": set_variable,
    "branch": branch,
    "goto": goto,
    "end": end,
    "db_query": db_query,
    "db_insert": db_insert,
    "generate_pdf": generate_pdf_block,
    "generate_pdf_voted": generate_pdf_voted,
    "show_outfits_voting": show_outfits_voting,
    "collect_vote": collect_vote,
    "http_request": http_request,
    "handoff_to_admin": handoff_to_admin,
}

# Triggers don't execute — they just declare entry points.
# Merge extras (30+ блоков из extra_blocks.py)
from app.bot.runtime.extra_blocks import EXTRA_BLOCKS  # noqa: E402

BLOCKS.update(EXTRA_BLOCKS)

TRIGGER_TYPES = {"command", "text_match"}
