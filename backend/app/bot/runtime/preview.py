"""Send a one-shot preview of a draft flow to the bot owner.

The constructor's "Test" button calls
``POST /api/admin/flows/{id}/preview`` which dispatches this. The preview
uses the draft graph (not the published one) and writes to a temporary
session keyed by the owner's Telegram id, so it doesn't clobber whatever
state the real user has.
"""

from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot

from app.bot.runtime import registry, state
from app.bot.runtime.engine import ExecutionContext, _execute_from
from app.core.config import settings

log = logging.getLogger(__name__)


async def run_preview(*, bot: Bot, flow_id: str) -> tuple[bool, str]:
    """Returns ``(ok, message)`` describing what happened."""
    owner = settings.bot_owner_telegram_id
    if not owner:
        return False, "BOT_OWNER_TELEGRAM_ID not configured"
    flow = registry.flow_by_id(flow_id)
    if not flow:
        return False, "Flow not found"
    graph = flow.get("graph") or {}
    nodes = registry.index_nodes(graph)

    # Find the start command trigger.
    start_id: str | None = None
    for n in graph.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        if (
            n.get("type") == "command"
            and ((n.get("params") or {}).get("command") or "").lstrip("/") == "start"
        ):
            start_id = n.get("next") or n["id"]
            break
    if not start_id:
        return False, "Flow has no /start trigger"

    # Synthesise a session and user.
    tg_user = {
        "id": owner,
        "username": "preview",
        "first_name": "Preview",
        "last_name": "",
        "full_name": "Preview",
        "language_code": "ru",
        "is_premium": True,
    }
    session = state.Session(
        telegram_id=owner,
        flow_id=flow_id,
        current_node_id=None,
        vars={},
        awaiting_input=False,
    )
    ctx = ExecutionContext(
        chat_id=owner,
        session=session,
        tg_user=tg_user,
        flow_id=flow_id,
        graph=graph,
        nodes=nodes,
    )
    try:
        await bot.send_message(
            chat_id=owner, text="🧪 Превью флоу: " + str(flow.get("name") or flow_id)
        )
    except Exception as exc:
        return False, f"Can't message owner ({exc}). Owner must /start the bot once."

    await _execute_from(bot, ctx, start_id)
    # Save the preview session too so the owner can finish it interactively.
    state.save(session)
    return True, "Preview sent"


