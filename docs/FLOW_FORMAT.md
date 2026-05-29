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
