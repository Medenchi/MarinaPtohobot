"""Генератор JSON-флоу через Claude API.

Использует системный промпт из docs/AI_FLOW_PROMPT.md, шлёт пользовательскую
задачу в Claude (по умолчанию claude-opus-4-7), валидирует ответ через наш
validator.validate_graph, и при ошибках просит Claude исправить (до 3 итераций).

Запуск:
    export ANTHROPIC_API_KEY=sk-ant-api03-...
    python3 scripts/gen_flow.py \\
        --task "Сделай флоу-викторину про стиль из 6 вопросов" \\
        --out docs/flows/style_quiz.json \\
        --model claude-opus-4-7
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx

# Локальный валидатор
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.bot.runtime.validator import summary, validate_graph  # noqa: E402

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

PROMPT_FILE = Path(__file__).resolve().parent.parent / "docs" / "AI_FLOW_PROMPT.md"


def extract_system_prompt() -> str:
    """Берём всё между ====BEGIN PROMPT==== и ====END PROMPT==== из AI_FLOW_PROMPT.md
    и дополняем «свежими» разделами v2/v3 из того же файла.
    """
    text = PROMPT_FILE.read_text(encoding="utf-8")
    m = re.search(r"====BEGIN PROMPT====\n(.*?)\n====END PROMPT====", text, re.S)
    body = m.group(1) if m else text
    # Также подмешиваем v2/v3 секции (находятся ниже)
    v2_v3 = re.search(r"## 🆕 v2.*", text, re.S)
    if v2_v3:
        body += "\n\n" + v2_v3.group(0)
    return body


def extract_json(text: str) -> dict:
    """Достаём первый JSON-объект из ответа модели (на случай если она обернула в ``` или дала пояснения)."""
    text = text.strip()
    # ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    # просто {...}
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Не нашёл JSON в ответе модели")


def call_claude(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 8000,
) -> str:
    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    with httpx.Client(timeout=120.0) as cli:
        r = cli.post(API_URL, headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Claude API {r.status_code}: {r.text}")
        data = r.json()
    return data["content"][0]["text"]


def generate(
    task: str,
    *,
    model: str = "claude-opus-4-7",
    max_iters: int = 3,
    api_key: str | None = None,
) -> dict:
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY не задан")

    system = extract_system_prompt()
    user_message = f"### Задача\n\n{task}\n\nВерни ТОЛЬКО JSON, без markdown-обёрток и комментариев."
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for attempt in range(1, max_iters + 1):
        print(f"→ Запрос к {model} (попытка {attempt}/{max_iters})...", flush=True)
        try:
            response_text = call_claude(api_key, model, system, messages)
        except Exception as exc:
            raise SystemExit(f"Ошибка API: {exc}") from exc

        try:
            flow = extract_json(response_text)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"⚠ Не смог распарсить JSON: {exc}", flush=True)
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"JSON невалиден: {exc}. Пришли ВЕСЬ JSON заново, чистым, без обёрток."})
            continue

        graph = flow.get("graph") or {}
        issues = validate_graph(graph)
        summ = summary(issues)
        print(f"  Валидатор: ❗ {summ['error']}  ⚠ {summ['warning']}  💡 {summ['hint']}  (узлов: {len(graph.get('nodes', []))})", flush=True)

        errors = [i for i in issues if i["level"] == "error"]
        if not errors:
            return flow

        # Просим исправить
        err_text = "\n".join(f'  - {i["code"]} в `{i.get("node_id") or "?"}`: {i["message"]}' for i in errors[:10])
        print(f"  Ошибки:\n{err_text}", flush=True)
        messages.append({"role": "assistant", "content": json.dumps(flow, ensure_ascii=False)})
        messages.append({
            "role": "user",
            "content": (
                f"AI-валидатор нашёл ошибки:\n{err_text}\n\n"
                "Исправь их и пришли ВЕСЬ JSON заново. Без комментариев и markdown — только чистый объект."
            ),
        })

    raise SystemExit(f"Не удалось получить валидный флоу за {max_iters} попыток")


def main() -> None:
    ap = argparse.ArgumentParser(description="Генератор JSON-флоу через Claude API")
    ap.add_argument("--task", required=True, help="Описание желаемого флоу")
    ap.add_argument("--out", required=True, help="Путь сохранения JSON (например docs/flows/my.json)")
    ap.add_argument("--model", default="claude-opus-4-7", help="ID модели (по умолч. claude-opus-4-7)")
    ap.add_argument("--iters", type=int, default=3, help="Макс итераций самовалидации")
    args = ap.parse_args()

    flow = generate(args.task, model=args.model, max_iters=args.iters)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Сохранено: {out}")
    print(f"   Узлов: {len(flow.get('graph', {}).get('nodes', []))}")


if __name__ == "__main__":
    main()
