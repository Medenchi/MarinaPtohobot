# Формат JSON-графа для конструктора бота

Это полная спецификация структуры, которую понимает рантайм бота
(`backend/app/bot/runtime/`) и которую сохраняет конструктор
(`frontend/src/pages/admin/Constructor.tsx`) в колонку `bot_flows.graph`.

Всё валидируется AI-валидатором (`validator.py` / `validator.ts`) —
ошибки видны в шапке конструктора (`❗ ⚠ 💡`) и через кнопку
«🧠 AI-проверка» в `/builder`.

---

## 1. Корень графа

```jsonc
{
  "nodes": [ /* массив блоков, см. ниже */ ],
  "edges": []                 // опционально, не используется рантаймом
                              //  — нужны только для совместимости/визуала
}
```

В `bot_flows` это поле — `jsonb`. Колонки:

| колонка            | тип       | смысл                                                  |
|--------------------|-----------|--------------------------------------------------------|
| `id`               | uuid      | первичный ключ                                         |
| `name`             | text      | имя флоу                                               |
| `description`      | text      | заметка для админа                                     |
| `graph`            | jsonb     | сам граф (см. ниже)                                    |
| `is_published`     | bool      | бот гоняет только published-флоу                       |
| `published_at`     | timestamp |                                                        |
| `version`          | int       | автоинкремент при `updateFlow`                         |

---

## 2. Узел (`node`)

```jsonc
{
  "id": "ask_name",                  // string, уникальный в пределах графа
  "type": "ask_question",            // тип блока — см. таблицу в §4
  "params": { ... },                 // параметры конкретного блока
  "next": "ask_phone",               // id следующего блока ИЛИ null
  "position": { "x": 320, "y": 80 }  // ОПЦИОНАЛЬНО — координаты на холсте
}
```

* `id` — латиница / цифры / `_`. Регистр важен. Дубликаты → ошибка
  `duplicate_id`.
* `next: null` означает «после этого блока флоу заканчивается».
* `position` пишется автоматически когда юзер двигает блок мышкой
  на канве. Если позиции нет — канвас разложит блоки сеткой 4×N.

---

## 3. Триггеры (точки входа)

Триггерные узлы **не выполняются** — они только говорят движку: «когда
юзер сделал X, начни флоу с узла, на который смотрит `next`».

### `command` — старт по слэш-команде

```jsonc
{
  "id": "trg_start",
  "type": "command",
  "params": {
    "command": "start",        // без слэша
    "keep_vars": false         // true → НЕ сбрасывать собранные vars при /start
  },
  "next": "hello"
}
```

> ⚠ Если у `/start` стоит `keep_vars: false` (по умолчанию), движок
> обнуляет `session.vars`. Это правильно для опросников «заново».

### `text_match` — старт по тексту

```jsonc
{
  "id": "trg_pricing",
  "type": "text_match",
  "params": {
    "pattern": "цена",
    "mode": "contains"         // exact | contains | starts_with
  },
  "next": "send_pricing"
}
```

---

## 4. Все типы блоков

