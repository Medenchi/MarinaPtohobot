/**
 * Управление справочником outfit_categories. Доступно только админу
 * (Денису). Семь типов: Цвета / Стили / Сезоны / Поводы / Фигура /
 * Бюджет / Тип съёмки.
 *
 * UX: семь карточек, в каждой — список существующих значений (кнопка ×
 * рядом), плюс поле «добавить». Все изменения сразу пишутся в Supabase.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Trash } from "@phosphor-icons/react";
import {
  CATEGORY_KINDS,
  addCategory,
  deleteCategory,
  listCategories,
  type CategoryKind,
  type OutfitCategory,
} from "@/lib/api";
import Footer from "@/components/Footer";

export default function Categories() {
  const [rows, setRows] = useState<OutfitCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    setLoading(true);
    try {
      setRows(await listCategories());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  async function add(kind: CategoryKind, value: string) {
    if (!value.trim()) return;
    try {
      await addCategory(kind, value);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(id: number) {
    try {
      await deleteCategory(id);
      setRows((r) => r.filter((x) => x.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <header className="border-b border-line bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link to="/admin" className="text-xs text-muted hover:text-ink">
            ← к флоу
          </Link>
          <h1 className="serif-heading text-xl">Категории</h1>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        <p className="text-sm text-muted mb-4">
          Эти значения видит Марина в выпадашках при редактировании образов.
          Можно безопасно добавлять/убирать — на уже сохранённых образах ничего
          не сломается (там они хранятся как обычный текст через запятую).
        </p>

        {error && (
          <p className="text-xs text-red-600 mb-3 card border-red-200 bg-red-50">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-sm text-muted">Загрузка…</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {CATEGORY_KINDS.map((k) => (
              <KindCard
                key={k.kind}
                kind={k.kind}
                title={k.label}
                items={rows.filter((r) => r.kind === k.kind)}
                onAdd={(v) => void add(k.kind, v)}
                onRemove={remove}
              />
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

function KindCard({
  kind,
  title,
  items,
  onAdd,
  onRemove,
}: {
  kind: CategoryKind;
  title: string;
  items: OutfitCategory[];
  onAdd: (v: string) => void;
  onRemove: (id: number) => void;
}) {
  const [input, setInput] = useState("");
  return (
    <div className="card space-y-2">
      <div className="flex items-baseline justify-between">
        <h3 className="font-medium">{title}</h3>
        <span className="text-[10px] text-muted font-mono">{kind}</span>
      </div>
      <div className="flex flex-wrap gap-1.5 min-h-[28px]">
        {items.length === 0 && (
          <span className="text-xs text-muted">пусто</span>
        )}
        {items.map((it) => (
          <span
            key={it.id}
            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-paper border border-line"
          >
            {it.value}
            <button
              onClick={() => onRemove(it.id)}
              className="text-muted hover:text-red-600"
              title="Удалить"
            >
              <Trash size={10} weight="thin" />
            </button>
          </span>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onAdd(input);
          setInput("");
        }}
        className="flex gap-1 pt-1"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="новое значение"
          className="flex-1 text-xs border border-line rounded px-2 py-1 focus:outline-none focus:border-ink"
        />
        <button type="submit" className="btn-outline text-xs px-2 py-1">
          <Plus size={12} weight="thin" /> Добавить
        </button>
      </form>
    </div>
  );
}
