"""Статический валидатор графа флоу.

Гоняется и в боте (перед сохранением сессии и при загрузке published),
и доступен из мини-конструктора в боте. Цель — поймать классические ошибки:

* битые ссылки `next` / `target` на несуществующие id;
* отсутствие хотя бы одного триггера;
* дублирующиеся id;
* `ask_question` без `variable`;
* `send_message`/`ask_question` с пустым text;
* потенциально бесконечные циклы (узел ссылается сам на себя без выхода).

Возвращаем структуру с уровнями ``error|warning|hint`` — фронтенд может
рисовать бейджи на узлах.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal, TypedDict

from app.bot.runtime.format import find_format_issues

Level = Literal["error", "warning", "hint"]


class Issue(TypedDict):
    level: Level
    node_id: str | None
    message: str
    code: str


TRIGGER_TYPES = {"command", "text_match"}
NEXT_BEARING = {
    "send_message",
    "ask_question",
    "set_var",
    "branch",
    "send_photo",
    "send_document",
    "buttons",
    "delay",
}


def _walk_nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = graph.get("nodes") or []
    return [n for n in nodes if isinstance(n, dict)]


def validate_graph(graph: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    nodes = _walk_nodes(graph)
    ids: dict[str, int] = {}
    for n in nodes:
        nid = n.get("id")
        if not nid:
            issues.append(
                {"level": "error", "node_id": None, "code": "missing_id", "message": "Узел без id"}
            )
            continue
        ids[nid] = ids.get(nid, 0) + 1
    for nid, count in ids.items():
        if count > 1:
            issues.append(
                {
                    "level": "error",
                    "node_id": nid,
                    "code": "duplicate_id",
                    "message": f"id «{nid}» встречается {count} раз",
                }
            )

    has_trigger = any(n.get("type") in TRIGGER_TYPES for n in nodes)
    if not has_trigger:
        issues.append(
            {
                "level": "error",
                "node_id": None,
                "code": "no_trigger",
                "message": "В флоу нет ни одного триггера (command/text_match)",
            }
        )

    node_by_id = {n["id"]: n for n in nodes if n.get("id")}

    for n in nodes:
        nid = n.get("id") or "?"
        ntype = n.get("type")
        params = n.get("params") or {}
        nxt = n.get("next")

        if nxt and nxt not in node_by_id:
            issues.append(
                {
                    "level": "error",
                    "node_id": nid,
                    "code": "dangling_next",
                    "message": f"next=«{nxt}» указывает в никуда",
                }
            )
        if nxt == nid and ntype in NEXT_BEARING:
            issues.append(
                {
                    "level": "warning",
                    "node_id": nid,
                    "code": "self_loop",
                    "message": "Узел ссылается сам на себя — возможен бесконечный цикл",
                }
            )

        if ntype == "send_message" and not (params.get("text") or "").strip():
            issues.append(
                {
                    "level": "warning",
                    "node_id": nid,
                    "code": "empty_text",
                    "message": "Пустой текст сообщения",
                }
            )
        if ntype == "ask_question":
            if not (params.get("variable") or "").strip():
                issues.append(
                    {
                        "level": "error",
                        "node_id": nid,
                        "code": "no_variable",
                        "message": "ask_question без переменной — ответ потеряется",
                    }
                )
            if not (params.get("text") or "").strip():
                issues.append(
                    {
                        "level": "warning",
                        "node_id": nid,
                        "code": "empty_question",
                        "message": "Вопрос без текста",
                    }
                )
        # Кнопки бывают и у send_message и у buttons; они могут быть list[list[dict]]
        btns = params.get("buttons")
        if btns is not None or ntype == "buttons":
            if not btns and ntype == "buttons":
                issues.append(
                    {
                        "level": "warning",
                        "node_id": nid,
                        "code": "no_buttons",
                        "message": "У блока кнопок пустой список",
                    }
                )
            for entry in btns if isinstance(btns, list) else []:
                row = entry if isinstance(entry, list) else [entry]
                for b in row:
                    if not isinstance(b, dict) or b.get("url"):
                        continue
                    tgt = b.get("target") or b.get("next")
                    if tgt and tgt not in node_by_id:
                        issues.append(
                            {
                                "level": "error",
                                "node_id": nid,
                                "code": "dangling_button",
                                "message": f"Кнопка ведёт на «{tgt}», которого нет",
                            }
                        )

    # ----- Лёгкая разметка ~b:..~ ~link:..~ ~emoji:..~ -----
    def _walk(v: Any, nid: str | None) -> None:
        if isinstance(v, str):
            for msg in find_format_issues(v):
                issues.append(
                    {
                        "level": "warning",
                        "node_id": nid,
                        "code": "format_issue",
                        "message": msg,
                    }
                )
        elif isinstance(v, list):
            for item in v:
                _walk(item, nid)
        elif isinstance(v, dict):
            for val in v.values():
                _walk(val, nid)

    for n in nodes:
        _walk(n.get("params"), n.get("id"))

    # Достижимость от триггеров
    reachable: set[str] = set()
    stack = [n["id"] for n in nodes if n.get("type") in TRIGGER_TYPES and n.get("id")]
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        n = node_by_id.get(cur)
        if not n:
            continue
        if n.get("next"):
            stack.append(n["next"])
        for entry in (n.get("params") or {}).get("buttons") or []:
            row = entry if isinstance(entry, list) else [entry]
            for b in row:
                if isinstance(b, dict):
                    t = b.get("target") or b.get("next")
                    if t:
                        stack.append(t)
        # branch: true_next / false_next
        if n.get("type") == "branch":
            for k in ("true_next", "false_next"):
                t = (n.get("params") or {}).get(k)
                if t:
                    stack.append(t)

    for nid in node_by_id:
        n = node_by_id[nid]
        if n.get("type") in TRIGGER_TYPES:
            continue
        if nid not in reachable:
            issues.append(
                {
                    "level": "hint",
                    "node_id": nid,
                    "code": "unreachable",
                    "message": "Блок не достижим ни из одного триггера",
                }
            )
    return issues


def summary(issues: Iterable[Issue]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0, "hint": 0}
    for i in issues:
        counts[i["level"]] = counts.get(i["level"], 0) + 1
    return counts