| `type`             | что делает                                                                | основные `params`                                                                 | имеет `next` |
|--------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------|--------------|
| `send_message`     | отправить текст (с inline-кнопками или reply-клавиатурой)                 | `text`, `parse_mode`, `buttons`, `reply_keyboard`, `disable_preview`              | да           |
| `send_photo`       | отправить фото по URL                                                     | `url` / `photo`, `caption`, `buttons`                                             | да           |
| `send_album`       | альбом картинок (берёт `vars.matched_outfits`)                            | `items_var`, `caption_template`                                                   | да           |
| `send_document`    | файл                                                                      | `file` / `url`, `caption`, `filename`                                             | да           |
| `send_video`       | видео                                                                     | `url`, `caption`                                                                  | да           |
| `typing`           | «печатает…» на N сек                                                      | `seconds`                                                                         | да           |
| `delay`            | sleep                                                                     | `seconds` (0.1–30)                                                                | да           |
| `ask_question`     | задаёт вопрос, **пауза** до ответа, ответ → в `vars[variable]`            | `text`, `variable`, `options`, `inline`                                           | да           |
| `set_variable`     | присвоить переменной значение (можно шаблон)                              | `name`, `value`                                                                   | да           |
| `branch`           | if/else по переменной                                                     | `variable`, `value`, `op`, `true_next`, `false_next`                              | условно      |
| `goto`             | прыжок в другой узел                                                      | `next`                                                                            | да           |
| `end`              | финал, чистит `current_node_id`                                           | —                                                                                 | нет          |
| `db_query`         | SELECT из supabase в `vars`                                               | `table`, `select`, `filters`, `save_to`, `limit`, `order`                         | да           |
| `db_insert`        | INSERT (например, в `bookings`)                                           | `table`, `fields` (kv), `save_to`                                                 | да           |
| `generate_pdf`     | сгенерить PDF подборки                                                    | `items_var`, `filename`, `caption`, `send_now`, `save_to`                         | да           |
| `http_request`     | внешний API                                                               | `url`, `method`, `headers`, `json`, `save_to`                                     | да           |
| `handoff_to_admin` | переслать заявку владельцу бота в Telegram                                | `text` (template)                                                                 | да           |

### `ask_question` — главное про опросники

```jsonc
{
  "id": "ask_shoot_type",
  "type": "ask_question",
  "params": {
    "text": "Какой формат съёмки тебе ближе?",
    "variable": "shoot_type",          // ОБЯЗАТЕЛЬНО — без этого валидатор ругнётся
    "inline": true,                    // true → inline-кнопки, false → reply-клавиатура
    "options": [
      { "text": "💕 Лав-стори",      "value": "love"    },
      { "text": "👨‍👩‍👧 Семейная",      "value": "family"  },
      { "text": "🤰 Беременность",  "value": "pregnancy" },
      { "text": "👩 Индивидуальная", "value": "solo"    }
    ]
  },
  "next": "ask_date"
}
```

* `value` — то, что попадёт в `vars.shoot_type` при клике.
* Если `options` пустой — бот ждёт **свободный текст** от пользователя,
  и пишет его в `vars[variable]`.
* `inline: false` рисует Reply-клавиатуру под текстовым полем.

### `send_message` с inline-кнопками

```jsonc
{
  "id": "menu",
  "type": "send_message",
  "params": {
    "text": "Что подобрать?",
    "buttons": [
      [
        { "text": "📋 Меню",   "next": "show_menu" },
        { "text": "📞 Связь", "url":  "https://t.me/marina_photo" }
      ],
      [
        { "text": "🛍 Образы", "next": "show_outfits", "value": "outfits" }
      ]
    ]
  },
  "next": null
}
```

Кнопка — либо `next` (переход на узел), либо `url` (открывает ссылку).

### `branch` — условные переходы

```jsonc
{
  "id": "if_studio",
  "type": "branch",
  "params": {
    "variable": "{{vars.location}}",
    "op": "eq",                        // eq | neq | contains | not_contains | in | gt | lt | empty | not_empty
    "value": "studio",
    "true_next":  "studio_brief",
    "false_next": "outdoor_brief"
  }
}
```

### `db_insert` — записать заявку

```jsonc
{
  "id": "save_booking",
  "type": "db_insert",
  "params": {
    "table": "bookings",
    "fields": {
      "full_name":      "{{vars.name}}",
      "phone":          "{{vars.phone}}",
      "shoot_type":     "{{vars.shoot_type}}",
      "preferred_date": "{{vars.date}}",
      "notes":          "{{vars.notes}}",
      "payload": {
        "format":   "{{vars.format}}",
        "people":   "{{vars.people}}",
        "mood":     "{{vars.mood}}",
        "refs":     "{{vars.refs}}"
      }
    }
  },
  "next": "thank_you"
}
```

