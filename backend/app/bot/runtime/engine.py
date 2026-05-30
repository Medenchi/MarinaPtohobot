"""Flow execution engine — drives the bot from a JSON graph.

The engine is the single aiogram catch-all. On each incoming update it:

1. Loads / creates the user's :class:`Session` (Supabase ``bot_sessions``).
2. Resolves which node to execute (trigger lookup, awaiting-input answer,
   callback target).
3. Walks forward through the graph executing blocks until it hits a block
   that pauses (``ask_question``) or ``end``.
4. Persists the session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message, PollAnswer

from app.bot.runtime import blocks, registry, state
from app.bot.runtime.keyboards import parse_cb
from app.bot.runtime.vars import build_context

log = logging.getLogger(__name__)

MAX_STEPS = 50  # safety net against infinite loops in user-authored graphs


@dataclass(slots=True)
class ExecutionContext:
    """Per-update execution scratch space."""

    chat_id: int
    session: state.Session
    tg_user: dict[str, Any]
    flow_id: str | None
    graph: dict[str, Any]
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def vars(self) -> dict[str, Any]:
        return self.session.vars

    @property
    def template_ctx(self) -> dict[str, Any]:
        return build_context(vars_=self.vars, user=self.tg_user)


async def _execute_from(bot: Bot, ctx: ExecutionContext, start_node_id: str) -> None:
    node_id: str | None = start_node_id
    steps = 0
    while node_id and steps < MAX_STEPS:
        node = ctx.nodes.get(node_id)
        if not node:
            log.warning("Node %s not found in flow %s", node_id, ctx.flow_id)
            break
        ctx.session.current_node_id = node_id
        ntype = node.get("type")
        if ntype in blocks.TRIGGER_TYPES:
            # Triggers don't execute; just walk to their `next`.
            node_id = node.get("next")
            steps += 1
            continue
        fn = blocks.BLOCKS.get(ntype or "")
        if fn is None:
            log.warning("Unknown block type %r at node %s", ntype, node_id)
            break
        try:
            node_id = await fn(bot, ctx, node)
        except Exception:
            log.exception("Block %s (%s) crashed", node_id, ntype)
            state.log_event(
                telegram_id=ctx.tg_user.get("id"),
                telegram_username=ctx.tg_user.get("username"),
                flow_id=ctx.flow_id,
                node_id=node_id,
                event_type="block_error",
                payload={"block_type": ntype},
            )
            break
        if ctx.session.awaiting_input:
            # ask_question called — pause here. current_node_id was set above.
            return
        steps += 1
    if not node_id:
        ctx.session.awaiting_input = False
        ctx.session.current_node_id = None


async def _make_ctx(bot: Bot, chat_id: int, tg_user_obj: Any) -> ExecutionContext | None:
    flow = registry.published_flow()
    if not flow:
        await bot.send_message(
            chat_id=chat_id,
            text="Бот пока не настроен. Загляни позже.",
        )
        return None
    graph = flow.get("graph") or {}
    session = state.load(tg_user_obj.id)
    # Если в сессии остался id уже удалённого/снятого с публикации флоу,
    # сбросим прогресс — иначе FK на bot_flows упадёт при save().
    if session.flow_id and session.flow_id != flow["id"]:
        log.info(
            "Migrating tg=%s from old flow=%s to current=%s",
            session.telegram_id,
            session.flow_id,
            flow["id"],
        )
        session.current_node_id = None
        session.awaiting_input = False
    session.flow_id = flow["id"]
    return ExecutionContext(
        chat_id=chat_id,
        session=session,
        tg_user=state.user_to_vars(tg_user_obj),
        flow_id=flow["id"],
        graph=graph,
        nodes=registry.index_nodes(graph),
    )


def make_router() -> Router:
    router = Router(name="flow_runtime")

    @router.message(CommandStart(deep_link=True))
    @router.message(CommandStart())
    @router.message(Command(commands=["help", "menu", "reset", "stop"]))
    async def on_command(message: Message, command: CommandObject = None) -> None:
        # Deep-link payload: /start ref_pin_42 → command.args = "ref_pin_42"
        deeplink = command.args if command and command.args else None
        await _handle_message(
            message,
            command_hint=_extract_command(message.text),
            deeplink=deeplink,
        )

    @router.message()
    async def on_any_message(message: Message) -> None:
        await _handle_message(message, command_hint=_extract_command(message.text), deeplink=None)

    @router.callback_query()
    async def on_callback(cq: CallbackQuery) -> None:
        await _handle_callback(cq)

    @router.poll_answer()
    async def on_poll_answer(answer: PollAnswer) -> None:
        await _handle_poll_answer(answer)

    return router


async def _handle_poll_answer(answer: PollAnswer) -> None:
    """Обработка голосов в Telegram-опросах из блока ask_poll."""
    if not answer.user or not answer.bot:
        return
    bot = answer.bot
    tg_user = answer.user
    state.upsert_bot_user(tg_user)
    # Грузим сессию пользователя напрямую (poll_answer не приходит с chat)
    session = state.load(tg_user.id)
    poll_map = session.vars.get("_pending_polls") or {}
    info = poll_map.get(answer.poll_id)
    if not info:
        log.debug("poll_answer без pending poll %s", answer.poll_id)
        return
    options = info.get("options") or []
    values = info.get("values") or options  # fallback на old behavior (text==value)
    chosen = [values[i] for i in (answer.option_ids or []) if 0 <= i < len(values)]
    if info.get("multiple"):
        session.vars[info["variable"]] = chosen
    else:
        session.vars[info["variable"]] = chosen[0] if chosen else ""
    # снимаем pending
    del poll_map[answer.poll_id]
    session.vars["_pending_polls"] = poll_map
    # Восстанавливаем chat_id из сохранённого
    chat_id = info.get("chat_id") or tg_user.id
    # Идём в next
    flow = registry.published_flow()
    if not flow:
        state.save(session)
        return
    graph = flow.get("graph") or {}
    nodes = registry.index_nodes(graph)
    node = nodes.get(info["node_id"])
    next_id = node.get("next") if node else None
    session.awaiting_input = False
    session.flow_id = flow["id"]
    if next_id:
        ctx = ExecutionContext(
            chat_id=chat_id,
            session=session,
            tg_user=state.user_to_vars(tg_user),
            flow_id=flow["id"],
            graph=graph,
            nodes=nodes,
        )
        await _execute_from(bot, ctx, next_id)
    state.save(session)


def _extract_command(text: str | None) -> str | None:
    if not text or not text.startswith("/"):
        return None
    head = text.split()[0]
    cmd = head[1:].split("@", 1)[0]
    return cmd or None


async def _handle_message(
    message: Message,
    *,
    command_hint: str | None,
    deeplink: str | None = None,
) -> None:
    if not message.from_user or not message.chat:
        return
    bot = message.bot
    if bot is None:
        return
    state.upsert_bot_user(message.from_user)
    ctx = await _make_ctx(bot, message.chat.id, message.from_user)
    if ctx is None:
        return

    target_node_id: str | None = None

    # 1) Commands always (re)start a flow if a matching trigger exists.
    if command_hint:
        trig = registry.find_trigger(ctx.graph, command=command_hint)
        if trig:
            target_node_id = trig.get("next") or trig["id"]
            ctx.session.awaiting_input = False
            # Reset vars on /start unless the trigger explicitly opts out.
            if command_hint == "start" and not (trig.get("params") or {}).get("keep_vars"):
                ctx.session.vars = {}
                ctx = ExecutionContext(
                    chat_id=ctx.chat_id,
                    session=ctx.session,
                    tg_user=ctx.tg_user,
                    flow_id=ctx.flow_id,
                    graph=ctx.graph,
                    nodes=ctx.nodes,
                )
            # Если в /start был payload (deep-link) — пишем его в vars и логируем
            if deeplink:
                ctx.vars["ref"] = deeplink
                ctx.vars["deeplink"] = deeplink
                state.log_event(
                    telegram_id=ctx.tg_user.get("id"),
                    telegram_username=ctx.tg_user.get("username"),
                    flow_id=ctx.flow_id,
                    node_id=target_node_id,
                    event_type="deeplink",
                    payload={"ref": deeplink},
                )
                import contextlib
                with contextlib.suppress(Exception):
                    state.get_supabase().rpc("increment_post_clicks", {"p_code": deeplink}).execute()

    # 2) Mid-question answer: capture text and resume.
    if target_node_id is None and ctx.session.awaiting_input and ctx.session.current_node_id:
        current = ctx.nodes.get(ctx.session.current_node_id)
        if current and current.get("type") == "ask_question":
            params = current.get("params") or {}
            var = params.get("variable")
            if var:
                ctx.vars[str(var)] = message.text or ""
            ctx.session.awaiting_input = False
            target_node_id = current.get("next")

    # 3) Free-text trigger fallback.
    if target_node_id is None and message.text:
        trig = registry.find_trigger(ctx.graph, text=message.text)
        if trig:
            target_node_id = trig.get("next") or trig["id"]

    state.log_event(
        telegram_id=ctx.tg_user.get("id"),
        telegram_username=ctx.tg_user.get("username"),
        flow_id=ctx.flow_id,
        node_id=target_node_id,
        event_type="message",
        payload={"text": (message.text or "")[:200]},
    )

    if target_node_id is None:
        # No-op — nothing matched. Keep the session as-is.
        state.save(ctx.session)
        return

    await _execute_from(bot, ctx, target_node_id)
    state.save(ctx.session)


async def _handle_gallery_callback(cq: CallbackQuery, raw_data: str) -> None:
    """Обработка кнопок ◀/▶/like/skip/done в show_outfits_gallery.

    Формат: gal:<node_id>:<action>
    """
    from app.bot.runtime._gallery_blocks import _send_gallery_card

    if not cq.from_user or not cq.message or not cq.message.chat:
        return
    bot = cq.bot
    if bot is None:
        return
    parts = raw_data.split(":", 2)
    if len(parts) < 3:
        await cq.answer()
        return
    _, node_id, action = parts

    state.upsert_bot_user(cq.from_user)
    ctx = await _make_ctx(bot, cq.message.chat.id, cq.from_user)
    if ctx is None:
        await cq.answer()
        return
    node = ctx.nodes.get(node_id)
    if not node:
        await cq.answer("Узел не найден", show_alert=True)
        return

    p = node.get("params") or {}
    items_key = p.get("items_var") or "matched_outfits"
    items = ctx.vars.get(items_key) or []
    if not isinstance(items, list) or not items:
        await cq.answer("Образы кончились")
        return

    idx_var = f"_gallery_idx_{node_id}"
    cur_idx = int(ctx.vars.get(idx_var) or 0)
    total = len(items)
    liked_var = p.get("liked_var") or "liked_ids"
    disliked_var = p.get("disliked_var") or "disliked_ids"
    msg_id = cq.message.message_id

    if action == "prev":
        new_idx = (cur_idx - 1) % total
        ctx.vars[idx_var] = new_idx
        await _send_gallery_card(bot, ctx, node, items, new_idx, edit_message_id=msg_id)
        await cq.answer()
    elif action == "next":
        new_idx = (cur_idx + 1) % total
        ctx.vars[idx_var] = new_idx
        await _send_gallery_card(bot, ctx, node, items, new_idx, edit_message_id=msg_id)
        await cq.answer()
    elif action in ("like", "skip"):
        cur_item = items[cur_idx]
        oid = cur_item.get("id")
        arr = ctx.vars.setdefault(liked_var if action == "like" else disliked_var, [])
        try:
            oid_int = int(oid)
        except (TypeError, ValueError):
            oid_int = oid
        if oid_int not in arr:
            arr.append(oid_int)
        await cq.answer("👍 запомнила!" if action == "like" else "ок, мимо")
        # Сразу к следующему
        new_idx = (cur_idx + 1) % total
        ctx.vars[idx_var] = new_idx
        await _send_gallery_card(bot, ctx, node, items, new_idx, edit_message_id=msg_id)
    elif action == "done":
        await cq.answer("Собираю PDF…")
        next_id = node.get("next")
        if next_id:
            await _execute_from(bot, ctx, next_id)
    else:
        await cq.answer()
    state.save(ctx.session)


async def _handle_callback(cq: CallbackQuery) -> None:
    if not cq.from_user or not cq.message or not cq.message.chat:
        return
    bot = cq.bot
    if bot is None:
        return
    raw_data = cq.data or ""

    # ====== Перехват: callback галереи (gal:<node_id>:action) ======
    if raw_data.startswith("gal:"):
        await _handle_gallery_callback(cq, raw_data)
        return

    parsed = parse_cb(raw_data)
    if parsed is None:
        await cq.answer()
        return
    target_node_id, value = parsed
    state.upsert_bot_user(cq.from_user)
    ctx = await _make_ctx(bot, cq.message.chat.id, cq.from_user)
    if ctx is None:
        await cq.answer()
        return

    # Special-case: голосование за образ (callback like:<id> / skip:<id>).
    # Не уходим в новый узел — просто пишем в vars.liked_ids / disliked_ids,
    # отвечаем "сохранил" и выходим. Кнопка «Готово» отправит callback
    # n:<next_node>|done — тот обрабатывается стандартно.
    # Рейтинг: callback "rate:<var_name>:<value>" пишет в vars[var_name]
    if isinstance(value, str) and value.startswith("rate:"):
        _, var_name, rating_value = [*value.split(":", 2), "", ""][:3]
        if var_name:
            try:
                ctx.vars[var_name] = int(rating_value)
            except (TypeError, ValueError):
                ctx.vars[var_name] = rating_value
        await cq.answer(f"Спасибо за {rating_value}⭐!")
        if target_node_id:
            await _execute_from(bot, ctx, target_node_id)
        state.save(ctx.session)
        return

    if isinstance(value, str) and (value.startswith("like:") or value.startswith("skip:")):
        kind, _, oid = value.partition(":")
        node = ctx.nodes.get(target_node_id) if target_node_id else None
        params = (node.get("params") if node else {}) or {}
        liked_var = params.get("liked_var") or "liked_ids"
        disliked_var = params.get("disliked_var") or "disliked_ids"
        try:
            oid_int = int(oid)
        except (TypeError, ValueError):
            oid_int = oid
        if kind == "like":
            arr = ctx.vars.setdefault(liked_var, [])
            if oid_int not in arr:
                arr.append(oid_int)
            await cq.answer("👍 запомнила!")
        else:
            arr = ctx.vars.setdefault(disliked_var, [])
            if oid_int not in arr:
                arr.append(oid_int)
            await cq.answer("ок, пропускаю")
        state.save(ctx.session)
        return

    # If the user clicked an ask_question option, record it.
    if ctx.session.awaiting_input and ctx.session.current_node_id:
        current = ctx.nodes.get(ctx.session.current_node_id)
        if current and current.get("type") == "ask_question":
            var = (current.get("params") or {}).get("variable")
            if var:
                ctx.vars[str(var)] = value if value is not None else (cq.data or "")
            ctx.session.awaiting_input = False
            # If the button's target *is* the question itself (the answer-recording
            # convention used by ask_question), advance to its real `next`.
            if target_node_id == current["id"]:
                target_node_id = current.get("next") or ""

    state.log_event(
        telegram_id=ctx.tg_user.get("id"),
        telegram_username=ctx.tg_user.get("username"),
        flow_id=ctx.flow_id,
        node_id=target_node_id,
        event_type="callback",
        payload={"value": value, "raw": cq.data},
    )

    await cq.answer()
    if target_node_id:
        await _execute_from(bot, ctx, target_node_id)
    state.save(ctx.session)
