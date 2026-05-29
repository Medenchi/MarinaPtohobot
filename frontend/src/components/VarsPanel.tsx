/**
 * Боковая панель «Переменные». Показывает:
 *   - все user.* (что приходит из Telegram автоматически),
 *   - все vars.*, которые встречаются в графе (как источник —
 *     ask_question.variable / set_variable.name / db_query.save_to /
 *     generate_pdf.save_to / db_insert.save_to / http_request.save_to),
 *   - где они используются (поиск по {{vars.x}} в текстах).
 *
 * Открывается кнопкой 📖 «Переменные» в шапке конструктора. Клик на токен
 * копирует {{...}} в буфер обмена.
 */

import { useMemo } from "react";
import { Copy, X } from "@phosphor-icons/react";
import type { FlowGraph } from "@/types";

interface Props {
  graph: FlowGraph;
  open: boolean;
  onClose: () => void;
}

interface VarInfo {
  name: string;       // без префикса (e.g. "color")
  ns: "vars" | "user";
  source: "TG" | string;  // node id, который её создал, или "TG"
  type: "string" | "list" | "object" | "any";
  usedIn: string[];   // массив node id, где встречается {{vars.x}}
  description?: string;
}

const USER_VARS: VarInfo[] = [
  { name: "first_name",    ns: "user", source: "TG", type: "string", usedIn: [], description: "Имя из Telegram" },
  { name: "last_name",     ns: "user", source: "TG", type: "string", usedIn: [], description: "Фамилия (часто пусто)" },
  { name: "full_name",     ns: "user", source: "TG", type: "string", usedIn: [], description: "first + last" },
  { name: "username",      ns: "user", source: "TG", type: "string", usedIn: [], description: "@username без @" },
  { name: "id",            ns: "user", source: "TG", type: "string", usedIn: [], description: "Telegram user id" },
  { name: "language_code", ns: "user", source: "TG", type: "string", usedIn: [], description: "ru / en и т.д." },
  { name: "is_premium",    ns: "user", source: "TG", type: "string", usedIn: [], description: "true/false" },
];

