// Schema descriptions for every block type the bot runtime understands.
// The constructor UI renders form fields based on these schemas. The same
// JSON shape is what app/bot/runtime/blocks.py interprets.

export type FieldKind =
  | "text"
  | "textarea"
  | "number"
  | "boolean"
  | "node-ref" // dropdown of other block ids
  | "options-list" // for ask_question: list of {text, value}
  | "buttons" // for send_message: list of rows of {text, next, value?, url?}
  | "filters" // for db_query: list of {column, op, value}
  | "kv"; // generic key/value dict

export interface BlockField {
  key: string;
  label: string;
  kind: FieldKind;
  hint?: string;
  placeholder?: string;
  required?: boolean;
  options?: { value: string; label: string }[];
}

export interface BlockSchema {
  type: string;
  group: "trigger" | "message" | "input" | "logic" | "data" | "special";
  title: string;
  description: string;
  hasNext: boolean; // shows the "next block" dropdown in the UI
  fields: BlockField[];
}

import { EXTRA_BLOCK_SCHEMAS } from "./extraBlockSchemas";

export const BLOCK_SCHEMAS: BlockSchema[] = [
  // ---- Triggers ----
  {
    type: "command",
    group: "trigger",
    title: "Команда",
    description: "Точка входа: /start, /help и т.п.",
    hasNext: true,
    fields: [
      { key: "command", label: "Команда (без слэша)", kind: "text", placeholder: "start", required: true },
      { key: "keep_vars", label: "Не сбрасывать переменные", kind: "boolean", hint: "По умолчанию /start обнуляет vars" },
    ],
  },
  {
    type: "text_match",
    group: "trigger",
    title: "Текст-триггер",
    description: "Срабатывает на сообщение пользователя",
    hasNext: true,
    fields: [
      { key: "pattern", label: "Текст", kind: "text", required: true },
      {
        key: "mode",
        label: "Режим",
        kind: "text",
        hint: "exact / contains / starts_with",
        placeholder: "exact",
      },
    ],
  },

  // ---- Messages ----
  {
    type: "send_message",
    group: "message",
    title: "Сообщение",
    description: "Текст + опциональные inline-кнопки. Поддерживает {{vars.x}} и {{user.first_name}}.",
    hasNext: true,
    fields: [
      { key: "text", label: "Текст", kind: "textarea", required: true },
      { key: "buttons", label: "Кнопки (inline)", kind: "buttons" },
      {
        key: "parse_mode",
        label: "Parse mode",
        kind: "text",
        placeholder: "HTML",
        hint: "HTML или MarkdownV2",
      },
    ],
  },
  {
    type: "send_photo",
    group: "message",
    title: "Фото",
    description: "Отправляет картинку по URL.",
    hasNext: true,
    fields: [
      { key: "url", label: "URL картинки", kind: "text", required: true },
      { key: "caption", label: "Подпись", kind: "textarea" },
    ],
  },
  {
    type: "send_album",
    group: "message",
    title: "Альбом (медиагруппа)",
    description: "Шлёт до 10 фото из переменной (обычно matched_outfits).",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Переменная со списком", kind: "text", placeholder: "matched_outfits" },
      { key: "caption_template", label: "Шаблон подписи", kind: "text", placeholder: "{{outfit.title}}" },
    ],
  },
  {
    type: "send_document",
    group: "message",
    title: "Документ",
    description: "Шлёт файл по URL или Telegram file_id.",
    hasNext: true,
    fields: [
      { key: "file", label: "URL или file_id", kind: "text", required: true },
      { key: "filename", label: "Имя файла", kind: "text" },
      { key: "caption", label: "Подпись", kind: "textarea" },
    ],
  },
  {
    type: "send_video",
    group: "message",
    title: "Видео",
    description: "Шлёт видео по URL.",
    hasNext: true,
    fields: [
      { key: "url", label: "URL", kind: "text", required: true },
      { key: "caption", label: "Подпись", kind: "textarea" },
    ],
  },
  {
    type: "typing",
    group: "message",
    title: "Печатает…",
    description: "Показывает индикатор и ждёт N секунд.",
    hasNext: true,
    fields: [{ key: "seconds", label: "Секунд", kind: "number", placeholder: "1.5" }],
  },
  {
    type: "delay",
    group: "message",
    title: "Задержка",
    description: "Пауза без индикатора.",
    hasNext: true,
    fields: [{ key: "seconds", label: "Секунд", kind: "number", placeholder: "1" }],
  },

  // ---- Input ----
  {
    type: "ask_question",
    group: "input",
    title: "Вопрос",
    description: "Шлёт текст и сохраняет ответ в переменную.",
    hasNext: true,
    fields: [
      { key: "text", label: "Вопрос", kind: "textarea", required: true },
      { key: "variable", label: "Имя переменной", kind: "text", required: true, placeholder: "color" },
      { key: "options", label: "Варианты", kind: "options-list" },
      { key: "inline", label: "Inline-кнопки", kind: "boolean", hint: "Иначе reply-keyboard" },
    ],
  },

  // ---- Logic ----
  {
    type: "set_variable",
    group: "logic",
    title: "Записать переменную",
    description: "vars[name] = value (с подстановкой шаблонов).",
    hasNext: true,
    fields: [
      { key: "name", label: "Имя", kind: "text", required: true },
      { key: "value", label: "Значение", kind: "textarea" },
    ],
  },
  {
    type: "branch",
    group: "logic",
    title: "Условие",
    description: "Если левая часть op правая — true_next, иначе false_next.",
    hasNext: false,
    fields: [
      { key: "variable", label: "Левая часть", kind: "text", placeholder: "{{vars.color}}" },
      {
        key: "op",
        label: "Оператор",
        kind: "text",
        placeholder: "eq",
        hint: "eq / neq / contains / in / gt / lt / empty / not_empty",
      },
      { key: "value", label: "Правая часть", kind: "text" },
      { key: "true_next", label: "Если ИСТИНА → блок", kind: "node-ref" },
      { key: "false_next", label: "Если ЛОЖЬ → блок", kind: "node-ref" },
    ],
  },
  {
    type: "goto",
    group: "logic",
    title: "Переход",
    description: "Просто переходит к указанному блоку.",
    hasNext: false,
    fields: [{ key: "next", label: "Цель", kind: "node-ref", required: true }],
  },
  {
    type: "end",
    group: "logic",
    title: "Конец",
    description: "Завершает флоу. Следующий /start запустит всё заново.",
    hasNext: false,
    fields: [],
  },

  // ---- Data ----
  {
    type: "db_query",
    group: "data",
    title: "Запрос в БД",
    description: "Достаёт строки из таблицы Supabase в переменную.",
    hasNext: true,
    fields: [
      { key: "table", label: "Таблица", kind: "text", required: true, placeholder: "outfits" },
      { key: "select", label: "Колонки (PostgREST)", kind: "text", placeholder: "*, outfit_images(*)" },
      { key: "filters", label: "Фильтры", kind: "filters" },
      { key: "order_by", label: "Сортировка по", kind: "text", placeholder: "sort_order" },
      { key: "descending", label: "По убыванию", kind: "boolean" },
      { key: "limit", label: "Лимит", kind: "number", placeholder: "20" },
      { key: "save_to", label: "Переменная для результата", kind: "text", placeholder: "matched_outfits" },
    ],
  },
  {
    type: "db_insert",
    group: "data",
    title: "Вставка в БД",
    description: "Кладёт новую строку (например — заявку).",
    hasNext: true,
    fields: [
      { key: "table", label: "Таблица", kind: "text", required: true, placeholder: "bookings" },
      { key: "fields", label: "Поля", kind: "kv" },
      { key: "save_to", label: "Сохранить вставленную строку в", kind: "text" },
    ],
  },

  // ---- Special ----
  {
    type: "generate_pdf",
    group: "special",
    title: "PDF подборки",
    description: "Генерит PDF с водяным знаком и шлёт юзеру.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник списка", kind: "text", placeholder: "matched_outfits" },
      { key: "filename", label: "Имя файла", kind: "text", placeholder: "podbor_obrazov.pdf" },
      { key: "caption", label: "Подпись при отправке", kind: "textarea" },
      { key: "send_now", label: "Отправить сразу", kind: "boolean" },
      { key: "save_to", label: "Сохранить ссылку в", kind: "text", placeholder: "pdf" },
    ],
  },
  {
    type: "http_request",
    group: "special",
    title: "HTTP запрос",
    description: "Дёргает внешний API.",
    hasNext: true,
    fields: [
      { key: "url", label: "URL", kind: "text", required: true },
      { key: "method", label: "Метод", kind: "text", placeholder: "GET" },
      { key: "headers", label: "Заголовки", kind: "kv" },
      { key: "body", label: "Тело JSON", kind: "kv" },
      { key: "save_to", label: "Сохранить ответ в", kind: "text" },
    ],
  },
  {
    type: "handoff_to_admin",
    group: "special",
    title: "Передать админу",
    description: "Шлёт сводку владельцу бота в личку.",
    hasNext: true,
    fields: [{ key: "message", label: "Текст сводки", kind: "textarea" }],
  },
  {
    type: "show_outfits_voting",
    group: "special",
    title: "Карусель с лайками",
    description: "Шлёт N фото-карточек с кнопками 👍/💔. Сохраняет id в vars.liked_ids / disliked_ids.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник", kind: "text", placeholder: "matched_outfits" },
      { key: "intro", label: "Подводка перед каруселью", kind: "textarea" },
      { key: "limit", label: "Сколько максимум", kind: "number", placeholder: "10" },
      { key: "liked_var", label: "Переменная для лайков", kind: "text", placeholder: "liked_ids" },
      { key: "disliked_var", label: "Для дизлайков", kind: "text", placeholder: "disliked_ids" },
      { key: "done_text", label: "Текст под кнопкой Готово", kind: "text" },
      { key: "done_button", label: "Подпись на кнопке", kind: "text", placeholder: "✅ Готово, дальше" },
    ],
  },
  {
    type: "generate_pdf_voted",
    group: "special",
    title: "PDF с секциями (Понравилось / Может подойти)",
    description: "Сборка PDF: liked_ids → раздел «Понравилось», остальные → «Может подойти». Если лайков нет — без секций.",
    hasNext: true,
    fields: [
      { key: "items_var", label: "Источник", kind: "text", placeholder: "matched_outfits" },
      { key: "liked_var", label: "Переменная с лайками", kind: "text", placeholder: "liked_ids" },
      { key: "filename", label: "Имя файла", kind: "text", placeholder: "podbor_obrazov.pdf" },
      { key: "caption", label: "Подпись при отправке", kind: "textarea" },
      { key: "send_now", label: "Отправить сразу", kind: "boolean" },
      { key: "save_to", label: "Сохранить ссылку в", kind: "text", placeholder: "pdf" },
    ],
  },
  ...EXTRA_BLOCK_SCHEMAS,
];

export function schemaFor(type: string): BlockSchema | undefined {
  return BLOCK_SCHEMAS.find((s) => s.type === type);
}

export const BLOCK_GROUPS: { id: BlockSchema["group"]; title: string }[] = [
  { id: "trigger", title: "Триггеры" },
  { id: "message", title: "Сообщения" },
  { id: "input", title: "Вопросы" },
  { id: "logic", title: "Логика" },
  { id: "data", title: "Данные" },
  { id: "special", title: "Спец" },
];
