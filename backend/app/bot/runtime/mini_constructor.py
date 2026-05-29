"""Мини-конструктор внутри Telegram-бота.

Доступен только владельцу (``settings.bot_owner_telegram_id``) по команде
``/builder``. Позволяет:

* посмотреть список флоу;
* увидеть карту блоков (нумерованный список + связи);
* быстро добавить простой блок (send_message / ask_question);
* выпустить/снять с публикации;
* запустить превью у себя;
* прогнать AI-валидатор и получить отчёт.

Это именно «мини» — для полноценной правки графа есть веб-конструктор.
Но базовое управление прямо из телеги полезно: пришёл feedback от Марины —
сразу поправил без открытия ноутбука.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.runtime import registry, validator
from app.core.config import settings
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

CB_PREFIX = "mc:"


def _is_owner(uid: int | None) -> bool:
    return bool(uid and settings.bot_owner_telegram_id and uid == settings.bot_owner_telegram_id)


def _kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=d) for t, d in row]
            for row in rows
        ]
    )


async def _send_main_menu(message: Message) -> None:
    flows = _list_flows()
    text = "🛠 *Мини-конструктор*\n\nВыбери действие или флоу:\n\n"
    text += "\n".join(
        f"{'⭐' if f['is_published'] else '·'} *{f['name']}* — v{f['version']}"
        for f in flows[:10]
    ) or "_нет флоу_"
    rows: list[list[tuple[str, str]]] = []
    for f in flows[:8]:
        rows.append([(f["name"][:32], f"{CB_PREFIX}open:{f['id']}")])
    rows.append([("➕ Новый флоу", f"{CB_PREFIX}new"),
                 ("🔄 Обновить", f"{CB_PREFIX}root")])
    await message.answer(text, reply_markup=_kb(rows), parse_mode="Markdown")


def _list_flows() -> list[dict[str, Any]]:
    sb = get_supabase()
    r = (sb.table("bot_flows")
           .select("id, name, version, is_published, updated_at, graph")
           .order("updated_at", desc=True)
           .limit(20)
           .execute())
    return r.data or []


def _get_flow(fid: str) -> dict[str, Any] | None:
    sb = get_supabase()
    r = sb.table("bot_flows").select("*").eq("id", fid).limit(1).execute()
    return (r.data or [None])[0]


def _save_flow(fid: str, patch: dict[str, Any]) -> None:
    sb = get_supabase()
    sb.table("bot_flows").update(patch).eq("id", fid).execute()
    registry.invalidate()


def _format_flow(flow: dict[str, Any]) -> str:
    graph = flow.get("graph") or {}
    nodes = graph.get("nodes") or []
    issues = validator.validate_graph(graph)
    summ = validator.summary(issues)
    lines = [
        f"📋 *{flow['name']}*",
        f"_v{flow['version']} • {'опубликован ⭐' if flow['is_published'] else 'черновик'}_",
        f"Узлов: {len(nodes)}  ·  "
        f"❗ {summ['error']}  ⚠ {summ['warning']}  💡 {summ['hint']}",
        "",
        "*Блоки:*",
    ]
    for i, n in enumerate(nodes[:20], 1):
        params = n.get("params") or {}
        title = params.get("text") or params.get("command") or params.get("variable") or ""
        title = str(title).replace("\n", " ")[:48]
        arrow = f" → `{n.get('next')}`" if n.get("next") else ""
        lines.append(f"{i}. `{n.get('id')}` _{n.get('type')}_ {title}{arrow}")
    if len(nodes) > 20:
        lines.append(f"…ещё {len(nodes) - 20}")
    if issues:
        lines.append("\n*AI-проверка:*")
        for it in issues[:8]:
            emoji = {"error": "❗", "warning": "⚠", "hint": "💡"}[it["level"]]
            lines.append(f"{emoji} `{it.get('node_id') or '-'}`: {it['message']}")
    return "\n".join(lines)


def _flow_kb(fid: str, published: bool) -> InlineKeyboardMarkup:
    rows: list[list[tuple[str, str]]] = [
        [("➕ Сообщение", f"{CB_PREFIX}add:{fid}:send_message"),
         ("❓ Вопрос", f"{CB_PREFIX}add:{fid}:ask_question")],
        [("🧠 AI-проверка", f"{CB_PREFIX}lint:{fid}"),
         ("👁 Превью", f"{CB_PREFIX}prev:{fid}")],
        [("⭐ Опубликовать", f"{CB_PREFIX}pub:{fid}") if not published
         else ("⏸ Снять с публикации", f"{CB_PREFIX}unpub:{fid}")],
        [("⬅ Назад", f"{CB_PREFIX}root")],
    ]
    return _kb(rows)


def make_router() -> Router:
    router = Router(name="mini_constructor")

    @router.message(Command("builder"))
    async def on_builder(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return  # тихо игнорируем не-владельцев
        await _send_main_menu(message)

    @router.callback_query(F.data.startswith(CB_PREFIX))
    async def on_cb(cq: CallbackQuery) -> None:
        if not _is_owner(cq.from_user.id if cq.from_user else None):
            await cq.answer("Доступ только владельцу", show_alert=True)
            return
        data = (cq.data or "")[len(CB_PREFIX):]
        parts = data.split(":")
        action = parts[0]
        try:
            await _dispatch(cq, action, parts[1:])
        except Exception as e:  # noqa: BLE001
            log.exception("mini-constructor error")
            await cq.answer(f"Ошибка: {e}", show_alert=True)

    return router


async def _dispatch(cq: CallbackQuery, action: str, args: list[str]) -> None:
    bot: Bot = cq.bot  # type: ignore[assignment]
    if action == "root":
        await cq.message.delete()  # type: ignore[union-attr]
        await _send_main_menu(cq.message)  # type: ignore[arg-type]
        await cq.answer()
        return
    if action == "new":
        sb = get_supabase()
        sb.table("bot_flows").insert({
            "name": "Новый флоу (из бота)",
            "graph": {"nodes": [], "edges": []},
        }).execute()
        await cq.answer("Создан")
        await cq.message.delete()  # type: ignore[union-attr]
        await _send_main_menu(cq.message)  # type: ignore[arg-type]
        return
    if action == "open":
        flow = _get_flow(args[0])
        if not flow:
            await cq.answer("Флоу не найден", show_alert=True)
            return
        await cq.message.edit_text(  # type: ignore[union-attr]
            _format_flow(flow),
            reply_markup=_flow_kb(flow["id"], flow["is_published"]),
            parse_mode="Markdown",
        )
        await cq.answer()
        return
    if action == "lint":
        flow = _get_flow(args[0])
        if not flow:
            return
        issues = validator.validate_graph(flow.get("graph") or {})
        if not issues:
            await cq.answer("✅ Чисто", show_alert=True)
            return
        text = "*AI-проверка*\n\n" + "\n".join(
            f"{ {'error': '❗', 'warning': '⚠', 'hint': '💡'}[i['level']] } "
            f"`{i.get('node_id') or '-'}` — {i['message']}"
            for i in issues[:25]
        )
        await cq.message.answer(text, parse_mode="Markdown")  # type: ignore[union-attr]
        await cq.answer()
        return
    if action == "pub":
        _save_flow(args[0], {"is_published": True, "published_at": "now()"})
        await cq.answer("Опубликовано")
        flow = _get_flow(args[0])
        if flow:
            await cq.message.edit_text(  # type: ignore[union-attr]
                _format_flow(flow),
                reply_markup=_flow_kb(flow["id"], flow["is_published"]),
                parse_mode="Markdown",
            )
        return
    if action == "unpub":
        _save_flow(args[0], {"is_published": False})
        await cq.answer("Снято")
        flow = _get_flow(args[0])
        if flow:
            await cq.message.edit_text(  # type: ignore[union-attr]
                _format_flow(flow),
                reply_markup=_flow_kb(flow["id"], flow["is_published"]),
                parse_mode="Markdown",
            )
        return
    if action == "prev":
        sb = get_supabase()
        sb.table("bot_preview_requests").insert({
            "flow_id": args[0],
            "telegram_id": cq.from_user.id,
            "status": "pending",
        }).execute()
        await cq.answer("Превью поставлено в очередь")
        return
    if action == "add":
        flow = _get_flow(args[0])
        if not flow:
            return
        block_type = args[1]
        nodes = (flow.get("graph") or {}).get("nodes") or []
        new_id = f"{block_type}_{len(nodes) + 1}"
        if block_type == "send_message":
            new_node = {"id": new_id, "type": "send_message",
                        "params": {"text": "Новое сообщение"}, "next": None}
        else:
            new_node = {"id": new_id, "type": "ask_question",
                        "params": {"text": "Новый вопрос?", "variable": "answer"},
                        "next": None}
        graph = flow.get("graph") or {"nodes": [], "edges": []}
        graph.setdefault("nodes", []).append(new_node)
        # связать с последним
        if len(graph["nodes"]) > 1:
            prev = graph["nodes"][-2]
            if not prev.get("next"):
                prev["next"] = new_id
        _save_flow(flow["id"], {"graph": graph})
        await cq.answer(f"Добавлен {new_id}")
        flow = _get_flow(flow["id"])
        if flow:
            await cq.message.edit_text(  # type: ignore[union-attr]
                _format_flow(flow),
                reply_markup=_flow_kb(flow["id"], flow["is_published"]),
                parse_mode="Markdown",
            )
        return
    await cq.answer()