> `telegram_id` и `telegram_username` для `bookings` автоматически
> подставляются движком — можно их не указывать в `fields`.

### `handoff_to_admin` — пинг владельцу

```jsonc
{
  "id": "ping_marina",
  "type": "handoff_to_admin",
  "params": {
    "text": "🆕 Новая заявка от {{vars.name}}\nТип: {{vars.shoot_type}}\nДата: {{vars.date}}\nТел: {{vars.phone}}"
  },
  "next": "thank_you"
}
```

Отправляет сообщение на `BOT_OWNER_TELEGRAM_ID`.

---

## 5. Шаблоны и переменные

В любом строковом `params` можно использовать токены:

| токен                          | что подставится                              |
|--------------------------------|----------------------------------------------|
| `{{user.first_name}}`          | имя из Telegram                              |
| `{{user.username}}`            | @username (без `@`)                          |
| `{{user.full_name}}`           | полное имя                                   |
| `{{user.id}}`                  | telegram id                                  |
| `{{user.language_code}}`       | `ru`, `en` и т.д.                            |
| `{{user.is_premium}}`          | bool                                         |
| `{{vars.<имя>}}`               | любое, что ранее записал `ask_question` / `set_variable` |

Если токен — единственное содержимое строки, рантайм вернёт **сырое
значение** (например, список — останется списком, число — числом).
Это используется, например, в `branch.variable`.

---

## 6. Правила валидатора (что ловит «🧠 AI-проверка»)

| код               | уровень     | что значит                                                        |
|-------------------|-------------|-------------------------------------------------------------------|
| `no_trigger`      | ❗ error    | в графе нет ни `command`, ни `text_match`                          |
| `duplicate_id`    | ❗ error    | повторяющийся `id`                                                 |
| `dangling_next`   | ❗ error    | `next` указывает на несуществующий узел                            |
| `no_variable`     | ❗ error    | `ask_question` без `variable` — ответ потеряется                   |
| `dangling_button` | ❗ error    | кнопка ссылается на несуществующий узел                            |
| `empty_text`      | ⚠ warning  | `send_message` с пустым текстом                                    |
| `empty_question`  | ⚠ warning  | `ask_question` без `text`                                          |
| `no_buttons`      | ⚠ warning  | блок с кнопками без кнопок                                         |
| `self_loop`       | ⚠ warning  | узел ссылается сам на себя                                         |
| `unreachable`     | 💡 hint    | блок не достижим ни от одного триггера                             |

Бот не публикует флоу с ошибками? — публикует, но в шапке конструктора
видно красный счётчик. Лучше прогнать «AI-проверку» перед публикацией.

---

## 7. Чек-лист «хорошего» опросника

1. Один триггер `command` с `/start` → ведёт на приветствие.
2. Каждый `ask_question` имеет **уникальную** `variable` и заполненный `text`.
3. Закрытые вопросы дают `options` с понятными `value` (используй
   латиницу — удобнее в `branch` и при экспорте в `bookings.payload`).
4. В конце — `db_insert` в `bookings` (чтобы заявка попала Марине в
   `/mama/bookings`) **+** `handoff_to_admin` (чтобы пришло уведомление
   в Telegram владельцу).
5. Финальный `send_message` с благодарностью и `next: null`.
6. Никаких висящих `next` — прогоняй валидатор.

---

## 8. Готовые шаблоны (`blockTemplates.ts`)

В конструкторе кнопка **🧠 Шаблоны** → панель из 12 готовых под-графов
под флоу Марины. Клик и нужные узлы появляются справа от твоего графа
с уникальными id (`ask_occasion_1`, `pdf_outfits_1` и т.д.) — останется
только перетянуть стрелку из своего блока к первому новому.

