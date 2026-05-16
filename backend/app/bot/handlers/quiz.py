"""FSM-based outfit quiz — asks 7 questions, saves to Supabase,
then opens the WebApp with results."""

from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import (
    quiz_multi_select,
    quiz_single_select,
    results_keyboard,
)
from app.bot.states.quiz import OutfitQuiz
from app.core.supabase import get_supabase

router = Router(name="quiz")
log = logging.getLogger(__name__)

# ---- Option catalogues (value, label) ----

COLOR_OPTIONS = [
    ("black", "Чёрный"),
    ("white", "Белый"),
    ("beige", "Бежевый"),
    ("brown", "Коричневый"),
    ("gray", "Серый"),
    ("red", "Красный"),
    ("blue", "Синий"),
    ("green", "Зелёный"),
    ("pink", "Розовый"),
    ("purple", "Фиолетовый"),
]

STYLE_OPTIONS = [
    ("casual", "Кэжуал"),
    ("romantic", "Романтичный"),
    ("business", "Деловой"),
    ("sport", "Спортивный"),
    ("street", "Уличный"),
]

SEASON_OPTIONS = [
    ("winter", "Зима"),
    ("spring", "Весна"),
    ("summer", "Лето"),
    ("autumn", "Осень"),
    ("all", "Любой сезон"),
]

OCCASION_OPTIONS = [
    ("photoshoot", "Фотосессия"),
    ("everyday", "Повседневный"),
    ("party", "Праздник / вечеринка"),
    ("date", "Свидание"),
]

BODY_TYPE_OPTIONS = [
    ("hourglass", "Песочные часы"),
    ("pear", "Груша"),
    ("rectangle", "Прямоугольник"),
    ("apple", "Яблоко"),
    ("athletic", "Атлетичная"),
    ("skip", "Пропустить"),
]

BUDGET_OPTIONS = [
    ("low", "До 5 000 ₽"),
    ("medium", "5 000–15 000 ₽"),
    ("high", "15 000 ₽+"),
    ("any", "Любой"),
]

SHOOT_TYPE_OPTIONS = [
    ("studio", "Студия"),
    ("street", "На улице"),
    ("crowd", "Людное место / город"),
    ("nature", "Природа"),
]

STEP_PROMPTS: dict[str, str] = {
    "colors": "Какие цвета тебе нравятся? Выбери один или несколько:",
    "style": "Какой стиль тебе ближе?",
    "season": "Для какого сезона подбираем образ?",
    "occasion": "По какому поводу?",
    "body_type": "Тип фигуры (необязательно):",
    "budget": "Бюджет на образ?",
    "shoot_type": "Где планируется съёмка?",
}


async def begin_quiz(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OutfitQuiz.colors)
    await state.update_data(colors=set(), style=set())
    kb = quiz_multi_select(COLOR_OPTIONS, set(), "q_color")
    await message.answer(STEP_PROMPTS["colors"], reply_markup=kb)


# ---- Colors (multi-select) ----


