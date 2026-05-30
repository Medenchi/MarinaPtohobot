"""Догенерируем АКТ 1+2 — мельче, чтобы не упасть в 504."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.bot.runtime.validator import summary, validate_graph

API_KEY = os.environ["OPENAI_API_KEY"]
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.freemodel.dev")
MODEL = os.environ.get("MODEL", "gpt-5.4")

COMMON = """Ты пишешь часть JSON-флоу для бота Марины Заугольниковой.
ВЕРНИ ТОЛЬКО МАССИВ узлов [ {id,type,params,next}, ... ] — без markdown, без комментариев.
Каждый узел уже доступного типа: command, send_message, ask_question, branch, switch, set_variable, goto, end.
Лёгкая разметка ~b:..~ ~i:..~ ~qx:..~ ~emoji:5368324170671202286|✨~
Кнопки: buttons:[[{text,next?,url?,style?}]] МАССИВ РЯДОВ
Стили кнопок: primary | success | danger | (или не указывать)
URL только https://, http://, tg://, t.me/
ВСЕ ask_question имеют variable.
"""

PARTS = [
    {
        "name": "Часть 1A — Триггеры и welcome",
        "task": """Создай массив из 6 узлов:

1. {id:"start", type:"command", params:{command:"start"}, next:"welcome_branch_ref"}
2. {id:"brief", type:"command", params:{command:"brief"}, next:"ask_feeling"}
3. {id:"welcome_branch_ref", type:"branch", params:{variable:"{{vars.ref}}", op:"not_empty", value:"", true_next:"welcome_with_ref", false_next:"welcome_clean"}}
4. {id:"welcome_with_ref", type:"send_message", params:{text:"~b:Привет, {{user.first_name}}!~ ~emoji:5368324170671202286|✨~\\n\\nЯ вижу, ты пришла с метки ~code:{{vars.ref}}~ — наверняка из моей Pinterest-доски...\\n\\n~qx:Я — Марина. Я люблю снимать тот самый момент, который остаётся с тобой надолго: в дыхании, в жесте, в свете на ресницах. Сделаем такой кадр?~", buttons:[[{text:"✨ Поехали", next:"ask_feeling", style:"primary"}], [{text:"💼 Я по работе", next:"work_contact"}]]}, next:null}
5. {id:"welcome_clean", type:"send_message", params:{text:"~b:Привет, {{user.first_name}}!~ ~emoji:5368324170671202286|✨~\\n\\nЯ — Марина Заугольникова. Снимаю женщин и контент для экспертов в Москве.\\n\\n~qx:Помогу собрать твой идеальный визуальный образ — задам пару вопросов, покажу подборку и расскажу про съёмку. Идём?~", buttons:[[{text:"✨ Поехали", next:"ask_feeling", style:"primary"}], [{text:"💼 Я по работе", next:"work_contact"}]]}, next:null}
6. {id:"work_contact", type:"send_message", params:{text:"~b:Если ты по работе — пиши напрямую~\\n\\nМарина: ~link:https://t.me/mzaugolnikova|@mzaugolnikova~\\nСайт: ~link:https://zaugolnikova.ru/|zaugolnikova.ru~", buttons:[[{text:"💬 Написать", url:"https://t.me/mzaugolnikova", style:"success"}], [{text:"🌐 Сайт", url:"https://zaugolnikova.ru/"}], [{text:"← Назад", next:"welcome_clean"}]]}, next:null}

ВЕРНИ ТОЛЬКО МАССИВ.""",
    },
    {
        "name": "Часть 1B — Вопрос-чувство и switch",
        "task": """Создай массив из 2 узлов:

1. {id:"ask_feeling", type:"ask_question", params:{text:"~b:Что для тебя важнее всего в идее съёмки?~\\n\\nВыбери то, что отзывается сильнее", variable:"feeling", inline:true, options:[{text:"✨ Почувствовать себя красивой", value:"beauty"}, {text:"🤍 Запомнить важный момент", value:"memory"}, {text:"📸 Контент для соцсетей", value:"content"}, {text:"🤰 Беременность/семья/love", value:"family"}, {text:"👀 Просто посмотреть", value:"browse"}]}, next:"feeling_switch"}