| Группа | Шаблон | Что внутри |
|---|---|---|
| Поводы съёмок | `occasion_picker` | `ask_question` с 7 поводами Марины (love-story, семейная, беременность, индивидуальная, lookbook, контент, репортаж) |
| Образы | `outfits_by_occasion_pack` | `ask_question` повод → `db_query outfits filter occasions ilike '%{{vars.occasion}}%'` → `send_album` |
| Образы | `outfits_pdf_pack` | `generate_pdf` из `matched_outfits` с водяным знаком |
| Курсы | `courses_list_pack` | `db_query` published-курсов → `send_message` со ссылкой на каталог |
| Пакеты | `package_express` | Карточка «Экспресс — 15 000 ₽» |
| Пакеты | `package_light` | «Лайт — 25 000 ₽» |
| Пакеты | `package_comfort` | «Комфорт — 35 000 ₽» |
| Пакеты | `package_turnkey` | «Под ключ — 115 000 ₽» |
| Пакеты | `package_reportage` | «Репортаж — от 8 000 ₽/час» |
| Пакеты | `packages_menu` | Меню всех 5 пакетов: одно сообщение с кнопками + 5 раскрывающихся карточек с кнопкой «← к пакетам» |
| Контакты | `contacts_card` | Карточка контактов Марины (тел, e-mail, ИНН) |
| Контакты | `preparation_stages` | Этапы подготовки: бриф → локация → образы → напоминание |
| Контакты | `important_terms` | Бронь, ретушь, исходники, формат — текст из брифа |

Все тексты дословно из брифа Марины. Если нужно поправить — открой файл
`frontend/src/lib/blockTemplates.ts` и измени там.

---

## 9. Категории образов (`outfit_categories`)

Эти **тэги** — то, что Марина видит в чипсах при редактировании образа.
Управляются админом в `/admin/categories`. Хранятся в таблице
`outfit_categories(kind, value, sort_order)`, RLS — public read /
admin write.

`kind` — один из:
`colors`, `styles`, `seasons`, `occasions`, `body_types`, `budgets`,
`shoot_types`.

В образах эти теги по-прежнему лежат в текстовых колонках
`outfits.colors/styles/...` через запятую — никаких миграций существующих
данных не нужно.

В `db_query` фильтрах удобно использовать оператор `ilike`:

```jsonc
{
  "type": "db_query",
  "params": {
    "table": "outfits",
    "select": "*, outfit_images(*)",
    "filters": [
      { "column": "occasions", "op": "ilike", "value": "%{{vars.occasion}}%" },
      { "column": "is_published", "op": "eq", "value": "true" }
    ],
    "order_by": "sort_order",
    "limit": 10,
    "save_to": "matched_outfits"
  }
}
```

---

## 10. Гид по «лёгкому и интуитивному» форматированию (aiogram 3.28)

### Базовый HTML — то что точно работает

```html
<b>Жирный</b>
<i>Курсив</i>
<u>Подчёркнутый</u>
<s>Зачёркнутый</s>
<code>моноширинный</code>
<a href="https://example.com">ссылка</a>
<tg-spoiler>спойлер</tg-spoiler>
<blockquote>цитата</blockquote>
<blockquote expandable>раскрывающаяся цитата (Bot API 7.5+)</blockquote>
```

### Что НЕ работает в Telegram
- `<br>` — используй `\n`
- `<p>`, `<div>`, `<span>` — игнорируются (или ошибка)
- `<h1>`, `<h2>` — нет. Делай жирным
- Вложенный `<a>` внутрь `<b>` или наоборот — может ломаться, используй один уровень
- `<img>` — нет, картинку отправляй через `send_photo`

### Эмодзи как «иконки секций»
Лучше всего — одиночные эмодзи в начале абзаца:
- 📸 для фото / съёмок
- 💼 для пакетов / услуг
- 📋 для этапов / списков
- 📜 для условий / правил
- ✨ 🌿 💫 👑 🎥 для акцентов
- ❗ ⚠ 💡 ✅ для статусов