function collectVars(graph: FlowGraph): VarInfo[] {
  const found = new Map<string, VarInfo>();

  const note = (name: string, source: string, type: VarInfo["type"]) => {
    if (!name) return;
    const prev = found.get(name);
    if (!prev) {
      found.set(name, { name, ns: "vars", source, type, usedIn: [] });
    } else {
      // если уже есть, не перетираем source, но повышаем type до конкретного
      if (prev.type === "any" && type !== "any") prev.type = type;
    }
  };

  for (const n of graph.nodes) {
    const p = (n.params || {}) as Record<string, unknown>;
    switch (n.type) {
      case "ask_question":
        if (typeof p.variable === "string") note(p.variable, n.id, "string");
        break;
      case "set_variable":
        if (typeof p.name === "string") note(p.name, n.id, "any");
        break;
      case "db_query":
        if (typeof p.save_to === "string") note(p.save_to, n.id, "list");
        break;
      case "db_insert":
        if (typeof p.save_to === "string") note(p.save_to, n.id, "object");
        break;
      case "generate_pdf":
        if (typeof p.save_to === "string") note(p.save_to, n.id, "object");
        break;
      case "http_request":
        if (typeof p.save_to === "string") note(p.save_to, n.id, "object");
        break;
    }
  }

  // поиск использований — простая регулярка
  const usagePattern = /\{\{\s*vars\.([\w]+)/g;
  for (const n of graph.nodes) {
    walkStrings(n.params, (s) => {
      let m: RegExpExecArray | null;
      while ((m = usagePattern.exec(s)) !== null) {
        const v = found.get(m[1]);
        if (v && !v.usedIn.includes(n.id)) v.usedIn.push(n.id);
        if (!v) {
          // используется, но не определена — показываем как «висящую»
          found.set(m[1], {
            name: m[1], ns: "vars", source: "?", type: "any",
            usedIn: [n.id], description: "Используется, но нигде не определена",
          });
        }
      }
    });
  }

  return Array.from(found.values()).sort((a, b) => a.name.localeCompare(b.name));
}

function walkStrings(value: unknown, cb: (s: string) => void) {
  if (typeof value === "string") cb(value);
  else if (Array.isArray(value)) value.forEach((v) => walkStrings(v, cb));
  else if (value && typeof value === "object") {
    Object.values(value as Record<string, unknown>).forEach((v) => walkStrings(v, cb));
  }
}

function copy(token: string) {
  try {
    void navigator.clipboard.writeText(token);
  } catch {
    /* ignore */
  }
}

export default function VarsPanel({ graph, open, onClose }: Props) {
  const userVars: VarInfo[] = USER_VARS;
  const vars = useMemo(() => collectVars(graph), [graph]);

  if (!open) return null;

  return (
    <aside className="fixed inset-y-0 right-0 w-[360px] max-w-[92vw] bg-white border-l border-line shadow-xl z-40 flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-line">
        <h2 className="serif-heading text-lg">Переменные</h2>
        <button onClick={onClose} className="text-muted hover:text-ink" title="Закрыть">
          <X size={16} weight="thin" />
        </button>
      </header>
      <div className="flex-1 overflow-auto p-4 space-y-5 text-sm">
        <section>
          <h3 className="text-[10px] uppercase tracking-tighter text-muted mb-2">
            Из Telegram (автоматически)
          </h3>
          <ul className="space-y-1">
            {userVars.map((v) => (
              <VarRow key={v.name} v={v} />
            ))}
          </ul>
        </section>

        <section>
          <h3 className="text-[10px] uppercase tracking-tighter text-muted mb-2">
            Из этого флоу ({vars.length})
          </h3>
          {vars.length === 0 ? (
            <p className="text-xs text-muted">
              Пока никаких переменных нет. Добавь блок «Вопрос» и укажи «Имя
              переменной» — она появится здесь.
            </p>
          ) : (
            <ul className="space-y-1">
              {vars.map((v) => (
                <VarRow key={v.name} v={v} />
              ))}
            </ul>
          )}
        </section>

        <section className="text-xs text-muted leading-relaxed">
          <h3 className="text-[10px] uppercase tracking-tighter text-muted mb-1">
            Как использовать
          </h3>
          В любом тексте пиши <code className="text-ink">{"{{vars.имя}}"}</code> —
          подставится значение. То же для <code className="text-ink">{"{{user.first_name}}"}</code>.
          Если токен — единственное содержимое строки (например в фильтре
          <code> branch</code>), движок вернёт сырое значение (число, список,
          объект) без преобразования в текст.
        </section>
      </div>
    </aside>
  );
}

function VarRow({ v }: { v: VarInfo }) {
  const token = `{{${v.ns}.${v.name}}}`;
  return (
    <li>
      <button
        onClick={() => copy(token)}
        className="w-full text-left px-2 py-1.5 rounded border border-line bg-paper hover:border-ink group"
        title="Скопировать в буфер"
      >
        <div className="flex items-center gap-2">
          <code className="text-xs text-ink">{token}</code>
          <Copy size={11} weight="thin" className="opacity-0 group-hover:opacity-100 text-muted" />
          <span className="ml-auto text-[10px] text-muted font-mono">{v.type}</span>
        </div>
        <div className="flex justify-between mt-0.5">
          <span className="text-[10px] text-muted">
            {v.description || (v.source === "TG" ? "из Telegram" : `создаёт #${v.source}`)}
          </span>
          {v.usedIn.length > 0 && (
            <span className="text-[10px] text-muted">используется в {v.usedIn.length}</span>
          )}
        </div>
      </button>
    </li>
  );
}

// Используется для умной вставки токена в активное textarea/input.
export function insertAtCursor(text: string) {
  const el = document.activeElement as HTMLTextAreaElement | HTMLInputElement | null;
  if (!el || (el.tagName !== "TEXTAREA" && el.tagName !== "INPUT")) {
    copy(text);
    return;
  }
  const start = el.selectionStart ?? el.value.length;
  const end = el.selectionEnd ?? el.value.length;
  el.value = el.value.slice(0, start) + text + el.value.slice(end);
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.focus();
  el.setSelectionRange(start + text.length, start + text.length);
}

// noop import-keeper so Copy isn't tree-shaken into nothing in dev
export const __copyIcon = Copy;