2. {id:"feeling_switch", type:"switch", params:{variable:"feeling", cases:{"beauty":"reflect_beauty","memory":"reflect_memory","content":"reflect_content","family":"reflect_family","browse":"reflect_browse"}, default:"reflect_beauty"}, next:null}

ВЕРНИ ТОЛЬКО МАССИВ.""",
    },
    {
        "name": "Часть 1C — 5 reflect-узлов (резонансы)",
        "task": """Создай массив из 5 узлов-резонансов — каждый отвечает на чувство пользователя поэтично и ведёт в ask_occasion.

1. {id:"reflect_beauty", type:"send_message", params:{text:"~b:Почувствовать себя красивой~ ~emoji:5368324170671202286|✨~\\n\\n~i:Это самое честное желание. И самое правильное.~\\n\\n~qx:Я снимаю женщин так, чтобы они потом сами удивлялись: «Это что — Я?». Никакой пластики, только свет и точка съёмки, которая раскрывает тебя настоящую.~", buttons:[[{text:"Идём дальше ✨", next:"ask_occasion", style:"primary"}]]}, next:null}

2. {id:"reflect_memory", type:"send_message", params:{text:"~b:Запомнить важный момент~ ~emoji:5368324170671202287|🌿~\\n\\n~i:Время не остановить — но кадр может его удержать.~\\n\\n~qx:Когда мои клиенты возвращаются через год, два, пять — они говорят, что эти фото стали якорями для воспоминаний. Не парадные постеры, а живые мгновения.~", buttons:[[{text:"Идём дальше 🌿", next:"ask_occasion", style:"primary"}]]}, next:null}

3. {id:"reflect_content", type:"send_message", params:{text:"~b:Контент для соцсетей~ ~emoji:5368324170671202288|💫~\\n\\n~i:Понимаю. Эксперту нужны фото, от которых не стыдно ставить в шапку и закрепы.~\\n\\n~qx:Снимаю с акцентом на твою экспертность и стиль. Не «модельная вечеринка», а тёплая, минималистичная подача — то, что работает в визуале бренда.~", buttons:[[{text:"Идём дальше 💫", next:"ask_occasion", style:"primary"}]]}, next:null}

4. {id:"reflect_family", type:"send_message", params:{text:"~b:Семья, love-story, беременность~ ~emoji:5368324170671202287|🌿~\\n\\n~i:Самые честные кадры — когда любовь не позирует.~\\n\\n~qx:Снимаю семьи и пары так, чтобы лучшие фотки получались в моменты «между» — пока ребёнок смеётся, пока вы держитесь за руки автоматически. Без вымученных поз.~", buttons:[[{text:"Идём дальше 🌿", next:"ask_occasion", style:"primary"}]]}, next:null}

5. {id:"reflect_browse", type:"send_message", params:{text:"~b:Просто посмотреть~ ~emoji:5368324170671202286|✨~\\n\\n~i:Тоже отлично — не все решают сразу.~\\n\\n~qx:Давай покажу тебе подборку образов под твой стиль и расскажу про пакеты — без давления. Когда решишь — я здесь.~", buttons:[[{text:"Хорошо, дальше ✨", next:"ask_occasion", style:"primary"}]]}, next:null}

ВЕРНИ ТОЛЬКО МАССИВ.""",
    },
    {
        "name": "Часть 1D — 3 вопроса о подборе + set_season",
        "task": """Создай массив из 4 узлов:

1. {id:"ask_occasion", type:"ask_question", params:{text:"~b:По какому поводу подбираем образы?~ ~emoji:5368324170671202289|📸~", variable:"occasion", inline:true, options:[{text:"💕 Love-story", value:"love-story"}, {text:"👨‍👩‍👧 Семейная", value:"семейная съёмка"}, {text:"🤰 Беременность", value:"беременность"}, {text:"👩 Индивидуальная", value:"индивидуальная"}, {text:"🤝 Lookbook", value:"lookbook"}, {text:"📱 Контент", value:"контент для соцсетей"}, {text:"🤷 Ещё думаю", value:""}]}, next:"ask_style"}

