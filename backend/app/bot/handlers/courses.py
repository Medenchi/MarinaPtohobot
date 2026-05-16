"""Handles /pint deep-link — lists free courses and opens files."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import course_detail_keyboard, courses_list_keyboard
from app.core.supabase import get_supabase

router = Router(name="courses")
log = logging.getLogger(__name__)


async def show_courses(message: Message) -> None:
    try:
        sb = get_supabase()
        resp = (
            sb.table("courses")
            .select("id, title, short_description")
            .eq("is_published", True)
            .order("sort_order")
            .execute()
        )
        courses = resp.data or []
    except Exception:
        log.exception("Failed to fetch courses")
        await message.answer("Не удалось загрузить курсы. Попробуй позже.")
        return

    if not courses:
        await message.answer("Пока нет доступных материалов. Загляни позже!")
        return

    text = "Бесплатные материалы от Марины:\n\nВыбери интересующий курс:"
    kb = courses_list_keyboard(courses)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("course:"))
async def on_course_select(callback: CallbackQuery) -> None:
    course_id_str = (callback.data or "").split(":", 1)[1]
    try:
        course_id = int(course_id_str)
    except ValueError:
        await callback.answer("Неверный курс", show_alert=True)
        return

    try:
        sb = get_supabase()
        course_resp = (
            sb.table("courses")
            .select("id, title, description")
            .eq("id", course_id)
            .single()
            .execute()
        )
        course = course_resp.data
        files_resp = (
            sb.table("course_files")
            .select("id, title, storage_path, mime_type")
            .eq("course_id", course_id)
            .order("sort_order")
            .execute()
        )
        files = files_resp.data or []
    except Exception:
        log.exception("Failed to fetch course detail")
        await callback.answer("Ошибка загрузки", show_alert=True)
        return

    if not course:
        await callback.answer("Курс не найден", show_alert=True)
        return

    desc = course.get("description") or ""
    text = f"<b>{course['title']}</b>\n\n{desc}" if desc else f"<b>{course['title']}</b>"

    if not files:
        text += "\n\nМатериалы скоро появятся."

    kb = course_detail_keyboard(course_id, files)

    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "courses:back")
async def on_courses_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await show_courses(callback.message)
