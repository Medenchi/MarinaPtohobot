"""Генератор большой воронки по частям.

Чтобы обойти 60-секундный таймаут прокси cc.freemodel.dev, разбиваем
генерацию на 5 актов и склеиваем результат в один граф.
"""

from __future__ import annotations
import json, os, re, sys
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.bot.runtime.validator import summary, validate_graph

API_KEY = os.environ.get("OPENAI_API_KEY")
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.freemodel.dev")
MODEL = os.environ.get("MODEL", "gpt-5.4")

if not API_KEY:
    raise SystemExit("OPENAI_API_KEY не задан")

COMMON = """Ты пишешь часть JSON-флоу для бота фотографа Марины Заугольниковой.
Верни ТОЛЬКО JSON-массив узлов: [ {id,type,params,next,position}, ... ]
БЕЗ обёрток ```json```, БЕЗ комментариев, БЕЗ описаний.
С символа `[`.

# Типы блоков (используй ТОЛЬКО эти):
- command (params:{command}, next)
- text_match (params:{pattern,mode:exact|contains|starts_with}, next)
- send_message (params:{text,buttons?:[[{text,next?,url?,style?,icon_custom_emoji_id?}]]}, next)
- send_heading (params:{text,icon?,level?:1|2|3}, next)
- send_quote (params:{text,author?,expandable?:true}, next)
- send_checklist (params:{title?,items:[..]}, next)
- typing (params:{seconds}, next)
- delay (params:{seconds}, next)
- ask_question (params:{text,variable!,options?:[{text,value}],inline?:true}, next)
- branch (params:{variable,op:eq|neq|contains|not_empty|empty|gt|lt,value,true_next,false_next})
  ⚠ branch НЕ имеет верхнего next!
- switch (params:{variable,cases:{"v":"id"},default}, next: null)
- set_variable (params:{name,value}, next)
- goto (params:{next}, next: null)
- end (params:{}, next: null)
- db_query (params:{table,select,filters:[{column,op,value}],order_by?,descending?,limit?,save_to}, next)
- show_outfits_voting (params:{items_var,limit?,liked_var,disliked_var,done_text,done_button}, next)
- generate_pdf_voted (params:{items_var,liked_var,filename,caption,send_now?:true,save_to}, next)
- handoff_to_admin (params:{text}, next)

# Лёгкая разметка (используй везде в текстах):
- ~b:текст~ ~i:..~ ~u:..~ ~s:..~ ~code:..~ ~spoiler:..~
- ~q:цитата~ ~qx:длинная раскрывающаяся цитата~
- ~link:https://t.me/x|написать~
- ~emoji:5368324170671202286|✨~ — premium-эмодзи

# Цвета кнопок (только 4 валидных значения):
default | primary | success | danger
warning/secondary НЕ существуют — TG вернёт invalid button style!

# Значения категорий Марины (для db_query ilike):
gender: женское, мужское
occasions: love-story, семейная съёмка, беременность, индивидуальная, lookbook, контент для соцсетей, репортаж
styles: casual, smart casual, классика, романтика, минимализм, old money, бохо
colors: бежевый, белый, чёрный, серый, молочный, оливковый, пастельный, бордовый
budgets: до 5к, 5-15к, 15-30к, 30-60к, 60к+
shoot_types: студия, улица, природа, золотой час

# Переменные:
{{user.first_name}} {{user.username}}
{{vars.X}} — ask_question.variable, set_variable.name, db_query.save_to
{{vars.ref}} — deep-link payload (если /start пришёл с реф-меткой)
{{system.season}} — зима|весна|лето|осень
{{system.date}}

# ЖЁСТКИЕ ПРАВИЛА:
- id уникальны (snake_case)
- url в кнопках: ТОЛЬКО https:// http:// tg:// t.me/
- buttons — МАССИВ РЯДОВ [[btn,btn],[btn]]
- parse_mode не указывай (HTML по умолчанию)
- Тон Марины: на ты, поэтично, без сладости
"""