def default_flow_graph() -> dict[str, Any]:
    """A starter graph: outfit color quiz -> filter -> PDF.

    Inserted by the constructor's "Insert sample" button so Marina has
    something working right after applying migrations.
    """
    return {
        "nodes": [
            {
                "id": "trig_start",
                "type": "command",
                "params": {"command": "start"},
                "position": {"x": 40, "y": 40},
                "next": "welcome",
            },
            {
                "id": "welcome",
                "type": "send_message",
                "params": {
                    "text": (
                        "Привет, <b>{{user.first_name}}</b>! Я подберу образы для съёмки.\n"
                        "Готова ответить на пару вопросов?"
                    ),
                    "buttons": [
                        [{"text": "✨ Поехали", "next": "q_colors"}],
                        [{"text": "ℹ️ О съёмке", "next": "about"}],
                    ],
                },
                "position": {"x": 320, "y": 40},
                "next": None,
            },
            {
                "id": "about",
                "type": "send_message",
                "params": {
                    "text": "Я фотограф Marina. Сначала пройди мини-квиз — потом пришлю подборку и PDF.",
                    "buttons": [[{"text": "← Назад", "next": "welcome"}]],
                },
                "position": {"x": 320, "y": 240},
                "next": None,
            },
            {
                "id": "q_colors",
                "type": "ask_question",
                "params": {
                    "text": "Какой палитры образ хочешь?",
                    "variable": "color",
                    "options": [
                        {"text": "Чёрный", "value": "black"},
                        {"text": "Белый", "value": "white"},
                        {"text": "Бежевый", "value": "beige"},
                        {"text": "Серый", "value": "gray"},
                    ],
                },
                "position": {"x": 620, "y": 40},
                "next": "q_style",
            },
            {
                "id": "q_style",
                "type": "ask_question",
                "params": {
                    "text": "Ближе по настроению?",
                    "variable": "style",
                    "options": [
                        {"text": "Романтика", "value": "romantic"},
                        {"text": "Деловая", "value": "business"},
                        {"text": "Кэжуал", "value": "casual"},
                    ],
                },
                "position": {"x": 900, "y": 40},
                "next": "q_shoot",
            },
            {
                "id": "q_shoot",
                "type": "ask_question",
                "params": {
                    "text": "Где будем снимать?",
                    "variable": "shoot",
                    "options": [
                        {"text": "Студия", "value": "studio"},
                        {"text": "Улица", "value": "street"},
                        {"text": "Людное место", "value": "crowd"},
                    ],
                },
                "position": {"x": 1180, "y": 40},
                "next": "typing_thinking",
            },
            {
                "id": "typing_thinking",
                "type": "typing",
                "params": {"seconds": 2.0},
                "position": {"x": 1460, "y": 40},
                "next": "fetch",
            },
            {
                "id": "fetch",
                "type": "db_query",
                "params": {
                    "table": "outfits",
                    "select": "*, outfit_images(*)",
                    "filters": [
                        {"column": "is_published", "op": "is_published", "value": True},
                        {"column": "colors", "op": "ilike", "value": "{{vars.color}}"},
                        {"column": "styles", "op": "ilike", "value": "{{vars.style}}"},
                        {"column": "shoot_types", "op": "ilike", "value": "{{vars.shoot}}"},
                    ],
                    "save_to": "matched_outfits",
                    "limit": 8,
                    "order_by": "sort_order",
                },
                "position": {"x": 1460, "y": 200},
                "next": "branch_empty",
            },
            {
                "id": "branch_empty",
                "type": "branch",
                "params": {
                    "variable": "{{vars.matched_outfits_count}}",
                    "op": "gt",
                    "value": 0,
                    "true_next": "intro_results",
                    "false_next": "no_results",
                },
                "position": {"x": 1460, "y": 360},
            },
            {
                "id": "no_results",
                "type": "send_message",
                "params": {
                    "text": "Под твои параметры ничего не нашлось. Попробуй ещё раз: /start",
                },
                "position": {"x": 1180, "y": 520},
                "next": "end",
            },
            {
                "id": "intro_results",
                "type": "send_message",
                "params": {
                    "text": "Нашла <b>{{vars.matched_outfits_count}}</b> образов. Отправляю подборку…",
                },
                "position": {"x": 1740, "y": 360},
                "next": "send_outfits",
            },
            {
                "id": "send_outfits",
                "type": "send_album",
                "params": {
                    "items_var": "matched_outfits",
                    "caption_template": "{{outfit.title}}",
                },
                "position": {"x": 1740, "y": 520},
                "next": "make_pdf",
            },
            {
                "id": "make_pdf",
                "type": "generate_pdf",
                "params": {
                    "items_var": "matched_outfits",
                    "filename": "podbor_obrazov.pdf",
                    "caption": "📄 PDF с подборкой — сохраняй и приноси на съёмку!",
                    "save_to": "pdf",
                    "send_now": True,
                },
                "position": {"x": 1740, "y": 700},
                "next": "after_menu",
            },
            {
                "id": "after_menu",
                "type": "send_message",
                "params": {
                    "text": "Что дальше?",
                    "buttons": [
                        [{"text": "🔁 Подобрать ещё раз", "next": "trig_start"}],
                        [{"text": "📸 Записаться на съёмку", "next": "booking_phone"}],
                    ],
                },
                "position": {"x": 1460, "y": 860},
                "next": None,
            },
            {
                "id": "booking_phone",
                "type": "ask_question",
                "params": {
                    "text": "Оставь телефон — мама свяжется. Можно просто написать @username в Telegram.",
                    "variable": "phone",
                },
                "position": {"x": 1740, "y": 1020},
                "next": "booking_save",
            },
            {
                "id": "booking_save",
                "type": "db_insert",
                "params": {
                    "table": "bookings",
                    "fields": {
                        "phone": "{{vars.phone}}",
                        "shoot_type": "{{vars.shoot}}",
                        "full_name": "{{user.full_name}}",
                        "payload": {
                            "color": "{{vars.color}}",
                            "style": "{{vars.style}}",
                            "shoot": "{{vars.shoot}}",
                        },
                    },
                },
                "position": {"x": 1740, "y": 1180},
                "next": "booking_thanks",
            },
            {
                "id": "booking_thanks",
                "type": "send_message",
                "params": {
                    "text": "Спасибо! Мама уже видит заявку и скоро напишет 🌷",
                },
                "position": {"x": 1740, "y": 1340},
                "next": "end",
            },
            {
                "id": "end",
                "type": "end",
                "params": {},
                "position": {"x": 1460, "y": 1340},
            },
        ],
        "edges": [
            {"id": "e1", "source": "trig_start", "target": "welcome"},
            {"id": "e2", "source": "welcome", "target": "q_colors", "label": "Поехали"},
            {"id": "e3", "source": "welcome", "target": "about", "label": "О съёмке"},
            {"id": "e4", "source": "about", "target": "welcome"},
            {"id": "e5", "source": "q_colors", "target": "q_style"},
            {"id": "e6", "source": "q_style", "target": "q_shoot"},
            {"id": "e7", "source": "q_shoot", "target": "typing_thinking"},
            {"id": "e8", "source": "typing_thinking", "target": "fetch"},
            {"id": "e9", "source": "fetch", "target": "branch_empty"},
            {"id": "e10", "source": "branch_empty", "target": "intro_results", "label": "found"},
            {"id": "e11", "source": "branch_empty", "target": "no_results", "label": "empty"},
            {"id": "e12", "source": "intro_results", "target": "send_outfits"},
            {"id": "e13", "source": "send_outfits", "target": "make_pdf"},
            {"id": "e14", "source": "make_pdf", "target": "after_menu"},
            {"id": "e15", "source": "after_menu", "target": "trig_start", "label": "Ещё"},
            {"id": "e16", "source": "after_menu", "target": "booking_phone", "label": "Записаться"},
            {"id": "e17", "source": "booking_phone", "target": "booking_save"},
            {"id": "e18", "source": "booking_save", "target": "booking_thanks"},
            {"id": "e19", "source": "booking_thanks", "target": "end"},
            {"id": "e20", "source": "no_results", "target": "end"},
        ],
    }
