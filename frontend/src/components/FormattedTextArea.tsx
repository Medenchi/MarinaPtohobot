/**
 * Textarea с раскрывающейся панелью форматирования.
 *
 * Кнопки оборачивают выделение в ~b:...~ / ~i:...~ / ... — если ничего
 * не выделено, вставляют пустой шаблон и ставят курсор внутри.
 *
 * Используется в Constructor.tsx вместо обычного TextArea для полей,
 * которые поддерживают лёгкую разметку (text, caption и т.п.).
 */

import { useRef, useState } from "react";
import {
  TextB,
  TextItalic,
  TextUnderline,
  TextStrikethrough,
  Code,
  Quotes,
  EyeSlash,
  Link as LinkIcon,
  Smiley,
  CaretDown,
  CaretRight,
} from "@phosphor-icons/react";

interface Props {
  label?: string;
  hint?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}

interface Tool {
  id: string;
  icon: React.ReactNode;
  title: string;
  /** Префикс/суффикс для оборачивания выделения, либо своя функция вставки */
  wrap?: { open: string; close: string; placeholder?: string };
  insert?: (selected: string) => { text: string; cursorOffset?: number };
}

const TOOLS: Tool[] = [
  { id: "b", icon: <TextB size={14} weight="bold" />,      title: "Жирный",         wrap: { open: "~b:",       close: "~", placeholder: "текст" } },
  { id: "i", icon: <TextItalic size={14} weight="bold" />, title: "Курсив",         wrap: { open: "~i:",       close: "~", placeholder: "текст" } },
  { id: "u", icon: <TextUnderline size={14} />,            title: "Подчёркнутый",   wrap: { open: "~u:",       close: "~", placeholder: "текст" } },
  { id: "s", icon: <TextStrikethrough size={14} />,        title: "Зачёркнутый",    wrap: { open: "~s:",       close: "~", placeholder: "текст" } },
  { id: "code", icon: <Code size={14} />,                  title: "Моноширинный",   wrap: { open: "~code:",    close: "~", placeholder: "код" } },
  { id: "spoiler", icon: <EyeSlash size={14} />,           title: "Спойлер",        wrap: { open: "~spoiler:", close: "~", placeholder: "скрытый" } },
  { id: "q", icon: <Quotes size={14} />,                   title: "Цитата",         wrap: { open: "~q:",       close: "~", placeholder: "цитата" } },
  { id: "qx", icon: <Quotes size={14} weight="fill" />,    title: "Цитата раскрыв.", wrap: { open: "~qx:",     close: "~", placeholder: "длинная цитата" } },
  {
    id: "link",
    icon: <LinkIcon size={14} />,
    title: "Ссылка",
    insert: (sel) => {
      const url = prompt("URL (https://):", "https://") || "";
      if (!url.startsWith("https://") && !url.startsWith("http://") && !url.startsWith("tg://") && !url.startsWith("t.me/")) {
        return { text: sel || "" };
      }
      const label = sel || prompt("Текст ссылки:", "") || url;
      return { text: `~link:${url}|${label}~` };
    },
  },
  {
    id: "emoji",
    icon: <Smiley size={14} />,
    title: "Premium-эмодзи",
    insert: (sel) => {
      const id = prompt("ID премиум-эмодзи (число, из @ConvertEmojiBot):", "") || "";
      if (!/^\d+$/.test(id)) return { text: sel || "" };
      const fb = prompt("Fallback-эмодзи (для не-Premium):", "⭐") || "⭐";
      return { text: `~emoji:${id}|${fb}~` };
    },
  },
];

const VARIABLE_TOKENS = [
  { token: "{{user.first_name}}", label: "Имя из TG" },
  { token: "{{user.username}}",   label: "@username" },
  { token: "{{user.id}}",         label: "TG id" },
  { token: "{{system.season}}",   label: "Текущий сезон" },
  { token: "{{system.date}}",     label: "Сегодня" },
];

export default function FormattedTextArea({
  label, hint, placeholder, value, onChange, rows = 4,
}: Props) {
  const taRef = useRef<HTMLTextAreaElement | null>(null);
  const [open, setOpen] = useState(true);

  function applyTool(tool: Tool) {
    const ta = taRef.current;
    if (!ta) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const selected = value.slice(start, end);

    let insertion = "";
    let cursorPos = 0;

    if (tool.wrap) {
      const inner = selected || tool.wrap.placeholder || "";
      insertion = `${tool.wrap.open}${inner}${tool.wrap.close}`;
      cursorPos = selected
        ? start + insertion.length
        : start + tool.wrap.open.length + inner.length;
    } else if (tool.insert) {
      const r = tool.insert(selected);
      insertion = r.text;
      cursorPos = start + insertion.length + (r.cursorOffset || 0);
    }

    const next = value.slice(0, start) + insertion + value.slice(end);
    onChange(next);
    // вернуть фокус и поставить курсор
    requestAnimationFrame(() => {
      ta.focus();
      ta.setSelectionRange(cursorPos, cursorPos);
    });
  }

  function insertToken(token: string) {
    const ta = taRef.current;
    if (!ta) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const next = value.slice(0, start) + token + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      ta.focus();
      ta.setSelectionRange(start + token.length, start + token.length);
    });
  }

  return (
    <div>
      {label && (
        <span className="block text-xs uppercase tracking-tighter text-muted mb-1">
          {label}
        </span>
      )}

      {/* Toolbar */}
      <div className="border border-line rounded-t-md bg-paper px-1.5 py-1 flex items-center gap-0.5 flex-wrap">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="text-muted hover:text-ink px-1 inline-flex items-center"
          title={open ? "Свернуть" : "Развернуть"}
        >
          {open ? <CaretDown size={12} /> : <CaretRight size={12} />}
          <span className="text-[10px] ml-0.5">Форматирование</span>
        </button>
        {open && (
          <>
            <span className="w-px h-4 bg-line mx-1" />
            {TOOLS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => applyTool(t)}
                title={t.title}
                className="p-1.5 rounded hover:bg-white hover:border hover:border-line text-ink"
              >
                {t.icon}
              </button>
            ))}
            <span className="w-px h-4 bg-line mx-1" />
            <details className="relative">
              <summary className="cursor-pointer text-[10px] px-2 py-1 rounded hover:bg-white text-muted hover:text-ink list-none">
                {"{{}}"} переменные
              </summary>
              <div className="absolute z-20 mt-1 right-0 bg-white border border-line rounded shadow-md p-1 w-56">
                {VARIABLE_TOKENS.map((v) => (
                  <button
                    key={v.token}
                    type="button"
                    onClick={() => insertToken(v.token)}
                    className="w-full text-left text-[11px] px-2 py-1 rounded hover:bg-paper"
                  >
                    <code className="text-ink">{v.token}</code>
                    <span className="text-muted ml-2">{v.label}</span>
                  </button>
                ))}
              </div>
            </details>
          </>
        )}
      </div>

      <textarea
        ref={taRef}
        rows={rows}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border border-line border-t-0 rounded-b-md px-3 py-2 text-sm font-mono focus:outline-none focus:border-ink resize-y"
      />
      {hint && <p className="text-[10px] text-muted mt-1">{hint}</p>}
    </div>
  );
}
