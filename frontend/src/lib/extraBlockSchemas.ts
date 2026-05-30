/**
 * Схемы 30+ доп-блоков, реализованных в backend/.../extra_blocks.py.
 * Подключаются через blockSchemas.ts.
 */

import type { BlockSchema } from "./blockSchemas";

export const EXTRA_BLOCK_SCHEMAS: BlockSchema[] = [
  // ---- Текст / форматирование ----
  {
    type: "send_heading",
    group: "message",
    title: "Заголовок",
    description: "Большой заголовок с иконкой и декоративной линией. Уровни 1/2/3.",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст", kind: "text", required: true },
      { key: "icon", label: "Эмодзи", kind: "text", placeholder: "✨" },
      { key: "level", label: "Уровень (1–3)", kind: "number", placeholder: "1" },
    ],
  },
  {
    type: "send_quote",
    group: "message",
    title: "Цитата",
    description: "Telegram blockquote, можно раскрывающуюся.",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст цитаты", kind: "textarea", required: true },
      { key: "author", label: "Автор", kind: "text" },
      { key: "expandable", label: "Раскрывающаяся", kind: "boolean" },
    ],
  },
  {
    type: "send_checklist",
    group: "message",
    title: "Чек-лист",
    description: "Маркированный список с галочками ✅/▫️.",
    hasNext: true,
    fields: [
      { key: "title", label: "Заголовок", kind: "text" },
      { key: "items", label: "Пункты", kind: "options-list" },
      { key: "checked", label: "Отмеченные (индексы 0,1,2)", kind: "text" },
    ],
  },
  {
    type: "send_numbered_list",
    group: "message",
    title: "Нумерованный список",
    description: "1. 2. 3. …",
    hasNext: true,
    fields: [
      { key: "title", label: "Заголовок", kind: "text" },
      { key: "items", label: "Пункты", kind: "options-list" },
    ],
  },
  {
    type: "send_kv_table",
    group: "message",
    title: "Таблица ключ-значение",
    description: "Имя: Анна\\nТелефон: ...",
    hasNext: true,
    fields: [
      { key: "title", label: "Заголовок", kind: "text" },
      { key: "rows", label: "Поля (key/value)", kind: "kv" },
    ],
  },
  {
    type: "send_with_preview",
    group: "message",
    title: "Сообщение с превью ссылки",
    description: "Большое превью ссылки сверху (Bot API link_preview_options).",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст", kind: "textarea", required: true },
      { key: "url", label: "URL для превью", kind: "text", required: true },
      { key: "above_text", label: "Превью НАД текстом", kind: "boolean" },
      { key: "large", label: "Большое превью", kind: "boolean" },
    ],
  },

  // ---- Медиа ----
  {
    type: "send_sticker",
    group: "message",
    title: "Стикер",
    description: "По file_id стикера.",
    hasNext: true,
    fields: [{ key: "sticker_id", label: "file_id стикера", kind: "text", required: true }],
  },
  {
    type: "send_voice",
    group: "message",
    title: "Голосовое",
    description: ".ogg по URL.",
    hasNext: true,
    fields: [{ key: "url", label: "URL .ogg", kind: "text", required: true }],
  },
  {
    type: "send_audio",
    group: "message",
    title: "Аудио",
    description: ".mp3/.m4a с названием и исполнителем.",
    hasNext: true,
    fields: [
      { key: "url", label: "URL файла", kind: "text", required: true },
      { key: "title", label: "Название", kind: "text" },
      { key: "performer", label: "Исполнитель", kind: "text" },
    ],
  },
  {
    type: "send_video_note",
    group: "message",
    title: "Кругляш (видео-сообщение)",
    description: "Круглое видео.",
    hasNext: true,
    fields: [{ key: "url", label: "URL .mp4", kind: "text", required: true }],
  },
  {
    type: "send_location",
    group: "message",
    title: "Локация на карте",
    description: "Просто точка с координатами.",
    hasNext: true,
    fields: [
      { key: "latitude", label: "Широта", kind: "number", required: true },
      { key: "longitude", label: "Долгота", kind: "number", required: true },
    ],
  },
  {
    type: "send_venue",
    group: "message",
    title: "Место с адресом",
    description: "Локация + название + адрес.",
    hasNext: true,
    fields: [
      { key: "latitude", label: "Широта", kind: "number", required: true },
      { key: "longitude", label: "Долгота", kind: "number", required: true },
      { key: "title", label: "Название места", kind: "text", required: true },
      { key: "address", label: "Адрес", kind: "text", required: true },
    ],
  },
  {
    type: "send_contact",
    group: "message",
    title: "Контакт",
    description: "Карточка контакта.",
    hasNext: true,
    fields: [
      { key: "phone", label: "Телефон", kind: "text", required: true },
      { key: "first_name", label: "Имя", kind: "text", required: true },
      { key: "last_name", label: "Фамилия", kind: "text" },
    ],
  },
  {
    type: "send_dice",
    group: "special",
    title: "Кубик 🎲",
    description: "Анимированный бросок. Результат → vars[save_to].",
    hasNext: true,
    fields: [
      { key: "emoji", label: "Эмодзи (🎲🎯🏀⚽🎳🎰)", kind: "text", placeholder: "🎲" },
      { key: "save_to", label: "Сохранить в", kind: "text", placeholder: "dice_value" },
    ],
  },
  {
    type: "send_poll",
    group: "special",
    title: "Опрос (Poll)",
    description: "Telegram Poll с вариантами.",
    hasNext: true,
    fields: [
      { key: "question", label: "Вопрос", kind: "text", required: true },
      { key: "options", label: "Варианты", kind: "options-list" },
      { key: "anonymous", label: "Анонимный", kind: "boolean" },
      { key: "multiple", label: "Множественный выбор", kind: "boolean" },
    ],
  },
  {
    type: "send_chat_action",
    group: "message",
    title: "Chat action",
    description: "typing/upload_photo/record_voice/... и опц. пауза.",
    hasNext: true,
    fields: [
      { key: "action", label: "Action", kind: "text", placeholder: "typing" },
      { key: "seconds", label: "Длительность (сек)", kind: "number", placeholder: "1.5" },
    ],
  },

  // ---- Интерактив ----
  {
    type: "send_copy_button",
    group: "special",
    title: "Кнопка «📋 Скопировать»",
    description: "Inline-кнопка, копирует текст в буфер (CopyTextButton).",
    hasNext: true,
    fields: [
      { key: "text", label: "Сообщение", kind: "textarea", required: true },
      { key: "button_text", label: "Подпись кнопки", kind: "text", placeholder: "📋 Скопировать" },
      { key: "copy_text", label: "Что копировать", kind: "text", required: true },
    ],
  },
  {
    type: "send_webapp_button",
    group: "special",
    title: "Кнопка Mini App",
    description: "Открывает встроенное web-приложение.",
    hasNext: true,
    fields: [
      { key: "text", label: "Сообщение", kind: "textarea", required: true },
      { key: "button_text", label: "Подпись кнопки", kind: "text", placeholder: "🚀 Открыть" },
      { key: "url", label: "URL приложения (https://)", kind: "text", required: true },
    ],
  },
  {
    type: "send_share_button",
    group: "special",
    title: "Кнопка «Поделиться ботом»",
    description: "t.me/share/url — приглашает друга.",
    hasNext: true,
    fields: [
      { key: "text", label: "Сообщение", kind: "textarea", required: true },
      { key: "button_text", label: "Подпись кнопки", kind: "text", placeholder: "📤 Рассказать друзьям" },
      { key: "share_text", label: "Текст, который скопируется", kind: "text" },
    ],
  },
  {
    type: "send_rating",
    group: "input",
    title: "Звёздочный рейтинг ⭐",
    description: "Кнопки 1-5 ⭐. Результат → vars[save_to].",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст вопроса", kind: "text", placeholder: "Оцени:" },
      { key: "scale", label: "Шкала (макс)", kind: "number", placeholder: "5" },
      { key: "save_to", label: "Сохранить в", kind: "text", placeholder: "rating" },
    ],
  },

  // ---- Логика ----
  {
    type: "random_branch",
    group: "logic",
    title: "Случайная ветка",
    description: "Случайно выбирает один из choices.",
    hasNext: false,
    fields: [{ key: "choices", label: "Варианты (next id'ы)", kind: "options-list" }],
  },
  {
    type: "switch",
    group: "logic",
    title: "Switch-case",
    description: "По значению vars[var] идёт в нужный node id.",
    hasNext: false,
    fields: [
      { key: "variable", label: "Имя переменной", kind: "text", required: true },
      { key: "cases", label: "Кейсы (value → node_id)", kind: "kv" },
      { key: "default", label: "Default node id", kind: "node-ref" },
    ],
  },
  {
    type: "increment_var",
    group: "logic",
    title: "Прибавить к переменной",
    description: "vars[name] += delta (счётчики, баллы).",
    hasNext: true,
    fields: [
      { key: "name", label: "Имя переменной", kind: "text", required: true },
      { key: "delta", label: "Дельта", kind: "number", placeholder: "1" },
    ],
  },
  {
    type: "append_to_list",
    group: "logic",
    title: "Добавить в список",
    description: "vars[name].append(value).",
    hasNext: true,
    fields: [
      { key: "name", label: "Имя списка", kind: "text", required: true },
      { key: "value", label: "Что добавить (можно шаблон)", kind: "text", required: true },
    ],
  },
  {
    type: "regex_extract",
    group: "logic",
    title: "Извлечь по регулярке",
    description: "Достаёт первое совпадение из source в vars[save_to].",
    hasNext: true,
    fields: [
      { key: "source", label: "Откуда (шаблон)", kind: "text", required: true },
      { key: "pattern", label: "Regex", kind: "text", required: true, placeholder: "\\\\+?[0-9]{10,15}" },
      { key: "save_to", label: "Сохранить в", kind: "text", placeholder: "extracted" },
    ],
  },
  {
    type: "math_eval",
    group: "logic",
    title: "Арифметика",
    description: "Только +-*/, числа, скобки. Результат → vars[save_to].",
    hasNext: true,
    fields: [
      { key: "expression", label: "Выражение", kind: "text", required: true, placeholder: "{{vars.a}} + {{vars.b}}" },
      { key: "save_to", label: "Сохранить в", kind: "text", placeholder: "result" },
    ],
  },
  {
    type: "time_window",
    group: "logic",
    title: "По времени суток",
    description: "Если сейчас внутри окна — inside_next, иначе outside_next.",
    hasNext: false,
    fields: [
      { key: "start_hour", label: "Начало (час)", kind: "number", placeholder: "9" },
      { key: "end_hour", label: "Конец (час)", kind: "number", placeholder: "21" },
      { key: "inside_next", label: "Если внутри →", kind: "node-ref" },
      { key: "outside_next", label: "Если снаружи →", kind: "node-ref" },
    ],
  },
  {
    type: "schedule_branch",
    group: "logic",
    title: "Будни / выходные",
    description: "Branch по дню недели.",
    hasNext: false,
    fields: [
      { key: "weekday_next", label: "Будни →", kind: "node-ref" },
      { key: "weekend_next", label: "Выходные →", kind: "node-ref" },
    ],
  },

  // ---- Данные ----
  {
    type: "db_update",
    group: "data",
    title: "UPDATE строки",
    description: "Обновить строки таблицы по where.",
    hasNext: true,
    fields: [
      { key: "table", label: "Таблица", kind: "text", required: true },
      { key: "where", label: "Where (key=value)", kind: "kv" },
      { key: "fields", label: "Что обновить", kind: "kv" },
    ],
  },
  {
    type: "db_count",
    group: "data",
    title: "COUNT(*)",
    description: "Количество строк по фильтрам в vars[save_to].",
    hasNext: true,
    fields: [
      { key: "table", label: "Таблица", kind: "text", required: true },
      { key: "filters", label: "Фильтры", kind: "filters" },
      { key: "save_to", label: "Сохранить в", kind: "text", placeholder: "count" },
    ],
  },

  // ---- Контент-специфика ----
  {
    type: "send_outfit_card",
    group: "special",
    title: "Карточка одного образа",
    description: "Берёт items_var[index], шлёт фото + теги + кнопку купить.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник", kind: "text", placeholder: "matched_outfits" },
      { key: "index", label: "Индекс в списке", kind: "number", placeholder: "0" },
    ],
  },
  {
    type: "send_outfit_grid",
    group: "special",
    title: "Сетка образов (медиа-группа)",
    description: "До 10 фото одним сообщением.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник", kind: "text", placeholder: "matched_outfits" },
    ],
  },
  {
    type: "show_random_outfit",
    group: "special",
    title: "Случайный образ",
    description: "Из items_var случайно выбирает один и шлёт.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник", kind: "text", placeholder: "matched_outfits" },
    ],
  },
];

