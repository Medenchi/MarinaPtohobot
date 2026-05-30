"""Дополнение к extra_blocks: PDF grid + show_outfits_gallery.

Импортируется через extra_blocks → блоки регистрируются в EXTRA_BLOCKS.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    URLInputFile,
)

from app.bot.runtime.pdf import generate_pdf_grid, upload_pdf
from app.bot.runtime.vars import render
from app.core.config import settings

if TYPE_CHECKING:
    from aiogram import Bot

    from app.bot.runtime.engine import ExecutionContext

log = logging.getLogger(__name__)


def _advance(node: dict[str, Any]) -> str | None:
    return node.get("next")


async def generate_pdf_grid_block(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Раскадровка для печати: 4 образа на A4."""
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list) or not items:
        return _advance(node)

    liked_var = p.get("liked_var")
    if liked_var:
        liked_ids = ctx.vars.get(liked_var) or []
        liked_set = {int(x) for x in liked_ids if str(x).isdigit()}
        if liked_set:
            items = [o for o in items if isinstance(o, dict) and int(o.get("id") or 0) in liked_set]

    if not items:
        return _advance(node)

    blob = generate_pdf_grid(
        outfits=items,
        client_username=str(
            ctx.tg_user.get("username") or ctx.tg_user.get("first_name") or "клиент"
        ),
        bot_username=settings.bot_username or "bot",
    )
    try:
        url = upload_pdf(blob, telegram_id=int(ctx.tg_user.get("id") or 0))
    except Exception as exc:
        log.warning("PDF grid upload failed: %s", exc)
        url = ""
    save_to = str(p.get("save_to") or "pdf_grid")
    filename = str(render(p.get("filename") or "podborka_pechat.pdf", ctx.template_ctx))
    ctx.vars[save_to] = {"url": url, "filename": filename, "size": len(blob)}

    if p.get("send_now", True):
        caption = str(render(p.get("caption") or "", ctx.template_ctx)) or None
        await bot.send_document(
            chat_id=ctx.chat_id,
            document=BufferedInputFile(blob, filename=filename),
            caption=caption,
            parse_mode="HTML",
        )
    return _advance(node)


# ============================================================================
# ГАЛЕРЕЯ С ЛИСТАНИЕМ
# ============================================================================


def _make_gallery_kb(node_id: str) -> InlineKeyboardMarkup:
    """3 ряда: ◀ Назад / Вперёд ▶ — 👍 Нравится / 💔 Мимо — ✅ Готово."""

    def _btn(text: str, data: str, icon: str | None = None) -> InlineKeyboardButton:
        kw: dict[str, Any] = {"text": text, "callback_data": data}
        if icon and icon.isdigit():
            kw["icon_custom_emoji_id"] = icon
        return InlineKeyboardButton(**kw)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn("◀ Назад", f"gal:{node_id}:prev", "5895364284782743985"),
                _btn("Вперёд ▶", f"gal:{node_id}:next", "5895383238473421210"),
            ],
            [
                _btn("👍 Нравится", f"gal:{node_id}:like"),
                _btn("💔 Мимо", f"gal:{node_id}:skip"),
            ],
            [
                _btn("✅ Готово, собрать PDF", f"gal:{node_id}:done"),
            ],
        ]
    )


def _build_caption(item: dict[str, Any], idx: int, total: int) -> str:
    title = str(item.get("title") or "Образ")
    desc = (item.get("description") or "").strip()
    parts: list[str] = [
        f"<b>{title}</b>",
        f"<i>{idx + 1} / {total}</i>",
    ]
    if desc:
        parts.append("")
        parts.append(desc[:200])
    parts.append("")
    parts.append("<b>👇 ЛИСТАЙ кнопками ниже</b>")
    return "\n".join(parts)


async def _send_gallery_card(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
    items: list[dict[str, Any]],
    idx: int,
    edit_message_id: int | None = None,
) -> None:
    if not items:
        return
    idx = max(0, min(idx, len(items) - 1))
    item = items[idx]
    caption = _build_caption(item, idx, len(items))
    kb = _make_gallery_kb(node["id"])

    images = item.get("outfit_images") or []
    base = settings.supabase_url.rstrip("/")
    bucket = settings.storage_bucket_outfits
    photo_url = None
    if images:
        path = images[0].get("storage_path")
        if path:
            photo_url = f"{base}/storage/v1/object/public/{bucket}/{path}"

    if photo_url:
        try:
            if edit_message_id:
                await bot.edit_message_media(
                    chat_id=ctx.chat_id,
                    message_id=edit_message_id,
                    media=InputMediaPhoto(
                        media=URLInputFile(photo_url),
                        caption=caption,
                        parse_mode="HTML",
                    ),
                    reply_markup=kb,
                )
                return
            msg = await bot.send_photo(
                chat_id=ctx.chat_id,
                photo=URLInputFile(photo_url),
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb,
            )
            ctx.vars[f"_gallery_msg_{node['id']}"] = msg.message_id
            return
        except Exception as exc:
            log.warning("gallery photo failed: %s — fallback to text", exc)

    if edit_message_id:
        await bot.edit_message_text(
            chat_id=ctx.chat_id,
            message_id=edit_message_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        msg = await bot.send_message(
            chat_id=ctx.chat_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=kb,
        )
        ctx.vars[f"_gallery_msg_{node['id']}"] = msg.message_id


async def show_outfits_gallery(
    bot: Bot,
    ctx: ExecutionContext,
    node: dict[str, Any],
) -> str | None:
    """Карусель с одним образом + кнопки ◀/▶, 👍/💔, ✅ Готово."""
    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list) or not items:
        return _advance(node)

    liked_var = p.get("liked_var") or "liked_ids"
    disliked_var = p.get("disliked_var") or "disliked_ids"
    idx_var = f"_gallery_idx_{node['id']}"
    ctx.vars.setdefault(liked_var, [])
    ctx.vars.setdefault(disliked_var, [])
    ctx.vars[idx_var] = 0

    intro = str(render(p.get("intro") or "", ctx.template_ctx))
    if intro:
        await bot.send_message(chat_id=ctx.chat_id, text=intro, parse_mode="HTML")

    await _send_gallery_card(bot, ctx, node, items, 0)
    ctx.session.awaiting_input = False
    return None
