"""Handles /start and deep-link dispatching."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import start_keyboard
from app.core.supabase import get_supabase

router = Router(name="start")
log = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Привет! Я бот Марины — фотографа из Москвы.\n\n"
    "Могу подобрать тебе образ для фотосессии "
    "или поделиться бесплатными материалами."
)


async def _upsert_user(msg: Message) -> None:
    user = msg.from_user
    if user is None:
        return
    try:
        sb = get_supabase()
        sb.table("bot_users").upsert(
            {
                "telegram_id": user.id,
                "username": user.username or "",
                "full_name": user.full_name or "",
                "is_premium": bool(user.is_premium),
                "last_seen_at": "now()",
            },
            on_conflict="telegram_id",
        ).execute()
    except Exception:
        log.debug("upsert_user failed (non-critical)", exc_info=True)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, state: FSMContext) -> None:
    await _upsert_user(message)
    args = message.text or ""
    payload = args.split(maxsplit=1)[1] if " " in args else ""
    payload = payload.strip().lower()

    if payload.startswith("obraz"):
        from app.bot.handlers.quiz import begin_quiz

        await begin_quiz(message, state)
    elif payload.startswith("pint"):
        from app.bot.handlers.courses import show_courses

        await show_courses(message)
    else:
        await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _upsert_user(message)
    await message.answer(WELCOME_TEXT, reply_markup=start_keyboard())


@router.callback_query(F.data == "start:obraz")
async def cb_start_obraz(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return
    from app.bot.handlers.quiz import begin_quiz

    await begin_quiz(callback.message, state)
    await callback.answer()


@router.callback_query(F.data == "start:pint")
async def cb_start_pint(callback: CallbackQuery) -> None:
    if callback.message is None:
        return
    from app.bot.handlers.courses import show_courses

    await show_courses(callback.message)
    await callback.answer()
