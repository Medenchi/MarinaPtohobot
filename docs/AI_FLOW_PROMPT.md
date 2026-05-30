# 🤖 Промпт для генерации флоу нейросетью

Скопируй ВСЁ что ниже от первой до последней строки между маркерами
`====BEGIN PROMPT====` и `====END PROMPT====`, вставь в Claude / ChatGPT /
Gemini, потом допиши свой запрос в конце (после строки «### Задача»).

Промпт уже содержит:
- описание всех блоков и их параметров
- правила валидатора
- список таблиц в БД с реальными колонками
- список всех значений категорий (поводы, цвета и т.д.)
- шаблоны типовых паттернов (опросник → выборка → карусель → PDF)
- запрет на типовые ошибки (tel-кнопки, висячие next, дубли id)
- требование вернуть **ровно один валидный JSON**

Готовый файл импортируй: `/admin → Импорт → JSON-файл`.

---

```
====BEGIN PROMPT====

Ты — генератор JSON-флоу для Telegram-бота фотографа Марины Заугольниковой.
Бот построен на собственном движке (aiogram 3 + Supabase). Я даю тебе
ПОЛНУЮ спецификацию формата. Твоя задача — вернуть РОВНО один валидный
JSON, без комментариев, без markdown-обёрток ```json```, без преамбулы и
эпилога. Только JSON-объект.

# Структура корневого объекта

{
  "name": "Короткое название флоу (показывается в /admin)",
  "description": "Одной строкой что делает флоу",
  "graph": {
    "nodes": [ /* массив узлов */ ],
    "edges": []
  }
}

`edges` всегда пустой массив — связи задаются через node.next и кнопки.

# Узел (node)

{
  "id": "snake_case_unique",          // string, уникален в пределах графа
  "type": "тип_блока",                // см. список ниже
  "params": { ... },                  // зависит от типа
  "next": "id_следующего_или_null",
  "position": { "x": 80, "y": 120 }   // для визуального редактора
}

# 19 типов блоков

## ТРИГГЕРЫ (точки входа, сами не исполняются — только указывают, куда идти)

### command — старт по слэш-команде
{ "type": "command", "params": { "command": "start", "keep_vars": false }, "next": "..." }
- command: без слэша, обязательное
- keep_vars: если false (default), при /start обнуляются все vars

### text_match — старт по тексту от юзера
{ "type": "text_match", "params": { "pattern": "цена", "mode": "contains" }, "next": "..." }
- mode: "exact" | "contains" | "starts_with"

## СООБЩЕНИЯ

### send_message — отправить текст
{ "type": "send_message", "params": {
    "text": "Текст с <b>HTML</b> и {{vars.имя}}",
    "parse_mode": "HTML",                  // default HTML
    "disable_preview": true,               // default true
    "buttons": [                           // опционально, inline
      [ { "text": "Кнопка 1", "next": "node_id" },
        { "text": "Сайт", "url": "https://example.com" } ],
      [ { "text": "В одиночку на 2-й ряд", "next": "another" } ]
    ],
    "reply_keyboard": [["Да", "Нет"]]      // взаимоисключающе с buttons
  }, "next": "..." }
- buttons: МАССИВ РЯДОВ массивов кнопок (list[list[dict]])
- url у кнопки должен начинаться с https:// http:// или tg:// — НЕЛЬЗЯ tel:, mailto:
- если кнопка имеет url — никогда не указывай ей next

### send_photo, send_video, send_document
Аналогично, с параметром `url` или `file` для документа.

### send_album — медиа-группа из vars
{ "type": "send_album", "params": {
    "items_var": "matched_outfits",
    "caption_template": "{{outfit.title}}"
  }, "next": "..." }
Берёт из vars[items_var] (обычно matched_outfits — результат db_query),
шлёт до 10 фото в одном сообщении.

### typing, delay
{ "type": "typing", "params": { "seconds": 1.5 }, "next": "..." }
{ "type": "delay",  "params": { "seconds": 2.0 }, "next": "..." }

## ВВОД

### ask_question — задать вопрос, ждать ответ
{ "type": "ask_question", "params": {
    "text": "Как тебя зовут?",
    "variable": "name",                    // ОБЯЗАТЕЛЬНО — без неё ответ потеряется
    "inline": true,                        // default true; false = reply-клавиатура
    "options": [                           // если пусто — ждёт свободный текст
      { "text": "💕 Любовь",   "value": "love" },
      { "text": "👨‍👩‍👧 Семья", "value": "family" }
    ]
  }, "next": "next_node" }

## ЛОГИКА

### set_variable
{ "type": "set_variable", "params": { "name": "season", "value": "{{system.season}}" }, "next": "..." }

### branch — if/else
{ "type": "branch", "params": {
    "variable": "{{vars.color}}",
    "op": "eq",                            // eq|neq|contains|not_contains|in|gt|lt|empty|not_empty
    "value": "white",
    "true_next": "node_a",
    "false_next": "node_b"
  } }
- У branch НЕТ поля next — только true_next/false_next в params

### goto — безусловный переход
{ "type": "goto", "params": { "next": "target_node" } }

### end — финал
{ "type": "end", "params": {}, "next": null }

## ДАННЫЕ

### db_query — выборка из Supabase
{ "type": "db_query", "params": {
    "table": "outfits",
    "select": "id, title, description, colors, styles, occasions, gender, outfit_images(*)",
    "filters": [
      { "column": "is_published", "op": "eq",    "value": "true" },
      { "column": "gender",       "op": "ilike", "value": "%{{vars.gender}}%" },
      { "column": "occasions",    "op": "ilike", "value": "%{{vars.occasion}}%" }
    ],
    "order_by": "sort_order",
    "descending": false,
    "limit": 30,
    "save_to": "matched_outfits"
  }, "next": "..." }
- op: eq, neq, gt, lt, gte, lte, ilike, in, is
- ilike с %{{vars.x}}% — мягкий фильтр (рекомендуется для tag-полей)
- save_to обязателен — иначе результат потеряется

### db_insert — вставить строку (например заявку)
{ "type": "db_insert", "params": {
    "table": "bookings",
    "fields": {
      "full_name": "{{vars.name}}",
      "phone": "{{vars.phone}}",
      "notes": "{{vars.notes}}",
      "payload": { "color": "{{vars.color}}", "occasion": "{{vars.occasion}}" }
    }
  }, "next": "..." }
- Для table=bookings telegram_id/username подставляются автоматически

## СПЕЦИАЛЬНЫЕ

### show_outfits_voting — карусель образов с лайками 👍/💔
{ "type": "show_outfits_voting", "params": {
    "items_var": "matched_outfits",
    "limit": 15,
    "liked_var": "liked_ids",
    "disliked_var": "disliked_ids",
    "intro": "Вот что подошло ✨ Отметь 👍/💔",
    "done_text": "Когда отметишь — нажми сюда:",
    "done_button": "✅ Готово"
  }, "next": "node_после_готово" }
Шлёт N фото-карточек, под каждой кнопки 👍/💔. Накопленные id уходят
в vars.liked_ids и vars.disliked_ids. Финальная кнопка ведёт в next.

### generate_pdf_voted — собрать PDF с разделами
{ "type": "generate_pdf_voted", "params": {
    "items_var": "matched_outfits",
    "liked_var": "liked_ids",
    "filename": "podbor.pdf",
    "caption": "Твоя подборка ✨",
    "send_now": true,
    "save_to": "pdf"
  }, "next": "..." }
Если liked_ids непустой — раздел «Понравилось» + «Может подойти».
Иначе — обычный PDF без секций.

### generate_pdf — простой PDF
{ "type": "generate_pdf", "params": {
    "items_var": "matched_outfits",
    "filename": "podbor.pdf",
    "send_now": true,
    "save_to": "pdf"
  }, "next": "..." }

### http_request — внешний API
{ "type": "http_request", "params": {
    "url": "https://api.example.com/x",
    "method": "POST",
    "headers": { "Authorization": "Bearer ..." },
    "body": { "x": "{{vars.x}}" },
    "save_to": "api_result"
  }, "next": "..." }

### handoff_to_admin — пинг владельцу бота
{ "type": "handoff_to_admin", "params": {
    "text": "Новая заявка от {{vars.name}} ({{vars.phone}})"
  }, "next": "..." }

# Шаблоны (доступные переменные)

В любом строковом params можно вставить:
- {{user.first_name}}, {{user.last_name}}, {{user.full_name}}
- {{user.username}}, {{user.id}}, {{user.language_code}}, {{user.is_premium}}
- {{vars.<любое_имя>}} — то, что записали ask_question / set_variable / db_query.save_to / generate_pdf.save_to
- {{system.season}} → "зима" | "весна" | "лето" | "осень" (по текущему месяцу)
- {{system.month}}, {{system.year}}, {{system.date}}, {{system.weekday}}

Если строка состоит ТОЛЬКО из одного токена — движок вернёт сырое значение
(список/число/объект). Это используется в branch.variable.

# Таблицы в БД

## outfits — образы (для подборки)
Колонки:
- id (int), title, description
- colors, styles, seasons, occasions, body_types, budgets, shoot_types, gender (text через запятую)
- price_hint (text, свободный, типа "от 3 500 ₽")
- external_url, pinterest_url (ссылки)
- is_published (bool)
- outfit_images(*) — массив { id, storage_path, sort_order }

## bookings — заявки
- telegram_id, telegram_username (заполняются автоматически)
- full_name, phone, preferred_date, shoot_type, notes
- payload (jsonb — любые доп. поля)
- is_read

## courses — курсы
- id, slug, title, description, storage_path, cover_path, preview_pages, is_published

## bot_users — все юзеры бота (read-only)

## outfit_categories — справочник тегов (read-only из флоу)
- kind: gender | colors | styles | seasons | occasions | body_types | budgets | shoot_types
- value: одно значение
- sort_order

# Реальные значения категорий Марины

(используй именно эти строки в options.value чтобы попадать в db_query.ilike)

gender:      женское, мужское
colors:      бежевый, белый, чёрный, серый, коричневый, молочный, оливковый, пастельный, тёмно-синий, бордовый, винный, зелёный
styles:      casual, smart casual, классика, романтика, минимализм, old money, total look, street, бохо
seasons:     весна, лето, осень, зима, межсезонье
occasions:   love-story, семейная съёмка, беременность, индивидуальная, lookbook, контент для соцсетей, репортаж, деловая, свидание, прогулка
body_types:  песочные часы, прямоугольник, груша, перевёрнутый треугольник, яблоко, plus size
budgets:     до 5к, 5–15к, 15–30к, 30–60к, 60к+
shoot_types: студия, улица, дома у клиента, природа, золотой час, зимняя на улице

# ПРАВИЛА (нарушать НЕЛЬЗЯ)

1. id уникальны в пределах графа. Никаких дублей.
2. Каждый next ссылается на существующий id или null.
3. Каждый ask_question имеет params.variable. Без неё ответ теряется.
4. Должен быть хотя бы один триггер (command или text_match) — обычно command "start".
5. Все блоки должны быть достижимы от какого-то триггера (через next или через кнопки/branch).
6. url в кнопках — только https://, http://, tg:// или t.me/. Никаких tel: или mailto:.
7. buttons — это МАССИВ РЯДОВ: [[btn1, btn2], [btn3]]. Не плоский массив.
8. branch не имеет верхнего "next" — только true_next/false_next внутри params.
9. Тексты на «ты», эмодзи умеренно, тон тёплый/деловой по контексту.
10. HTML-теги в text: <b> <i> <a href="..."> <code>. НЕ используй <br>, ставь \\n.
11. Не путай `next` (на узел в графе) и `url` (внешняя ссылка) у кнопки.
12. Для db_query по тегам через запятую — используй op="ilike" и value="%{{vars.x}}%".
13. После show_outfits_voting обязательно ставь generate_pdf_voted (либо generate_pdf).
14. В конце основного сценария — send_message с CTA + end. CTA-кнопки только с url или next.

# Типовые паттерны (используй как кирпичи)

## Паттерн 1: «Опросник по поводу → подборка → PDF»

start (command) → hello (send_message с приветом) → ask_gender → ask_occasion →
query (db_query outfits с ilike по gender и occasion) → branch_has (not_empty) →
если пусто: empty_state (send_message «ничего нет, начать заново» с кнопкой → ask_gender) →
если есть: intro (send_message «вот что подошло») → voting (show_outfits_voting) →
make_pdf (generate_pdf_voted) → cta (send_message с пакетами Марины и кнопками
«Написать», «Сайт», «Подобрать ещё» → ask_gender) → end

## Паттерн 2: «Простой бриф с сохранением заявки»

start → ask_name → ask_phone → ask_shoot_type → ask_date → ask_notes →
summary (send_message «всё верно? <данные>» с кнопками «✅ Отправить» и «🔄 Заново») →
save_booking (db_insert в bookings) → ping_marina (handoff_to_admin) →
thank_you → end

## Паттерн 3: «Меню с раскрывающимися пунктами»

start → menu (send_message с кнопками-разделами) →
для каждого раздела: detail_X (send_message с инфой + кнопкой «← В меню» → menu)

# Перед тем как вернуть JSON — самопроверка:

1. Все id уникальны? — да
2. Все next и кнопочные next ведут на существующие id или null? — да
3. У каждого ask_question есть variable? — да
4. У каждой url-кнопки url начинается с https://, http://, tg://? — да
5. Все блоки достижимы из start? — да
6. У branch нет верхнего next, только true_next/false_next? — да
7. buttons это list[list[dict]]? — да
8. JSON синтаксически валиден (запятые, кавычки)? — да

Если что-то нет — исправь и проверь снова. Только потом возвращай.

### Задача

[НАПИШИ СЮДА что должен делать флоу. Чем подробнее — тем лучше.
Например:
"Сделай флоу для подбора детских образов. Спроси возраст ребёнка
(0-3, 3-7, 7-12), пол (м/ж/неважно), повод (день рождения, ёлка,
крещение, выпускной, прогулка), цвет любимый. По итогам сделай db_query
к outfits (occasions ilike поводом, colors ilike цветом), покажи
карусель с лайками, собери PDF, в конце предложи записаться на съёмку
с кнопкой «Написать Марине» (https://t.me/mzaugolnikova)."]

====END PROMPT====
```

---

## Как пользоваться

1. **Скопируй** весь блок выше (от `====BEGIN PROMPT====` до `====END PROMPT====`).
2. Вставь в Claude / ChatGPT / Gemini.
3. В конце, где `### Задача` — опиши, какой флоу нужен. Чем конкретнее — тем меньше нейросетка нафантазирует.
4. Получишь JSON. Сохрани как файл `мой-флоу.json`.
5. Зайди в `/admin` → **Импорт** → выбери файл → должен появиться новый флоу.
6. Открой его → **🧠 AI-проверка** в шапке. Если она показывает `❗ 0 ⚠ 0 💡 0` — всё ок, можно публиковать.
7. Если есть ошибки — скопируй текст ошибки обратно в чат с нейросеткой: «исправь: dangling_next в узле ask_color». Перегенерит.

## Примеры запросов которые точно сработают

```
Сделай флоу для подбора образов на корпоратив. Спроси формат
(деловой / новогодний / летний), цвет, бюджет (до 5к, 5-15к, 15к+).
Подбери из outfits по occasions ilike "%деловая%" или соответствующему
поводу. Покажи карусель с лайками. Собери PDF. В конце предложи
записаться на съёмку.
```

```
Сделай флоу-меню «О Марине». Кнопки: «Этапы съёмки», «Пакеты»,
«Условия», «Контакты». Каждая открывает отдельное сообщение с инфой
и кнопкой «← В меню». Тексты возьми из брифа Марины (есть в системном
промпте). В конце каждого раздела ещё кнопка «✍️ Написать»
с url https://t.me/mzaugolnikova.
```

```
Сделай флоу-викторину «Какой ты типаж по стилю?». 5 вопросов с
закрытыми ответами (по 3 варианта в каждом). По набранным значениям
через branch выведи один из 4 типажей (минимализм / классика / бохо /
casual) и для каждого типажа сделай db_query к outfits с
styles ilike "%типаж%" + покажи топ-5 через send_album.
```

---

## 🆕 Дополнение: 30+ новых блоков (aiogram 3.28)

Эти блоки тоже доступны движку — можешь использовать их в `type`:

### Текст / форматирование
- **`send_heading`** — большой заголовок (`text`, `icon`, `level: 1|2|3`)
- **`send_quote`** — Telegram blockquote (`text`, `author`, `expandable: bool`)
- **`send_checklist`** — список с галочками (`title`, `items: list[str]`, `checked: list[int]`)
- **`send_numbered_list`** — нумерованный список (`title`, `items: list[str]`)
- **`send_kv_table`** — таблица ключ-значение (`title`, `rows: {имя: значение}`)
- **`send_with_preview`** — сообщение с превью ссылки (`text`, `url`, `above_text: bool`, `large: bool`)

### Медиа
- **`send_sticker`** (`sticker_id: file_id`)
- **`send_voice`** (`url`) / **`send_audio`** (`url`, `title`, `performer`)
- **`send_video_note`** (`url`) — круглое видео
- **`send_location`** (`latitude`, `longitude`)
- **`send_venue`** (`latitude`, `longitude`, `title`, `address`) — место с адресом
- **`send_contact`** (`phone`, `first_name`, `last_name`)
- **`send_dice`** (`emoji: 🎲🎯🏀⚽🎳🎰`, `save_to`) — анимированный бросок
- **`send_poll`** (`question`, `options`, `anonymous`, `multiple`)
- **`send_chat_action`** (`action: typing/upload_photo/record_voice/...`, `seconds`)

### Интерактив (aiogram 3.17+, 3.28)
- **`send_copy_button`** (`text`, `button_text`, `copy_text`) — кнопка `CopyTextButton`, копирует в буфер
- **`send_webapp_button`** (`text`, `button_text`, `url: https://`) — открывает Mini App через `WebAppInfo`
- **`send_share_button`** (`text`, `button_text`, `share_text`) — t.me/share/url
- **`send_rating`** (`text`, `scale: 1-10`, `save_to`) — звёздочки, результат в vars

### Логика
- **`random_branch`** (`choices: ["node_a", "node_b", "node_c"]`) — случайно один
- **`switch`** (`variable`, `cases: {"love": "node_a", "family": "node_b"}`, `default`)
- **`increment_var`** (`name`, `delta`)
- **`append_to_list`** (`name`, `value`)
- **`regex_extract`** (`source: "{{vars.input}}"`, `pattern`, `save_to`)
- **`math_eval`** (`expression: "{{vars.a}} + {{vars.b}}"`, `save_to`)
- **`time_window`** (`start_hour`, `end_hour`, `inside_next`, `outside_next`)
- **`schedule_branch`** (`weekday_next`, `weekend_next`)

### Данные
- **`db_update`** (`table`, `where: {col: val}`, `fields: {col: val}`)
- **`db_count`** (`table`, `filters`, `save_to`)

### Контент-специфика
- **`send_outfit_card`** (`items_var`, `index`) — карточка одного образа с кнопкой «Купить»
- **`send_outfit_grid`** (`items_var`) — медиа-группа до 10
- **`show_random_outfit`** (`items_var`) — рандом один из списка

### Примеры использования

```jsonc
// Чек-лист подготовки к съёмке
{
  "id": "preparation",
  "type": "send_checklist",
  "params": {
    "title": "Что взять на съёмку",
    "items": ["Паспорт", "Образы (2-3 шт)", "Аксессуары", "Хорошее настроение"]
  },
  "next": "ask_next"
}

// Случайный образ дня
{
  "id": "daily_outfit",
  "type": "show_random_outfit",
  "params": { "items_var": "all_outfits" },
  "next": "end"
}

// Звёздочный рейтинг бота
{
  "id": "rate_us",
  "type": "send_rating",
  "params": { "text": "Оцени бота:", "scale": 5, "save_to": "user_rating" },
  "next": "thanks"
}

// Switch по типу съёмки
{
  "id": "by_type",
  "type": "switch",
  "params": {
    "variable": "shoot_type",
    "cases": {
      "love": "love_branch",
      "family": "family_branch",
      "lookbook": "lookbook_branch"
    },
    "default": "default_branch"
  }
}
```

---

## 🆕 v2: Лёгкая разметка `~tag:...~`

Вместо HTML в любом строковом `params` можно писать:

| Запись | Что значит |
|---|---|
| `~b:текст~` | жирный |
| `~i:текст~` | курсив |
| `~u:текст~` | подчёркнутый |
| `~s:текст~` | зачёркнутый |
| `~code:текст~` | моноширинный |
| `~spoiler:текст~` | скрытый текст |
| `~q:текст~` | цитата |
| `~qx:длинный текст~` | раскрывающаяся цитата |
| `~link:https://x.com\|написать~` | ссылка |
| `~emoji:5368324170671202286\|⭐~` | Premium-эмодзи с fallback |

⚠ В тексте inline-кнопок (`buttons[].text`) разметку и premium-эмодзи
Telegram НЕ парсит. Эмодзи можно ставить как обычный текст.

## 🆕 v2: ещё блоки

- **`delete_last_message`** (`count: 1`) — стереть последние N сообщений бота
- **`clear_chat`** — стереть все сообщения бота за сессию
- **`ask_poll`** (`question`, `options`, `variable`, `multiple: bool`) — нативный TG-опрос вместо inline-кнопок, результат → vars
- **`set_bot_name`** / **`set_bot_description`** / **`set_bot_short_description`** / **`set_bot_avatar`** — бот меняет своё имя/описание/аватарку
- **`send_colored_buttons`** (`text`, `buttons` с полем `color: green|red|yellow|blue|purple|orange|black|white`) — эмулирует цвета через эмодзи-кружки

## 🆕 v2: ограничения, о которых нужно знать

1. **Цветные кнопки в обычных чатах НЕ работают** в Telegram API. `send_colored_buttons` использует эмодзи в начале текста.
2. **Premium-эмодзи в `text` кнопок** Telegram игнорирует. Только в тексте сообщения.
3. **Удаление сообщений бота** — только младше 48 часов.
4. **`ask_poll`** — `is_anonymous` принудительно `false` (иначе нет `poll_answer`).

---

## 🆕 v3: Цветные кнопки и Premium-эмодзи (НАТИВНО)

В любой кнопке (`send_message.buttons[]`, `send_colored_buttons.buttons[]` и т.п.) можно использовать:

* **`style`**: `primary` | `success` | `danger` | `warning` | `secondary`
  — реальные цветные кнопки Telegram (видно всем без подписок)
* **`icon_custom_emoji_id`**: числовой ID premium-эмодзи (видно всем,
  если у владельца бота есть Telegram Premium)

```jsonc
{
  "text": "Купить Premium",
  "style": "success",
  "icon_custom_emoji_id": "5431843232120012345",
  "next": "buy"
}
```

Эти поля приоритетнее старого `color: "green"` (который эмулировал
через эмодзи-кружок 🟢).