### Premium-эмодзи (Bot API 9.4+ через aiogram 3.24+)
Доступно в `KeyboardBuilder.button(icon_custom_emoji_id=...)` — но в текущем
движке мы не используем (премиум-эмодзи завязаны на бизнес-аккаунты).

### Кнопки: лёгкие правила
- **Внешняя ссылка** → `{ "text": "Сайт", "url": "https://..." }`
- **Переход внутри флоу** → `{ "text": "Дальше", "next": "node_id" }`
- **Копирование текста в буфер** → используй блок `send_copy_button`
- **Запуск Mini App** → используй блок `send_webapp_button`
- **Звонок** (`tel:...`) → Telegram НЕ принимает, не вставляй
- **Email** (`mailto:...`) → тоже не принимает; делай `send_copy_button` для email

### Длинные сообщения
Telegram максимум **4096 символов** в одном сообщении. Если флоу выводит
больше — разбей на несколько `send_message` подряд.

---

## 11. ✨ Лёгкая разметка `~tag:...~`

Чтобы не писать руками HTML, движок поддерживает свой лёгкий синтаксис.
Он применяется автоматически ко всем строковым `params`. Под капотом
конвертируется в HTML, который Telegram умеет.

| Что хочешь | Как написать | Результат |
|---|---|---|
| Жирный | `~b:текст~` | `<b>текст</b>` |
| Курсив | `~i:текст~` | `<i>текст</i>` |
| Подчёркнутый | `~u:текст~` | `<u>текст</u>` |
| Зачёркнутый | `~s:текст~` | `<s>текст</s>` |
| Моноширинный | `~code:текст~` | `<code>текст</code>` |
| Спойлер | `~spoiler:текст~` | `<tg-spoiler>текст</tg-spoiler>` |
| Цитата | `~q:текст~` | `<blockquote>текст</blockquote>` |
| Раскрывающаяся цитата | `~qx:длинный текст~` | `<blockquote expandable>...</blockquote>` |
| Ссылка | `~link:https://t.me/x\|написать~` | `<a href="...">написать</a>` |
| Premium-эмодзи | `~emoji:5368324170671202286\|⭐~` | `<tg-emoji emoji-id="...">⭐</tg-emoji>` |

### Важно про premium-эмодзи

**Видны всем юзерам бота** (включая без Premium) — при условии что у
**ВЛАДЕЛЬЦА бота** (того, кто получил токен у @BotFather) есть активная
подписка Telegram Premium. Это анти-спам ограничение от Telegram.
Если у владельца Premium нет — никто не увидит premium-эмодзи, будет
**fallback** (то, что после `|`).
Поэтому всегда указывай fallback-эмодзи, и не клади `~emoji:~` внутрь
inline-кнопки `text=` — Telegram не парсит HTML в тексте кнопок.

### AI-валидатор разметки

Конструктор автоматически проверяет:
- нечётное число `~` (незакрытая разметка) → ⚠
- неизвестный тег (`~xyz:~`) → ⚠
- ссылка с недопустимой схемой (`javascript:`, `data:`, `tel:`) → ⚠
- emoji-id не числовой → ⚠

Узлы с проблемами разметки подсвечиваются жёлтым в режиме «Карта».

---

## 12. Цветные кнопки

⚠ **Реальных цветов inline-кнопок в обычных чатах Telegram НЕ ДАЁТ.**
Параметр `style="primary"` в `KeyboardBuilder.button()` aiogram 3.25+
работает только в *Direct Messages admin keyboards* каналов
(Bot API 9.4). В обычных чатах он игнорируется.

В движке есть блок **`send_colored_buttons`**, который эмулирует цвета
через цветные кружки-эмодзи:

```jsonc
{
  "type": "send_colored_buttons",
  "params": {
    "text": "Выбери реакцию:",
    "buttons": [
      [
        { "text": "Согласен",  "color": "green",  "next": "agree" },
        { "text": "Отказ",     "color": "red",    "next": "deny" }
      ],
      [
        { "text": "Подумаю",   "color": "yellow", "next": "later" }
      ]
    ]
  }
}
```