@router.callback_query(OutfitQuiz.colors, F.data.startswith("q_color:"))
async def on_color(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    data = await state.get_data()
    selected: set[str] = data.get("colors", set())

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы один цвет", show_alert=True)
            return
        await state.update_data(colors=selected)
        await state.set_state(OutfitQuiz.style)
        kb = quiz_multi_select(STYLE_OPTIONS, set(), "q_style")
        await _edit_or_answer(callback, STEP_PROMPTS["style"], kb)
        return

    if value in selected:
        selected.discard(value)
    else:
        selected.add(value)
    await state.update_data(colors=selected)
    kb = quiz_multi_select(COLOR_OPTIONS, selected, "q_color")
    await _edit_or_answer(callback, STEP_PROMPTS["colors"], kb)


# ---- Style (multi-select) ----


@router.callback_query(OutfitQuiz.style, F.data.startswith("q_style:"))
async def on_style(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    data = await state.get_data()
    selected: set[str] = data.get("style", set())

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы один стиль", show_alert=True)
            return
        await state.update_data(style=selected)
        await state.set_state(OutfitQuiz.season)
        kb = quiz_single_select(SEASON_OPTIONS, "q_season")
        await _edit_or_answer(callback, STEP_PROMPTS["season"], kb)
        return

    if value in selected:
        selected.discard(value)
    else:
        selected.add(value)
    await state.update_data(style=selected)
    kb = quiz_multi_select(STYLE_OPTIONS, selected, "q_style")
    await _edit_or_answer(callback, STEP_PROMPTS["style"], kb)


# ---- Season (single) ----


@router.callback_query(OutfitQuiz.season, F.data.startswith("q_season:"))
async def on_season(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    await state.update_data(season=value)
    await state.set_state(OutfitQuiz.occasion)
    kb = quiz_single_select(OCCASION_OPTIONS, "q_occasion")
    await _edit_or_answer(callback, STEP_PROMPTS["occasion"], kb)


# ---- Occasion (single) ----


@router.callback_query(OutfitQuiz.occasion, F.data.startswith("q_occasion:"))
async def on_occasion(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    await state.update_data(occasion=value)
    await state.set_state(OutfitQuiz.body_type)
    kb = quiz_single_select(BODY_TYPE_OPTIONS, "q_body")
    await _edit_or_answer(callback, STEP_PROMPTS["body_type"], kb)


# ---- Body type (single, optional) ----


@router.callback_query(OutfitQuiz.body_type, F.data.startswith("q_body:"))
async def on_body(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    if value != "skip":
        await state.update_data(body_type=value)
    await state.set_state(OutfitQuiz.budget)
    kb = quiz_single_select(BUDGET_OPTIONS, "q_budget")
    await _edit_or_answer(callback, STEP_PROMPTS["budget"], kb)


# ---- Budget (single) ----


@router.callback_query(OutfitQuiz.budget, F.data.startswith("q_budget:"))
async def on_budget(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    await state.update_data(budget=value)
    await state.set_state(OutfitQuiz.shoot_type)
    kb = quiz_single_select(SHOOT_TYPE_OPTIONS, "q_shoot")
    await _edit_or_answer(callback, STEP_PROMPTS["shoot_type"], kb)


# ---- Shoot type (single) → finish ----


@router.callback_query(OutfitQuiz.shoot_type, F.data.startswith("q_shoot:"))
async def on_shoot(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split(":", 1)[1]
    await state.update_data(shoot_type=value)
    data = await state.get_data()
    await state.clear()
    await _save_and_show_results(callback, data)


# ---- Restart ----


@router.callback_query(F.data == "quiz:restart")
async def on_restart(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return
    await begin_quiz(callback.message, state)
    await callback.answer()


# ---- Helpers ----


def _answers_dict(data: dict) -> dict:
    """Normalize FSM data into a clean JSON-friendly dict."""

    def _lst(v: object) -> list[str]:
        if isinstance(v, set):
            return sorted(v)
        if isinstance(v, str):
            return [v] if v else []
        return []

    return {
        "colors": _lst(data.get("colors")),
        "styles": _lst(data.get("style")),
        "seasons": _lst(data.get("season")),
        "occasions": _lst(data.get("occasion")),
        "body_types": _lst(data.get("body_type")),
        "budgets": _lst(data.get("budget")),
        "shoot_types": _lst(data.get("shoot_type")),
    }


async def _save_and_show_results(callback: CallbackQuery, data: dict) -> None:
    answers = _answers_dict(data)
    session_id = str(uuid.uuid4())
    user = callback.from_user

    try:
        sb = get_supabase()
        sb.table("quiz_sessions").insert(
            {
                "id": session_id,
                "telegram_user_id": user.id if user else None,
                "telegram_username": (user.username or "") if user else "",
                "answers": answers,
            }
        ).execute()
    except Exception:
        log.exception("Failed to save quiz session to Supabase")
        if callback.message:
            await callback.message.answer(
                "Произошла ошибка при сохранении. Попробуй ещё раз /start"
            )
        await callback.answer()
        return

    text = (
        "Готово! Я подобрал образы по твоим ответам.\n\n"
        "Нажми кнопку ниже, чтобы открыть результаты — "
        "там можно листать образы и скачать PDF-подборку."
    )
    kb = results_keyboard(session_id)
    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


async def _edit_or_answer(
    callback: CallbackQuery,
    text: str,
    markup: object,
) -> None:
    await callback.answer()
    if callback.message is None:
        return
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