PARTS = [
    {
        "name": "АКТ 1+2 — Знакомство и Персонализация",
        "task": """Создай ОТДЕЛЬНЫЙ массив узлов для актов 1 и 2.

УЗЛЫ:
- start (command, command:"start") → welcome_branch_ref
- brief (command, command:"brief") → ask_feeling (на случай /brief)
- welcome_branch_ref (branch на {{vars.ref}} op:not_empty) — если есть ref → welcome_with_ref, иначе → welcome_clean
- welcome_with_ref (send_message): текст "~b:Привет, {{user.first_name}}!~ Я вижу, ты с метки ~code:{{vars.ref}}~..." с premium-emoji, кнопки [["✨ Поехали","ask_feeling","primary"], ["💼 Я по работе","work_contact"]]
- welcome_clean (send_message): обычное приветствие без упоминания ref, те же кнопки
- work_contact (send_message): "Тебе быстрее напрямую: @mzaugolnikova" + кнопка "Написать" url=https://t.me/mzaugolnikova, "Сайт" url=https://zaugolnikova.ru/, "← Назад" next=welcome_clean
- ask_feeling (ask_question, variable:"feeling", inline:true) с 5 вариантами: "✨ Почувствовать себя красивой" (value:beauty), "🤍 Запомнить важный момент" (memory), "📸 Контент для соцсетей" (content), "🤰 Беременность/семья/love" (family), "👀 Просто посмотреть" (browse)
- feeling_switch (switch, variable:"feeling", cases:{"beauty":"reflect_beauty",...})
- reflect_beauty, reflect_memory, reflect_content, reflect_family, reflect_browse (по 5 send_message с поэтичными резонансами на 3-4 строки каждый с ~qx:..~ цитатами и premium-emoji, все next:ask_occasion)
- ask_occasion (ask_question, variable:"occasion", inline:true) с 6 вариантами (love-story/семейная съёмка/беременность/индивидуальная/lookbook/контент для соцсетей) + "🤷 ещё думаю" value:""
- ask_style (ask_question, variable:"style") с 6 вариантами + "любой" value:""
- ask_color (ask_question, variable:"color") с 6 вариантами + "любой"
- set_season (set_variable, name:"season", value:"{{system.season}}") → typing_search

Всего ~25 узлов. ВСЕ тексты на ты, с ~b:~i:~qx:..~ и premium-emoji.
ВЕРНИ ТОЛЬКО МАССИВ УЗЛОВ.""",
        "next_hint": "typing_search",
    },
    {
        "name": "АКТ 3 — Витрина с подборкой",
        "task": """Создай массив узлов для акта 3.

УЗЛЫ:
- typing_search (typing, seconds:2) → search_msg
- search_msg (send_message): "~i:Сейчас подбираю под тебя что-то особенное...~ ~emoji:5368324170671202288|💫~" → query_outfits
- query_outfits (db_query, table:"outfits", select:"*, outfit_images(*)", filters:[is_published eq true, occasions ilike "%{{vars.occasion}}%", styles ilike "%{{vars.style}}%"], save_to:"matched_outfits", limit:15) → check_empty
- check_empty (branch, variable:"{{vars.matched_outfits}}", op:not_empty, true_next:"intro_show", false_next:"empty_state")
- empty_state (send_message): "~b:Странно — точного совпадения нет~ Но могу показать ~i:самое близкое по настроению~..." кнопки [["✨ Показать ближайшее","query_nearest","primary"], ["🔄 Начать заново","ask_feeling"]]
- query_nearest (db_query, только is_published + occasions, save_to:"matched_outfits", limit:20) → intro_show
- intro_show (send_message): "~b:Вот что подобралось для тебя~ ~emoji:5368324170671202286|✨~\n\n~qx:Отмечай только то, что хочется надеть прямо сейчас. Никакой логики, только сердце.~" → voting
- voting (show_outfits_voting, items_var:"matched_outfits", limit:15, liked_var:"liked_ids", disliked_var:"disliked_ids", done_text:"Когда отметишь — нажми, и я соберу PDF", done_button:"✨ Готово, собрать подборку") → make_pdf
- make_pdf (generate_pdf_voted, items_var:"matched_outfits", liked_var:"liked_ids", filename:"podbor_marina.pdf", caption:"~b:Твоя подборка~ ~emoji:5368324170671202286|✨~ Раздел 'Понравилось' собран по твоим лайкам.", send_now:true, save_to:"pdf") → after_pdf
- after_pdf (send_message): "~b:Готово!~ PDF у тебя 💫\n\nКак ощущения от подборки?" с кнопками [["💖 Очень в точку!","reviews_block","success"], ["🤔 Есть вопросы","objections_menu"], ["📸 Хочу записаться","when_question","primary"]]

Всего ~10 узлов. ВЕРНИ ТОЛЬКО МАССИВ УЗЛОВ.""",
        "next_hint": "after_pdf",
    },
    {
        "name": "АКТ 4 — Социальные доказательства",
        "task": """Создай массив узлов для акта 4 (отзывы и about Марины).

УЗЛЫ:
- reviews_block (send_message): про Марину + 1 отзыв в ~qx:..~ с premium-emoji, кнопки [["💬 Ещё отзыв","review_2"], ["📸 Хочу съёмку","when_question","primary"]]
- review_2 (send_message): второй отзыв ~qx:..~ от другой клиентки (про семейную съёмку), кнопки [["💬 Ещё","review_3"], ["📸 К пакетам","when_question","success"]]
- review_3 (send_message): третий отзыв ~qx:..~ (про беременность), кнопки [["📸 Хочу так же","when_question","primary"], ["🤔 Есть вопросы","objections_menu"]]
- about_marina (send_message): "~b:Кто я~\n\n~i:Снимаю женщин 5+ лет.~ Работаю с естественным светом, делаю лёгкую ретушь без пластики. ~qx:В портфолио более 800 девушек — каждая нашла свой кадр.~" + кнопки [["📸 Записаться","when_question","primary"], ["💬 Написать","external_marina"]]
- external_marina (send_message): "Пиши! Я отвечаю быстро ~emoji:5368324170671202288|💫~" + url-кнопка к @mzaugolnikova

Все отзывы — РАЗНЫЕ, на разные типы съёмок, тон правдоподобный, не приторный.
Например первый — про индивидуальную ("боялась камеры, но Марина создала атмосферу"),
второй — про семейную ("дети сами просили ещё фоткать"),
третий — про беременность ("мягко, без давления, очень женственно").

Всего 5 узлов. ВЕРНИ ТОЛЬКО МАССИВ.""",
        "next_hint": "when_question",
    },
    {
        "name": "АКТ 5 — Снятие возражений",
        "task": """Создай массив узлов для акта 5 (FAQ-меню с возражениями).

УЗЛЫ:
- objections_menu (send_message): "~b:Что важно узнать заранее?~ ~emoji:5368324170671202287|🌿~\n\nВыбери — отвечу подробно:" с кнопками-рядами:
  [["😅 Я не фотогенична","obj_camera_shy"]]
  [["💸 Дорого ли это?","obj_price"]]
  [["🕐 Сколько по времени?","obj_time"]]
  [["👗 Что надеть?","obj_clothes"]]
  [["👶 Можно с детьми?","obj_kids"]]
  [["📸 Готова записаться","when_question","success"]]

- obj_camera_shy (send_message): "~b:Каждый второй так говорит~\n\n~qx:Я понимаю это как никто. У меня в начале съёмки всегда есть 10 минут «привыкания» — мы просто болтаем, смотрим референсы, я показываю как стать. Никто не толкает позировать с порога — мы плавно входим в кадр через жесты и дыхание.~ \n\nЕсли стесняешься — пиши, я отвечу, как смягчить страх ~emoji:5368324170671202287|🌿~" + [["← Назад","objections_menu"],["📸 Записаться","when_question","primary"]]

- obj_price (send_message): "~b:Я считаю это инвестицией в себя~\n\n~qx:5 пакетов — от 15 000 ₽ (Экспресс, 1 час, 15 фото) до 115 000 ₽ (Под ключ — со стилистом, визажистом и видео). Полный прайс покажу следующим шагом.~\n\nЕсть рассрочка через банк, можно по задатку 6 000 ₽" + [["💼 Показать пакеты","when_question","primary"],["← Назад","objections_menu"]]

- obj_time (send_message): "~b:По времени всё гибко~\n\n~i:Экспресс~ — 1 час съёмки, фото за 14 дней.\n~i:Лайт/Комфорт~ — съёмка до результата (~1.5-3 часа), фото 7-14 дней.\n~i:Под ключ~ — 3 часа полного процесса, фото уже на следующий день.\n\nВыбираешь под свою скорость." + [["← Назад","objections_menu"],["📸 Хорошо, дальше","when_question","primary"]]

- obj_clothes (send_message): "~b:Образы не должны быть проблемой~\n\n~qx:Перед съёмкой я присылаю подробные рекомендации с примерами — что точно работает на твою фигуру, какие цвета в кадре звучат, что НЕ брать. По запросу могу подключить стилиста (входит в пакет 'Под ключ').~\n\nА ещё у меня есть подборка образов прямо в этом боте — её ты уже видела ~emoji:5368324170671202286|✨~" + [["← Назад","objections_menu"],["📸 Записаться","when_question","primary"]]

- obj_kids (send_message): "~b:Дети — моя любимая часть~\n\n~i:Снимаю семьи с детьми любого возраста.~ Беру быстрый темп, делаю много кадров между «позами» — обычно лучшие фотки получаются именно в эти моменты живой жизни.\n\n~qx:Совет: не нагружайте день ребёнка перед съёмкой. И возьмите его любимую игрушку — для расслабления.~" + [["← Назад","objections_menu"],["📸 Записаться","when_question","primary"]]

Все ответы ТЁПЛЫЕ, без продаж в лоб. Используй ~qx:..~ для длинных абзацев.

Всего 6 узлов. ВЕРНИ ТОЛЬКО МАССИВ.""",
        "next_hint": "when_question",
    },
    {
        "name": "АКТ 6+7 — CTA с пакетами и доп.триггеры",
        "task": """Создай финальный массив узлов для актов 6 и 7.

УЗЛЫ:
- when_question (ask_question, variable:"when", text:"~b:Когда хочется снимать?~ ~emoji:5368324170671202289|📸~", inline:true) с 4 вариантами:
  "🔥 Срочно — в ближайшие 2 недели" (value:"urgent")
  "🌿 В этом месяце" (value:"this_month")
  "🌸 Через 1-2 месяца" (value:"in_1_2_months")
  "🤔 Просто исследую пока" (value:"browsing")
  → when_switch

- when_switch (switch, variable:"when", cases:{"urgent":"path_urgent","this_month":"path_month","in_1_2_months":"path_later","browsing":"path_browse"})

- path_urgent (send_message): "~b:Понимаю — срочно~ ~emoji:5368324170671202290|👑~\n\n~i:У меня есть пара слотов на следующие 2 недели.~ Пиши прямо сейчас — обсудим даты и подберём студию ASAP" + [["💬 Написать СЕЙЧАС","final_cta","success","https://t.me/mzaugolnikova"], ["📋 Сначала посмотреть пакеты","final_cta","primary"]]

- path_month (send_message): "~b:В этом месяце — отлично~\n\nВ ~qx:За раннее бронирование (за 3+ недели) я делаю скидку 10% на любой пакет. Просто упомяни этот бот при первом сообщении.~" + [["📋 К пакетам","final_cta","primary"], ["💬 Написать сразу","final_cta","success"]]

- path_later (send_message): "~b:Через 1-2 месяца — отлично, можно подготовиться~\n\nМогу прислать ~i:чек-лист подготовки к съёмке~ + забронировать твою дату уже сейчас (задаток всего 6 000 ₽)." + [["📋 Пакеты","final_cta","primary"], ["💬 Написать","final_cta","success"]]

- path_browse (send_message): "~b:Ок, исследуй спокойно~ ~emoji:5368324170671202287|🌿~\n\n~qx:Если решишь — я здесь. PDF с твоей подборкой уже у тебя. Можешь вернуться к /start в любое время и собрать новую.~" + [["📋 Показать пакеты на всякий","final_cta","primary"], ["💬 Контакты","external_link"]]

- final_cta (send_message): полный CTA с заголовком "~b:📸 ПАКЕТЫ СЪЁМКИ — выбери свой~ ~emoji:5368324170671202290|👑~" и текстом-каталогом ВСЕХ 5 пакетов:

"~b:✨ Экспресс — 15 000 ₽~
• Консультация и подбор студии
• 1 час съёмки
• 15 фото в цвете и ч/б за 14 дней
~i:Исходники jpg — +6 000 ₽~

~b:🌿 Лайт — 25 000 ₽~
• Подбор студии (аренда отдельно)
• Съёмка до результата
• 40 фото + все исходники
• 14 рабочих дней

~b:💫 Комфорт — 35 000 ₽~
• Съёмка до результата
• 80 фото + все исходники
• Готово за 7 рабочих дней

~b:👑 Под ключ — 115 000 ₽~
• 3 часа аренды студии (включено)
• Стилист, визаж, причёска, 3 образа
• Видео для Reels/Stories
• 100 фото + исходники
• Готово на СЛЕДУЮЩИЙ день

~b:🎥 Репортаж — от 8 000 ₽/час~
От 2 часов. 200+ фото за неделю в Google Drive.

~qx:Бронирование по задатку 6 000 ₽. Перенос даты — до 2 раз. Стиль естественный, лёгкая ретушь без пластики.~"

Кнопки:
[["💬 Написать Марине","external_link","success"]]
[["🌐 Сайт","https://zaugolnikova.ru/"]] — это url-кнопка
[["🔄 Пройти подбор ещё раз","start","default"]]
→ next: end_flow

- external_link (send_message): "Пиши Марине напрямую: @mzaugolnikova ~emoji:5368324170671202288|💫~" + url-кнопка t.me + "← К пакетам" next:final_cta

- end_flow (end, params:{})

# АКТ 7 — Дополнительные триггеры (отдельные ветки)
- trg_price (text_match, pattern:"цена", mode:"contains") → final_cta
- trg_reviews (text_match, pattern:"отзывы", mode:"contains") → reviews_block
- trg_portfolio (text_match, pattern:"портфолио", mode:"contains") → portfolio_link
- portfolio_link (send_message): "Портфолио Марины: ~link:https://zaugolnikova.ru/|zaugolnikova.ru~ ~emoji:5368324170671202289|📸~" + кнопка "📸 К пакетам" next:final_cta

Всего ~12 узлов. ВЕРНИ ТОЛЬКО МАССИВ.""",
        "next_hint": None,
    },
]