// ===== ВТОРАЯ ВОЛНА: удаление, опросы, бот-управление-собой, цветные кнопки =====

EXTRA_BLOCK_SCHEMAS.push(
  // ---- Управление сообщениями ----
  {
    type: "delete_last_message",
    group: "special",
    title: "Удалить последнее сообщение",
    description: "Стирает N последних сообщений бота, чтобы не наслаивались карточки.",
    hasNext: true,
    fields: [{ key: "count", label: "Сколько удалить", kind: "number", placeholder: "1" }],
  },
  {
    type: "clear_chat",
    group: "special",
    title: "Очистить весь чат бота",
    description: "Удаляет ВСЕ сообщения бота за сессию (лимит TG: 48 ч).",
    hasNext: true,
    fields: [],
  },
  // ---- Poll как вопрос ----
  {
    type: "ask_poll",
    group: "input",
    title: "Вопрос-опрос (Poll)",
    description:
      "Нативный Telegram-опрос. Юзер голосует — ответ пишется в vars[variable], затем next. Поддерживает множественный выбор.",
    hasNext: true,
    fields: [
      { key: "question", label: "Вопрос", kind: "textarea", required: true },
      { key: "options", label: "Варианты", kind: "options-list" },
      { key: "variable", label: "Имя переменной", kind: "text", required: true },
      { key: "multiple", label: "Можно выбрать несколько", kind: "boolean" },
    ],
  },
  // ---- Бот меняет себя ----
  {
    type: "set_bot_name",
    group: "special",
    title: "Сменить имя бота",
    description: "bot.set_my_name(name). Лимит 64 символа.",
    hasNext: true,
    fields: [
      { key: "name", label: "Новое имя", kind: "text", required: true },
      { key: "language_code", label: "Язык (ru/en)", kind: "text", placeholder: "ru" },
    ],
  },
  {
    type: "set_bot_description",
    group: "special",
    title: "Сменить описание бота",
    description: "bot.set_my_description. Лимит 512 символов. Видно в профиле.",
    hasNext: true,
    fields: [
      { key: "description", label: "Описание", kind: "textarea", required: true },
      { key: "language_code", label: "Язык", kind: "text", placeholder: "ru" },
    ],
  },
  {
    type: "set_bot_short_description",
    group: "special",
    title: "Сменить короткое описание",
    description: "Видно в превью-карточке при шаринге. Лимит 120 символов.",
    hasNext: true,
    fields: [
      { key: "short_description", label: "Короткое описание", kind: "text", required: true },
      { key: "language_code", label: "Язык", kind: "text", placeholder: "ru" },
    ],
  },
  {
    type: "set_bot_avatar",
    group: "special",
    title: "Сменить аватарку бота",
    description: "bot.set_my_profile_photo (aiogram 3.27+). URL должен быть https://.",
    hasNext: true,
    fields: [{ key: "url", label: "URL картинки", kind: "text", required: true }],
  },
  // ---- Цветные кнопки (через эмодзи) ----
  {
    type: "send_colored_buttons",
    group: "special",
    title: "Сообщение с «цветными» кнопками",
    description:
      "Эмулирует цвета через эмодзи-префиксы (🟢/🔴/🟡/🔵/🟣/🟠/⚫/⚪). У каждой кнопки поле color. Telegram не поддерживает реальные цвета inline-кнопок в обычных чатах.",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст", kind: "textarea", required: true },
      { key: "buttons", label: "Кнопки (с полем color)", kind: "buttons" },
    ],
  },
);
