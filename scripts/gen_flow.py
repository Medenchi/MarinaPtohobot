"""Генератор JSON-флоу через Claude API ИЛИ OpenAI-совместимый эндпоинт.

Использует системный промпт из docs/AI_FLOW_PROMPT.md, шлёт пользовательскую
задачу в модель, валидирует ответ через validator.validate_graph, и при
ошибках просит модель исправить (до 3 итераций).

Запуск:
  # Anthropic native (https://api.anthropic.com)
  export ANTHROPIC_API_KEY=sk-ant-api03-...
  python3 scripts/gen_flow.py --task '...' --out docs/flows/x.json

  # OpenAI-совместимый (freemodel / OpenRouter / etc.)
  export OPENAI_API_KEY=fe_oa_...
  export OPENAI_BASE_URL=https://api.freemodel.dev
  python3 scripts/gen_flow.py --task '...' --out docs/flows/x.json --model gpt-5.5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.bot.runtime.validator import summary, validate_graph  # noqa: E402

PROMPT_FILE = Path(__file__).resolve().parent.parent / "docs" / "AI_FLOW_PROMPT.md"


def extract_system_prompt() -> str:
    text = PROMPT_FILE.read_text(encoding="utf-8")
    m = re.search(r"====BEGIN PROMPT====\n(.*?)\n====END PROMPT====", text, re.S)
    body = m.group(1) if m else text
    v2_v3 = re.search(r"## 🆕 v2.*", text, re.S)
    if v2_v3:
        body += "\n\n" + v2_v3.group(0)
    return body


def extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Не нашёл JSON в ответе модели")


def call_anthropic(api_key: str, base: str, model: str, system: str, messages: list[dict], max_tokens: int) -> str:
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    payload = {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages}
    with httpx.Client(timeout=180.0) as cli:
        r = cli.post(f"{base.rstrip('/')}/v1/messages", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Anthropic API {r.status_code}: {r.text[:400]}")
        return r.json()["content"][0]["text"]


def call_openai(api_key: str, base: str, model: str, system: str, messages: list[dict], max_tokens: int) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
    oai_msgs = [{"role": "system", "content": system}] + messages
    payload = {"model": model, "max_tokens": max_tokens, "messages": oai_msgs}
    with httpx.Client(timeout=180.0) as cli:
        r = cli.post(f"{base.rstrip('/')}/v1/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"OpenAI API {r.status_code}: {r.text[:400]}")
        data = r.json()
    return data["choices"][0]["message"]["content"]


def call_model(api_key: str, base: str, model: str, system: str, messages: list[dict], max_tokens: int, provider: str) -> str:
    if provider == "openai":
        return call_openai(api_key, base, model, system, messages, max_tokens)
    return call_anthropic(api_key, base, model, system, messages, max_tokens)


def generate(
    task: str,
    *,
    model: str = "claude-opus-4-7",
    max_iters: int = 3,
    provider: str = "anthropic",
    api_key: str | None = None,
    base_url: str | None = None,
) -> dict:
    if provider == "openai":
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
    else:
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    if not api_key:
        raise SystemExit(f"API ключ для {provider} не задан")

    system = extract_system_prompt()
    user_message = f"### Задача\n\n{task}\n\nВерни ТОЛЬКО JSON-объект, без markdown-обёрток (без ```json), без комментариев."
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for attempt in range(1, max_iters + 1):
        print(f"→ {provider}/{model} (попытка {attempt}/{max_iters})...", flush=True)
        try:
            response_text = call_model(api_key, base_url, model, system, messages, 8000, provider)
        except Exception as exc:
            raise SystemExit(f"Ошибка API: {exc}") from exc

        try:
            flow = extract_json(response_text)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"  ⚠ Не распарсил JSON: {exc}", flush=True)
            print(f"  (preview ответа: {response_text[:200]!r})", flush=True)
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"JSON невалиден: {exc}. Пришли ВЕСЬ JSON заново, чистым, без обёрток."})
            continue

        graph = flow.get("graph") or {}
        issues = validate_graph(graph)
        summ = summary(issues)
        print(f"  Валидатор: ❗{summ['error']} ⚠{summ['warning']} 💡{summ['hint']} (узлов: {len(graph.get('nodes', []))})", flush=True)
        errors = [i for i in issues if i["level"] == "error"]
        if not errors:
            return flow
        err_text = "\n".join(f"  - {i['code']} в `{i.get('node_id') or '?'}`: {i['message']}" for i in errors[:10])
        print(f"  Ошибки:\n{err_text}", flush=True)
        messages.append({"role": "assistant", "content": json.dumps(flow, ensure_ascii=False)})
        messages.append({"role": "user", "content": f"AI-валидатор нашёл ошибки:\n{err_text}\n\nИсправь их и пришли ВЕСЬ JSON заново."})

    raise SystemExit(f"Не удалось получить валидный флоу за {max_iters} попыток")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-opus-4-7")
    ap.add_argument("--provider", choices=["anthropic", "openai"], default="anthropic")
    ap.add_argument("--iters", type=int, default=3)
    args = ap.parse_args()
    flow = generate(args.task, model=args.model, max_iters=args.iters, provider=args.provider)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Сохранено: {out}")
    print(f"   Узлов: {len(flow.get('graph', {}).get('nodes', []))}")


if __name__ == "__main__":
    main()