def call(messages: list[dict], max_tokens: int = 12000, timeout: float = 300.0) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "content-type": "application/json"}
    payload = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    with httpx.Client(timeout=timeout) as cli:
        r = cli.post(f"{BASE.rstrip('/')}/v1/chat/completions", headers=headers, json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]


def extract_json_array(text: str) -> list:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    if m:
        return json.loads(m.group(1))
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start:end+1])
    raise ValueError("Не нашёл JSON-массив")


all_nodes: list[dict] = []
for i, part in enumerate(PARTS, 1):
    print(f"\n=== ЧАСТЬ {i}/{len(PARTS)}: {part['name']} ===")
    messages = [
        {"role": "system", "content": COMMON},
        {"role": "user", "content": part["task"]},
    ]
    for attempt in range(1, 4):
        print(f"  попытка {attempt}/3 ...")
        try:
            text = call(messages, max_tokens=12000, timeout=300)
            nodes = extract_json_array(text)
            print(f"  ✓ получено узлов: {len(nodes)}")
            all_nodes.extend(nodes)
            break
        except Exception as e:
            print(f"  ✗ {str(e)[:200]}")
            if attempt >= 3:
                print(f"  СКИП части {i}")

print(f"\n=== ВСЕГО УЗЛОВ: {len(all_nodes)} ===")

# Размещаем по сетке (если AI не дал position)
for idx, n in enumerate(all_nodes):
    if "position" not in n or not isinstance(n.get("position"), dict):
        n["position"] = {"x": 80 + (idx % 6) * 280, "y": 80 + (idx // 6) * 200}

flow = {
    "name": "Большая встреча со светом",
    "description": "Грандиозная воронка от Марины Заугольниковой — 7 актов, deep-link атрибуция, switch-персонализация, отзывы, FAQ и финальный CTA со всеми 5 пакетами.",
    "graph": {"nodes": all_nodes, "edges": []},
}

# Валидируем
issues = validate_graph(flow["graph"])
summ = summary(issues)
print(f"\nВалидатор: ❗{summ['error']} ⚠{summ['warning']} 💡{summ['hint']}")
errors = [i for i in issues if i["level"] == "error"]
for e in errors[:20]:
    print(f"  - {e['code']} в {e.get('node_id')}: {e['message']}")

out = Path("docs/flows/grand_funnel.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
size_lines = len(out.read_text().splitlines())
print(f"\n✅ Сохранено: {out} ({size_lines} строк, {len(all_nodes)} узлов)")
