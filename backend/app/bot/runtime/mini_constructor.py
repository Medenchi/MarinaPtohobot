"""Мини-конструктор внутри Telegram-бота.

Доступен только владельцу (``settings.bot_owner_telegram_id``) по команде
``/builder``. Позволяет:

* посмотреть список флоу;
* увидеть карту блоков (нумерованный список + связи);
* быстро добавить простой блок (send_message / ask_question);
* выпустить/снять с публикации;
* запустить превью у себя;
* прогнать AI-валидатор и получить отчёт.

Сообщения форматируются HTML (а не Markdown), потому что Markdown ломается
на любом спецсимволе underscore/star/backtick, который встречается в id/имени/тексте флоу.
"""

from __future__ import annotations

import contextlib
import html
import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.bot.runtime import registry, validator
from app.bot.runtime.multibot import register_child_bot
from app.core.config import settings
from app.core.supabase import get_supabase

log = logging.getLogger(__name__)

CB_PREFIX = "mc:"

LEVEL_EMOJI = {"error": "❗", "warning": "⚠", "hint": "💡"}


def _is_owner(uid: int | None) -> bool:
    return bool(uid and settings.bot_owner_telegram_id and uid == settings.bot_owner_telegram_id)


def _kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows
        ]
    )


def _esc(s: Any) -> str:
    """HTML-escape for safe rendering inside <b>/<code>/etc."""
    return html.escape(str(s if s is not None else ""), quote=False)


async def _send_main_menu(message: Message) -> None:
    flows = _list_flows()
    lines = ["🛠 <b>Мини-конструктор</b>", "", "Выбери действие или флоу:", ""]
    if flows:
        for f in flows[:10]:
            star = "⭐" if f["is_published"] else "·"
            lines.append(f"{star} <b>{_esc(f['name'])}</b> — v{_esc(f.get('version', 0))}")
    else:
        lines.append("<i>нет флоу</i>")
    rows: list[list[tuple[str, str]]] = []
    for f in flows[:8]:
        rows.append([(f["name"][:32], f"{CB_PREFIX}open:{f['id']}")])
    rows.append([("➕ Новый флоу", f"{CB_PREFIX}new"), ("🔄 Обновить", f"{CB_PREFIX}root")])
    await message.answer("\n".join(lines), reply_markup=_kb(rows), parse_mode="HTML")


def _list_flows() -> list[dict[str, Any]]:
    sb = get_supabase()
    r = (
        sb.table("bot_flows")
        .select("id, name, version, is_published, updated_at, graph")
        .order("updated_at", desc=True)
        .limit(20)
        .execute()
    )
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
    pub = "опубликован ⭐" if flow.get("is_published") else "черновик"
    lines = [
        f"📋 <b>{_esc(flow.get('name'))}</b>",
        f"<i>v{_esc(flow.get('version', 0))} • {pub}</i>",
        f"Узлов: {len(nodes)}  ·  ❗ {summ['error']}  ⚠ {summ['warning']}  💡 {summ['hint']}",
        "",
        "<b>Блоки:</b>",
    ]
    for i, n in enumerate(nodes[:20], 1):
        params = n.get("params") or {}
        title = (
            params.get("text")
            or params.get("command")
            or params.get("variable")
            or params.get("pattern")
            or ""
        )
        title = str(title).replace("\n", " ")[:48]
        nxt = n.get("next")
        arrow = f" → <code>{_esc(nxt)}</code>" if nxt else ""
        lines.append(
            f"{i}. <code>{_esc(n.get('id'))}</code> "
            f"<i>{_esc(n.get('type'))}</i> {_esc(title)}{arrow}"
        )
    if len(nodes) > 20:
        lines.append(f"…ещё {len(nodes) - 20}")
    if issues:
        lines.append("")
        lines.append("<b>AI-проверка:</b>")
        for it in issues[:8]:
            emoji = LEVEL_EMOJI.get(it["level"], "•")
            lines.append(
                f"{emoji} <code>{_esc(it.get('node_id') or '-')}</code>: {_esc(it['message'])}"
            )
    return "\n".join(lines)


def _flow_kb(fid: str, published: bool) -> InlineKeyboardMarkup:
    rows: list[list[tuple[str, str]]] = [
        [
            ("➕ Сообщение", f"{CB_PREFIX}add:{fid}:send_message"),
            ("❓ Вопрос", f"{CB_PREFIX}add:{fid}:ask_question"),
        ],
        [
            ("🧠 AI-проверка", f"{CB_PREFIX}lint:{fid}"),
            ("👁 Превью", f"{CB_PREFIX}prev:{fid}"),
        ],
        [
            ("⭐ Опубликовать", f"{CB_PREFIX}pub:{fid}")
            if not published
            else ("⏸ Снять с публикации", f"{CB_PREFIX}unpub:{fid}")
        ],
        [("⬅ Назад", f"{CB_PREFIX}root")],
    ]
    return _kb(rows)


