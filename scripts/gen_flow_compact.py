"""Компактная версия генератора: короткий промпт (~3k), быстрая модель."""

from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.bot.runtime.validator import summary, validate_graph

COMPACT_SYSTEM = """Ты — генератор JSON-флоу для Telegram-бота фотографа Марины Заугольниковой.

Верни ТОЛЬКО JSON-объект {name, description, graph: {nodes, edges: []}}.
БЕЗ ```json```, БЕЗ комментариев, БЕЗ преамбулы. Сразу с символа `{`.

# Узел: { "id": "snake_case", "type": "...", "params": {...}, "next": "id_или_null", "position": {"x":N,"y":N} }

# Типы блоков:

## Триггеры (не исполняются, только указывают начало):
- command: params={command:"start"}, next: id
- text_match: params={pattern:"...", mode:"exact|contains|starts_with"}, next: id

## Сообщения:
- send_message: params={text, buttons?, parse_mode?, disable_preview?}
  text поддерживает лёгкую разметку: ~b:текст~ ~i:~ ~u:~ ~s:~ ~code:~ ~spoiler:~
    ~q:цитата~ ~qx:раскрыв. цитата~ ~link:url|текст~ ~emoji:ID|fallback~
  buttons: [[{text,next?,url?,style?,icon_custom_emoji_id?,value?}]] МАССИВ РЯДОВ
  style: primary|success|danger|warning|secondary (Bot API 9.4)
- send_heading: params={text, icon?, level?}
- send_quote: params={text, author?, expandable?}
- send_checklist: params={title?, items:[..]}
- typing: params={seconds}
- delay: params={seconds}

## Ввод:
- ask_question: params={text, variable, options?:[{text,value}], inline?:true}, next: id
- ask_poll: params={question, options:[..], variable, multiple?:bool}, next: id

## Логика:
- branch: params={variable:"{{vars.x}}", op:"eq|neq|contains|not_empty|empty|gt|lt|in", value, true_next, false_next}
  ВНИМАНИЕ: у branch НЕТ верхнего "next"! Только true_next/false_next в params.
- set_variable: params={name, value}, next: id
- goto: params={next:"id"}
- end: params={}, next: null
- switch: params={variable, cases:{"v1":"id1"}, default}
- random_branch: params={choices:["id_a","id_b"]}

## Данные:
- db_query: params={table, select, filters:[{column,op,value}], order_by?, limit?, save_to}, next: id
- db_insert: params={table, fields:{col:val}}, next: id

## Спец:
- show_outfits_voting: params={items_var:"matched_outfits", limit?, liked_var:"liked_ids", disliked_var:"disliked_ids", done_text, done_button}, next: id
- generate_pdf_voted: params={items_var, liked_var, filename, caption, send_now?:true, save_to}, next: id
- delete_last_message: params={count?:1}, next: id
- handoff_to_admin: params={text}, next: id

# Шаблоны переменных:
{{user.first_name}} {{user.username}} {{user.id}}
{{vars.X}} {{system.season}}

# Значения категорий Марины (1-в-1 в options.value для db_query ilike):
gender: женское, мужское
occasions: love-story, семейная съёмка, беременность, индивидуальная, lookbook, контент для соцсетей, репортаж, прогулка
styles: casual, smart casual, классика, романтика, минимализм, old money, бохо
colors: бежевый, белый, чёрный, серый, молочный, оливковый, пастельный, бордовый
budgets: до 5к, 5–15к, 15–30к, 30–60к, 60к+
shoot_types: студия, улица, природа, золотой час

# ЖЁСТКИЕ ПРАВИЛА:
1. id уникальны
2. Каждый next ссылается на существующий id или null
3. Каждый ask_question и ask_poll имеет params.variable
4. Минимум 1 триггер (command "start")
5. Все блоки достижимы от триггера через next/кнопки/branch
6. url только https://, http://, tg://, t.me/ — НЕЛЬЗЯ tel:, mailto:
7. buttons это [[..],[..]] — МАССИВ РЯДОВ
8. branch без верхнего "next" — только true_next/false_next
9. Тексты на «ты», с ~b:..~ ~i:..~ ~qx:..~ ~emoji:ID|fb~
10. JSON валиден
"""

def extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m: return json.loads(m.group(1))
    start = text.find("{"); end = text.rfind("}")
    if start >= 0 and end > start: return json.loads(text[start:end+1])
    raise ValueError("Не нашёл JSON")

def call_openai(api_key, base, model, system, messages, max_tokens=16000, timeout=300.0):
    headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
    payload = {"model": model, "max_tokens": max_tokens,
               "messages": [{"role":"system","content":system}] + messages}
    with httpx.Client(timeout=timeout) as cli:
        r = cli.post(f"{base.rstrip('/')}/v1/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"API {r.status_code}: {r.text[:400]}")
        return r.json()["choices"][0]["message"]["content"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt-5.4-mini")
    ap.add_argument("--iters", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com")
    if not api_key: raise SystemExit("OPENAI_API_KEY не задан")

    user_msg = f"### Задача\n\n{args.task}\n\nВерни JSON и НИЧЕГО кроме."
    messages = [{"role":"user","content":user_msg}]

    for attempt in range(1, args.iters+1):
        print(f"→ {args.model} ({attempt}/{args.iters})...", flush=True)
        try:
            text = call_openai(api_key, base, args.model, COMPACT_SYSTEM, messages, timeout=args.timeout)
        except Exception as exc:
            print(f"  err: {exc}", flush=True)
            if attempt >= args.iters: raise SystemExit(str(exc))
            continue
        try:
            flow = extract_json(text)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"  ⚠ {exc}", flush=True)
            print(f"  preview: {text[:200]!r}", flush=True)
            messages.append({"role":"assistant","content":text})
            messages.append({"role":"user","content":f"JSON невалиден: {exc}. Только JSON, целиком."})
            continue
        graph = flow.get("graph") or {}
        issues = validate_graph(graph)
        summ = summary(issues)
        print(f"  ❗{summ['error']} ⚠{summ['warning']} 💡{summ['hint']} ({len(graph.get('nodes',[]))} узлов)", flush=True)
        errors = [i for i in issues if i["level"]=="error"]
        if not errors:
            out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n✅ Сохранено: {out}\n   Узлов: {len(graph.get('nodes',[]))}")
            return
        err_text = "\n".join(f"- {i['code']} в `{i.get('node_id') or '?'}`: {i['message']}" for i in errors[:10])
        print(f"  Ошибки:\n{err_text}", flush=True)
        messages.append({"role":"assistant","content":json.dumps(flow, ensure_ascii=False)})
        messages.append({"role":"user","content":f"Ошибки валидатора:\n{err_text}\n\nИсправь, целиком JSON."})

    raise SystemExit(f"Не удалось за {args.iters} попыток")

if __name__ == "__main__":
    main()
