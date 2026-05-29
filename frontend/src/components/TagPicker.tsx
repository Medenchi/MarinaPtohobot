/**
 * Multi-select по справочнику outfit_categories.
 *
 * Внутри хранится **строка через запятую** — ровно как в БД (outfits.colors
 * и т.д.). Снаружи компонент выглядит как набор тегов-чипсов: клик добавляет
 * / удаляет. Плюс свободный ввод нового тега (на случай, когда нужного нет
 * в справочнике; админ позже добавит его через /admin/categories).
 */

import { useMemo, useState } from "react";
import { Plus, X } from "@phosphor-icons/react";
import type { CategoryKind, OutfitCategory } from "@/lib/api";

interface Props {
  label: string;
  kind: CategoryKind;
  value: string; // comma-separated
  options: OutfitCategory[];
  onChange: (next: string) => void;
}

function toList(s: string): string[] {
  return (s || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}
function fromList(xs: string[]): string {
  return Array.from(new Set(xs.map((x) => x.trim()).filter(Boolean))).join(", ");
}

export default function TagPicker({ label, kind, value, options, onChange }: Props) {
  const [adding, setAdding] = useState(false);
  const [custom, setCustom] = useState("");
  const selected = useMemo(() => new Set(toList(value)), [value]);
  const filtered = useMemo(
    () => options.filter((o) => o.kind === kind),
    [options, kind],
  );

  function toggle(v: string) {
    const list = toList(value);
    if (selected.has(v)) onChange(fromList(list.filter((x) => x !== v)));
    else onChange(fromList([...list, v]));
  }

  function addCustom() {
    const v = custom.trim();
    if (!v) {
      setAdding(false);
      return;
    }
    onChange(fromList([...toList(value), v]));
    setCustom("");
    setAdding(false);
  }

  return (
    <div>
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">
        {label}
      </span>
      <div className="flex flex-wrap gap-1.5 p-2 border border-line rounded-md bg-white min-h-[42px]">
        {/* Выбранные */}
        {toList(value).map((v) => (
          <button
            key={`sel-${v}`}
            onClick={() => toggle(v)}
            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-ink text-white hover:bg-ink/80"
            title="Снять"
            type="button"
          >
            {v}
            <X size={10} weight="bold" />
          </button>
        ))}
        {/* Доступные из справочника */}
        {filtered
          .filter((o) => !selected.has(o.value))
          .map((o) => (
            <button
              key={o.id}
              onClick={() => toggle(o.value)}
              className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border border-line text-muted hover:border-ink hover:text-ink"
              type="button"
            >
              <Plus size={10} weight="thin" />
              {o.value}
            </button>
          ))}
        {/* Свободный ввод (если справочника не хватает) */}
        {adding ? (
          <span className="inline-flex items-center gap-1">
            <input
              autoFocus
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") addCustom();
                if (e.key === "Escape") {
                  setAdding(false);
                  setCustom("");
                }
              }}
              onBlur={addCustom}
              placeholder="свой вариант"
              className="text-xs px-2 py-1 rounded-full border border-ink focus:outline-none"
              style={{ width: 120 }}
            />
          </span>
        ) : (
          <button
            onClick={() => setAdding(true)}
            className="text-xs px-2 py-1 rounded-full border border-dashed border-line text-muted hover:border-ink hover:text-ink"
            type="button"
            title="Добавить свой вариант"
          >
            + ещё
          </button>
        )}
      </div>
    </div>
  );
}