async def _safe_edit(cq: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None) -> None:
    """edit_text, который не падает если текст не изменился / сообщение слишком старое."""
    msg = cq.message
    if msg is None:
        return
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        log.warning("edit_text failed (%s), sending new message", e)
        with contextlib.suppress(Exception):
            await msg.answer(text, reply_markup=markup, parse_mode="HTML")


# ---- Reply-клавиатура владельца ----

ADMIN_KB_BUTTONS = [
    ["📋 Флоу", "🧠 AI-проверка"],
    ["🏷 Категории", "👗 Образы"],
    ["📊 Заявки", "🌐 Открыть веб-админку"],
    ["❌ Скрыть"],
]


def _admin_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in ADMIN_KB_BUTTONS],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери раздел или просто пиши…",
    )


async def _send_admin_keyboard(message: Message) -> None:
    web = settings.public_web_url.rstrip("/")
    text = (
        "🛠 <b>Админка Марины</b>\n\n"
        f'Веб: <a href="{web}/admin">{web}/admin</a>\n'
        f'Контент Марины: <a href="{web}/mama">{web}/mama</a>\n\n'
        "Внизу — быстрые кнопки. Команды:\n"
        "  /builder — мини-конструктор флоу\n"
        "  /admin — это меню\n"
        "  /hide — спрятать клавиатуру"
    )
    await message.answer(
        text,
        reply_markup=_admin_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


def make_router() -> Router:
    router = Router(name="mini_constructor")

    @router.message(Command("builder"))
    async def on_builder(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return  # тихо игнорируем не-владельцев
        await _send_main_menu(message)

    @router.message(Command(commands=["admin", "menu"]))
    async def on_admin(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return
        await _send_admin_keyboard(message)

    @router.message(Command("addbot"))
    async def on_addbot(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.answer(
                "Использование: <code>/addbot 123456:ABC-DEF...</code>\n\n"
                "Получи токен у @BotFather и пришли командой выше. "
                "Бот добавится в пул и заработает после рестарта контейнера.",
                parse_mode="HTML",
            )
            return
        token = parts[1].strip()
        if ":" not in token or len(token) < 30:
            await message.answer("Это не похоже на валидный токен бота.")
            return
        row = register_child_bot(
            token=token,
            owner_telegram_id=message.from_user.id if message.from_user else None,
            display_name=f"Bot by {message.from_user.id}" if message.from_user else None,
        )
        if row:
            await message.answer(
                f"✅ Бот зарегистрирован (id={row.get('id')}).\n"
                "Перезапусти контейнер чтобы он начал поллиться.",
                parse_mode="HTML",
            )
        else:
            await message.answer("Не удалось сохранить (см. логи).")

    @router.message(Command("hide"))
    async def on_hide(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return
        await message.answer(
            "Клавиатура спрятана. /admin — вернуть.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @router.message(
        F.text.in_(
            {
                "📋 Флоу",
                "🧠 AI-проверка",
                "🏷 Категории",
                "👗 Образы",
                "📊 Заявки",
                "🌐 Открыть веб-админку",
                "❌ Скрыть",
            }
        )
    )
    async def on_reply_btn(message: Message) -> None:
        if not _is_owner(message.from_user.id if message.from_user else None):
            return
        web = settings.public_web_url.rstrip("/")
        txt = message.text or ""
        if txt == "📋 Флоу":
            await _send_main_menu(message)
            return
        if txt == "🧠 AI-проверка":
            sb = get_supabase()
            r = (
                sb.table("bot_flows")
                .select("id, name, graph")
                .eq("is_published", True)
                .order("published_at", desc=True)
                .limit(1)
                .execute()
            )
            flow = (r.data or [None])[0]
            if not flow:
                await message.answer("Нет опубликованного флоу.")
                return
            issues = validator.validate_graph(flow.get("graph") or {})
            if not issues:
                await message.answer(
                    f"✅ Чисто (<b>{_esc(flow['name'])}</b>)",
                    parse_mode="HTML",
                )
                return
            lines = [f"<b>{_esc(flow['name'])}</b>", ""]
            for i in issues[:20]:
                e = LEVEL_EMOJI.get(i["level"], "·")
                lines.append(
                    f"{e} <code>{_esc(i.get('node_id') or '-')}</code> — {_esc(i['message'])}"
                )
            await message.answer(chr(10).join(lines), parse_mode="HTML")
            return
        if txt == "🏷 Категории":
            await message.answer(
                "🏷 <b>Категории</b>\n\n"
                f'Открой <a href="{web}/admin/categories">{web}/admin/categories</a> '
                "чтобы редактировать справочники (Пол, Цвета, Стили, Сезоны, "
                "Поводы, Фигура, Бюджет, Тип съёмки).",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return
        if txt == "👗 Образы":
            await message.answer(
                "👗 <b>Образы</b>\n\n"
                f'Каталог — в <a href="{web}/mama">контент-админке Марины</a>. '
                "Там можно загружать фото, ставить теги, публиковать.",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return
        if txt == "📊 Заявки":
            await message.answer(
                "📊 <b>Заявки и статистика</b>\n\n"
                f'• <a href="{web}/mama/bookings">{web}/mama/bookings</a>\n'
                f'• <a href="{web}/mama/stats">{web}/mama/stats</a>',
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return
        if txt == "🌐 Открыть веб-админку":
            await message.answer(
                "🌐 <b>Веб-админка</b>\n\n"
                f'• <a href="{web}/admin">{web}/admin</a> — флоу + конструктор\n'
                f'• <a href="{web}/admin/categories">{web}/admin/categories</a> — категории\n'
                f'• <a href="{web}/mama">{web}/mama</a> — образы / курсы / заявки',
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            return
        if txt == "❌ Скрыть":
            await message.answer(
                "ОК, спрятала. /admin — вернуть.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

    @router.callback_query(F.data.startswith(CB_PREFIX))
    async def on_cb(cq: CallbackQuery) -> None:
        if not _is_owner(cq.from_user.id if cq.from_user else None):
            await cq.answer("Доступ только владельцу", show_alert=True)
            return
        data = (cq.data or "")[len(CB_PREFIX) :]
        parts = data.split(":")
        action = parts[0]
        try:
            await _dispatch(cq, action, parts[1:])
        except Exception as e:
            log.exception("mini-constructor error")
            with contextlib.suppress(Exception):
                await cq.answer(f"Ошибка: {e}"[:190], show_alert=True)

    return router


async def _dispatch(cq: CallbackQuery, action: str, args: list[str]) -> None:
    msg = cq.message
    if action == "root":
        if msg:
            with contextlib.suppress(Exception):
                await msg.delete()
            await _send_main_menu(msg)
        await cq.answer()
        return
    if action == "new":
        sb = get_supabase()
        sb.table("bot_flows").insert(
            {
                "name": "Новый флоу (из бота)",
                "graph": {"nodes": [], "edges": []},
            }
        ).execute()
        await cq.answer("Создан")
        if msg:
            with contextlib.suppress(Exception):
                await msg.delete()
            await _send_main_menu(msg)
        return
    if action == "open":
        flow = _get_flow(args[0])
        if not flow:
            await cq.answer("Флоу не найден", show_alert=True)
            return
        await _safe_edit(cq, _format_flow(flow), _flow_kb(flow["id"], flow["is_published"]))
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
        lines = ["<b>AI-проверка</b>", ""]
        for i in issues[:25]:
            emoji = LEVEL_EMOJI.get(i["level"], "•")
            lines.append(
                f"{emoji} <code>{_esc(i.get('node_id') or '-')}</code> — {_esc(i['message'])}"
            )
        if msg:
            await msg.answer("\n".join(lines), parse_mode="HTML")
        await cq.answer()
        return
    if action == "pub":
        _save_flow(args[0], {"is_published": True, "published_at": "now()"})
        await cq.answer("Опубликовано")
        flow = _get_flow(args[0])
        if flow:
            await _safe_edit(cq, _format_flow(flow), _flow_kb(flow["id"], flow["is_published"]))
        return
    if action == "unpub":
        _save_flow(args[0], {"is_published": False})
        await cq.answer("Снято")
        flow = _get_flow(args[0])
        if flow:
            await _safe_edit(cq, _format_flow(flow), _flow_kb(flow["id"], flow["is_published"]))
        return
    if action == "prev":
        sb = get_supabase()
        sb.table("bot_preview_requests").insert(
            {
                "flow_id": args[0],
                "telegram_id": cq.from_user.id,
                "status": "pending",
            }
        ).execute()
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
            new_node = {
                "id": new_id,
                "type": "send_message",
                "params": {"text": "Новое сообщение"},
                "next": None,
            }
        else:
            new_node = {
                "id": new_id,
                "type": "ask_question",
                "params": {"text": "Новый вопрос?", "variable": "answer"},
                "next": None,
            }
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
            await _safe_edit(cq, _format_flow(flow), _flow_kb(flow["id"], flow["is_published"]))
        return
    await cq.answer()