2. {id:"ask_style", type:"ask_question", params:{text:"~b:Какой стиль ближе?~\\n~i:Без правильного ответа — что нравится тебе~", variable:"style", inline:true, options:[{text:"🤍 Минимализм", value:"минимализм"}, {text:"👔 Классика", value:"классика"}, {text:"🍂 Old money", value:"old money"}, {text:"👕 Casual", value:"casual"}, {text:"🌸 Романтика", value:"романтика"}, {text:"🌊 Бохо", value:"бохо"}, {text:"🤷 Любой", value:""}]}, next:"ask_color"}

3. {id:"ask_color", type:"ask_question", params:{text:"~b:Какие цвета любишь в кадре?~", variable:"color", inline:true, options:[{text:"🤎 Бежевый", value:"бежевый"}, {text:"🤍 Белый", value:"белый"}, {text:"🖤 Чёрный", value:"чёрный"}, {text:"🥛 Молочный", value:"молочный"}, {text:"🫒 Оливковый", value:"оливковый"}, {text:"🌸 Пастельный", value:"пастельный"}, {text:"🤷 Любой", value:""}]}, next:"set_season"}

4. {id:"set_season", type:"set_variable", params:{name:"season", value:"{{system.season}}"}, next:"typing_search"}

ВЕРНИ ТОЛЬКО МАССИВ.""",
    },
]

def call(messages, max_tokens=8000, timeout=180):
    headers = {"Authorization": f"Bearer {API_KEY}", "content-type": "application/json"}
    payload = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    with httpx.Client(timeout=timeout) as cli:
        r = cli.post(f"{BASE.rstrip('/')}/v1/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]

def extract_array(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    if m: return json.loads(m.group(1))
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end+1])
    raise ValueError("Не нашёл массив")

new_nodes = []
for i, part in enumerate(PARTS, 1):
    print(f"\n=== ЧАСТЬ 1.{chr(64+i)}: {part['name']} ===")
    msgs = [{"role":"system","content":COMMON},{"role":"user","content":part["task"]}]
    for attempt in range(1, 4):
        print(f"  попытка {attempt}/3...")
        try:
            text = call(msgs, max_tokens=6000, timeout=180)
            nodes = extract_array(text)
            print(f"  ✓ узлов: {len(nodes)}")
            new_nodes.extend(nodes)
            break
        except Exception as e:
            print(f"  ✗ {str(e)[:200]}")
            if attempt >= 3:
                print(f"  СКИП")

print(f"\n=== Догенерено: {len(new_nodes)} узлов АКТ 1+2 ===")

# Грузим существующий grand_funnel.json и склеиваем
flow_path = Path("docs/flows/grand_funnel.json")
flow = json.loads(flow_path.read_text())
existing_ids = {n["id"] for n in flow["graph"]["nodes"]}

# Добавляем только новые
added = 0
for n in new_nodes:
    if n["id"] not in existing_ids:
        flow["graph"]["nodes"].insert(0, n)  # вставляем в начало
        existing_ids.add(n["id"])
        added += 1
    else:
        print(f"  ⚠ дубль id: {n['id']} — пропускаю")

# Раскладываем заново
for idx, n in enumerate(flow["graph"]["nodes"]):
    n["position"] = {"x": 80 + (idx % 6) * 280, "y": 80 + (idx // 6) * 200}

# Валидируем
issues = validate_graph(flow["graph"])
summ = summary(issues)
print(f"\nВсего узлов: {len(flow['graph']['nodes'])}")
print(f"Валидатор: ❗{summ['error']} ⚠{summ['warning']} 💡{summ['hint']}")
errors = [i for i in issues if i["level"]=="error"]
for e in errors[:15]:
    print(f"  - {e['code']} в {e.get('node_id')}: {e['message']}")

flow_path.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ Обновлён {flow_path}: {len(flow_path.read_text().splitlines())} строк")