Поддерживаемые цвета: `green` 🟢, `red` 🔴, `yellow` 🟡, `blue` 🔵,
`purple` 🟣, `orange` 🟠, `black` ⚫, `white` ⚪.

---

## 13. Удаление сообщений (борьба с наслаиванием)

Когда юзер прыгает по меню, каждое нажатие добавляет новое сообщение —
чат превращается в кашу. Решение:

- **`delete_last_message`** (`count: 1`) — удаляет N последних сообщений бота
- **`clear_chat`** — удаляет ВСЕ сообщения бота за сессию

Лимит Telegram: бот может удалить только свои сообщения младше **48 часов**.
Старее — `delete_message` вернёт ошибку, блок просто пропустит и идёт дальше.

Технически: на каждый исходящий API-вызов навешан middleware
`CollectMessageIdsMiddleware` (`backend/app/bot/runtime/middleware.py`),
который ловит `message_id` из ответа Telegram и кладёт в RAM-кэш + сессию.

---

## 14. Опрос вместо inline-кнопок

Если нужно дать юзеру выбрать без видимых кнопок (нативный TG-опрос с
голосованием), используй блок **`ask_poll`** вместо `ask_question`:

```jsonc
{
  "type": "ask_poll",
  "params": {
    "question": "Какие цвета любишь?",
    "options": ["Бежевый", "Чёрный", "Белый", "Пастельный"],
    "variable": "favorite_colors",
    "multiple": true
  },
  "next": "next_step"
}
```

Когда юзер голосует:
1. Telegram присылает update `poll_answer`
2. Engine ловит его (`@router.poll_answer()`)
3. Пишет результат в `vars[variable]` (строка или массив строк при `multiple=true`)
4. Идёт в `next`

⚠ Параметр `is_anonymous` принудительно `false` — иначе `poll_answer` не приходит.

---

## 15. Бот меняет себя

Из aiogram 3.27+ доступны:
- **`set_bot_name`** — bot.set_my_name (макс 64 символа)
- **`set_bot_description`** — то, что видно в профиле (макс 512 символов)
- **`set_bot_short_description`** — превью при шаринге (макс 120)
- **`set_bot_avatar`** — bot.set_my_profile_photo по URL

Используй в админ-флоу или по сезонам:
```jsonc
{
  "type": "set_bot_description",
  "params": {
    "description": "Новогодняя подборка образов от Марины! ❄️ Пишите /start"
  }
}
```

---

## 16. Мультибот: создание ботов ботом

Главный бот (по `BOT_TOKEN` в env) умеет «усыновлять» других ботов.

1. У @BotFather создаёшь бота, получаешь токен
2. Шлёшь главному боту: `/addbot 123456:ABC-DEF...`
3. Запись попадает в таблицу `child_bots`
4. После рестарта контейнера (Wisp → Restart) — все activated дочерние
   боты подключатся в общий dispatcher и начнут поллиться параллельно
5. Внутри хендлеров `bot: Bot` подменяется на того, кому юзер написал

Технически — `dp.start_polling(*bots)` (aiogram 3.x).

Для управления через веб-админку — таблица `child_bots`:
```sql
select id, bot_username, display_name, is_enabled, flow_id from child_bots;
```

Если у бота своя ветка — указываешь `flow_id` (UUID из `bot_flows`),
тогда он гоняет именно этот флоу, а не общий published.

---

## 17. 🎨 Цветные кнопки и Premium-эмодзи (нативно)

Через aiogram 3.28 → Telegram Bot API 9.4 в `InlineKeyboardButton` есть
два **настоящих** поля, поддерживаемых в обычных чатах:

### `style` — цвет кнопки

Принимает: `primary` (синяя), `success` (зелёная), `danger` (красная),
`warning` (жёлтая), `secondary` (серая). Видно ВСЕМ пользователям без
каких-либо подписок.

