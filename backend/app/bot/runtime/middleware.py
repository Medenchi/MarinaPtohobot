"""Bot session middleware.

Перехватывает все исходящие API-вызовы send_message / send_photo / send_*
и сохраняет ``message_id`` в текущую сессию пользователя — чтобы блок
``delete_last_message`` мог их удалить.

Хранилище message_id'ов — в RAM (process-local), потому что в общем
случае flow исполняется в одном процессе. Также параллельно пишем
в session.bot_message_ids (persist в Supabase) на случай рестарта.
"""

from __future__ import annotations

import logging
from collections import defaultdict

log = logging.getLogger(__name__)


# chat_id → список message_id, что бот отправил
_RECENT: dict[int, list[int]] = defaultdict(list)
_MAX = 50  # держим в RAM не больше 50 последних на чат


def remember(chat_id: int, message_id: int) -> None:
    arr = _RECENT[chat_id]
    arr.append(message_id)
    if len(arr) > _MAX:
        del arr[: len(arr) - _MAX]


def pop_last(chat_id: int, n: int = 1) -> list[int]:
    arr = _RECENT[chat_id]
    out = list(arr[-n:])
    if n >= len(arr):
        arr.clear()
    else:
        del arr[-n:]
    return out


def get_recent(chat_id: int) -> list[int]:
    return list(_RECENT.get(chat_id, []))


def clear(chat_id: int) -> None:
    _RECENT[chat_id] = []


class CollectMessageIdsMiddleware:
    """Aiogram session middleware: после каждого send_* API-вызова
    запоминаем message_id из ответа.
    """

    async def __call__(self, make_request, bot, method):
        result = await make_request(bot, method)
        # Большинство send_* возвращают Message с message_id и chat.id
        try:
            chat = getattr(result, "chat", None)
            mid = getattr(result, "message_id", None)
            if chat is not None and mid is not None:
                remember(int(chat.id), int(mid))
        except Exception:
            pass
        return result


def install(bot) -> None:
    """Подключить middleware к bot.session."""
    bot.session.middleware(CollectMessageIdsMiddleware())