```jsonc
{
  "type": "send_message",
  "params": {
    "text": "Подтверди операцию:",
    "buttons": [
      [
        { "text": "Да",  "style": "success", "next": "confirm" },
        { "text": "Нет", "style": "danger",  "next": "cancel"  }
      ],
      [
        { "text": "Позже", "style": "secondary", "next": "later" }
      ]
    ]
  }
}
```

### `icon_custom_emoji_id` — Premium-эмодзи

Числовой ID кастомного эмодзи. Получить можно так: переслать эмодзи
@ConvertEmojiBot, скопировать `custom_emoji_id`.

⚠ **Важно**: иконка отобразится у всех пользователей (включая без Premium),
**только если у ВЛАДЕЛЬЦА бота (твоего аккаунта с токеном) есть Telegram Premium**
ИЛИ для бота куплены юзернеймы на Fragment. Иначе TG молча проигнорирует
поле.

```jsonc
{
  "type": "send_message",
  "params": {
    "text": "Меню профиля:",
    "buttons": [[
      {
        "text": "Личный кабинет",
        "style": "primary",
        "icon_custom_emoji_id": "5431843232120012345",
        "next": "profile"
      }
    ]]
  }
}
```

Эти поля поддерживаются в:
- `send_message.buttons`
- `ask_question.options` (если будут указаны явно)
- `send_colored_buttons.buttons`
- любых других местах, где есть build_inline

---

## 18. 🧰 Тулбар форматирования в конструкторе

В Constructor для всех полей-textarea теперь работает компонент
**`FormattedTextArea`** с панелью кнопок:

| Кнопка | Что вставляет |
|---|---|
| **B** | оборачивает выделение в `~b:...~` |
| **I** | `~i:...~` |
| **U** | `~u:...~` |
| **S** | `~s:...~` |
| **Code** | `~code:...~` |
| **EyeSlash** | `~spoiler:...~` |
| **Quotes** | `~q:...~` или `~qx:...~` (раскрывающаяся) |
| **Link** | спрашивает URL и текст → `~link:url\|text~` |
| **Smiley** | спрашивает ID Premium-эмодзи и fallback → `~emoji:id\|⭐~` |
| **{{}}** | dropdown с готовыми токенами {{user.first_name}}, {{system.season}} и т.д. |

Если выделен текст — оборачивает его. Если нет — вставляет шаблон и
ставит курсор внутрь.

---

## 19. 🤖 Веб-BotFather — управление дочерними ботами

Открой **`/admin/bots`** (Vercel-фронт). Это полноценная веб-версия
BotFather, которая работает через прямые вызовы api.telegram.org:

### Что можно делать на странице

* **Добавить бот** — вставляешь токен → автоматически тянется `getMe`,
  записывается в `child_bots`
* **Профиль** — менять имя (`setMyName`), описание (`setMyDescription`),
  короткое описание (`setMyShortDescription`), аватарку
  (`setMyProfilePhoto` — multipart upload)
* **Команды** — редактировать список команд бота (`setMyCommands`),
  по разным языкам (`language_code`)
* **Настройки пула** — отображаемое имя в админке, включён/выключен в
  пуле поллинга, привязка к конкретному `flow_id` (если не указан —
  бот использует главный published)
* **Удалить** — убрать из пула (сам бот в TG остаётся, удалить может
  только @BotFather)

### Архитектура

* Таблица `child_bots` (миграция 0012) хранит токены и метаданные
* `backend/app/bot/runtime/multibot.py` при старте контейнера читает
  активных и подключает к `dp.start_polling(*all_bots)`
* Все хендлеры используют `bot: Bot` из контекста — aiogram сам
  подменяет на нужный экземпляр

### Безопасность

* Токены доступны только админу (RLS + пароль на фронте)
* Прямые вызовы `api.telegram.org` идут с фронта по HTTPS
* Токен виден в детали-карточке «Показать токен» (раскрытие по клику)
