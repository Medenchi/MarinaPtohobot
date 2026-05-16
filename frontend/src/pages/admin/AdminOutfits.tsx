import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Trash,
  PencilSimple,
  X,
  Image as ImageIcon,
  CloudArrowUp,
} from "@phosphor-icons/react";
import { api, apiUpload } from "@/lib/api";
import Footer from "@/components/Footer";
import Spinner from "@/components/Spinner";

interface OutfitImage {
  id: number;
  storage_path: string;
  caption: string | null;
}

interface Outfit {
  id: number;
  title: string;
  description: string | null;
  colors: string;
  styles: string;
  seasons: string;
  occasions: string;
  body_types: string;
  budgets: string;
  shoot_types: string;
  price_hint: string | null;
  external_url: string | null;
  sort_order: number;
  is_published: boolean;
  outfit_images: OutfitImage[];
}

const empty: Omit<Outfit, "id" | "outfit_images"> = {
  title: "",
  description: "",
  colors: "",
  styles: "",
  seasons: "",
  occasions: "",
  body_types: "",
  budgets: "",
  shoot_types: "",
  price_hint: "",
  external_url: "",
  sort_order: 0,
  is_published: true,
};

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "";
const BUCKET = "outfit-images";

export default function AdminOutfits() {
  const navigate = useNavigate();
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Outfit | null>(null);
  const [form, setForm] = useState(empty);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionStorage.getItem("admin_token")) {
      navigate("/admin");
    }
  }, [navigate]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api<Outfit[]>("/api/admin/outfits");
      setOutfits(data);
    } catch {
      setError("Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function openCreate() {
    setEditing(null);
    setForm(empty);
  }

  function openEdit(o: Outfit) {
    setEditing(o);
    setForm({
      title: o.title,
      description: o.description || "",
      colors: o.colors,
      styles: o.styles,
      seasons: o.seasons,
      occasions: o.occasions,
      body_types: o.body_types,
      budgets: o.budgets,
      shoot_types: o.shoot_types,
      price_hint: o.price_hint || "",
      external_url: o.external_url || "",
      sort_order: o.sort_order,
      is_published: o.is_published,
    });
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editing) {
        await api(`/api/admin/outfits/${editing.id}`, {
          method: "PATCH",
          body: JSON.stringify(form),
        });
      } else {
        await api("/api/admin/outfits", {
          method: "POST",
          body: JSON.stringify(form),
        });
      }
      setEditing(null);
      setForm(empty);
      await load();
    } catch {
      setError("Не удалось сохранить");
    }
  }

  async function remove(id: number) {
    if (!confirm("Удалить образ?")) return;
    await api(`/api/admin/outfits/${id}`, { method: "DELETE" });
    await load();
  }

  async function uploadImage(outfitId: number, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    await apiUpload(`/api/admin/outfits/${outfitId}/images`, fd);
    await load();
  }

  async function removeImage(imageId: number) {
    await api(`/api/admin/outfit-images/${imageId}`, { method: "DELETE" });
    await load();
  }

  if (loading) return <Spinner />;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-line flex items-center justify-between">
        <Link to="/admin/dashboard" className="flex items-center gap-2 text-sm">
          <ArrowLeft size={16} weight="bold" /> Назад
        </Link>
        <h1 className="serif-heading text-xl">Образы</h1>
        <button
          onClick={openCreate}
          className="text-sm flex items-center gap-1 hover:underline"
        >
          <Plus size={16} weight="bold" /> Создать
        </button>
      </header>

      <main className="flex-1 px-6 py-6 max-w-4xl mx-auto w-full">
        {error && <p className="text-red-500 mb-4">{error}</p>}

        {!editing && form === empty && outfits.length === 0 && (
          <p className="text-muted text-center py-10">Пока нет образов</p>
        )}

        {(editing || Object.values(form).some(Boolean)) && (
          <form onSubmit={save} className="card mb-6 space-y-3">
            <div className="flex items-center justify-between mb-2">
              <h2 className="serif-heading text-lg">
                {editing ? "Редактировать образ" : "Новый образ"}
              </h2>
              <button
                type="button"
                onClick={() => {
                  setEditing(null);
                  setForm(empty);
                }}
                className="text-muted hover:text-ink"
              >
                <X size={20} />
              </button>
            </div>

            <Field
              label="Название"
              value={form.title}
              onChange={(v) => setForm({ ...form, title: v })}
              required
            />
            <Field
              label="Описание"
              value={form.description || ""}
              onChange={(v) => setForm({ ...form, description: v })}
              textarea
            />
            <Field
              label="Цвета (через запятую: бежевый, белый)"
              value={form.colors}
              onChange={(v) => setForm({ ...form, colors: v })}
            />
            <Field
              label="Стиль (casual, романтичный)"
              value={form.styles}
              onChange={(v) => setForm({ ...form, styles: v })}
            />
            <Field
              label="Сезоны (зима, весна, лето, осень)"
              value={form.seasons}
              onChange={(v) => setForm({ ...form, seasons: v })}
            />
            <Field
              label="Поводы (повседневно, праздник)"
              value={form.occasions}
              onChange={(v) => setForm({ ...form, occasions: v })}
            />
            <Field
              label="Тип фигуры (если есть)"
              value={form.body_types}
              onChange={(v) => setForm({ ...form, body_types: v })}
            />
            <Field
              label="Бюджет (эконом, средний, премиум)"
              value={form.budgets}
              onChange={(v) => setForm({ ...form, budgets: v })}
            />
            <Field
              label="Тип съёмки (студия, улица, людное место)"
              value={form.shoot_types}
              onChange={(v) => setForm({ ...form, shoot_types: v })}
            />
            <Field
              label="Цена (текстом)"
              value={form.price_hint || ""}
              onChange={(v) => setForm({ ...form, price_hint: v })}
            />
            <Field
              label="Внешняя ссылка"
              value={form.external_url || ""}
              onChange={(v) => setForm({ ...form, external_url: v })}
            />

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_published}
                onChange={(e) =>
                  setForm({ ...form, is_published: e.target.checked })
                }
              />
              Опубликовано
            </label>

            <button type="submit" className="btn-primary">
              Сохранить
            </button>
          </form>
        )}

        <ul className="space-y-3">
          {outfits.map((o) => (
            <li key={o.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="serif-heading text-lg">
                    {o.title}
                    {!o.is_published && (
                      <span className="ml-2 text-xs text-muted">(скрыт)</span>
                    )}
                  </h3>
                  {o.description && (
                    <p className="text-sm text-muted">{o.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => openEdit(o)}
                    className="p-2 text-muted hover:text-ink"
                  >
                    <PencilSimple size={16} />
                  </button>
                  <button
                    onClick={() => remove(o.id)}
                    className="p-2 text-muted hover:text-red-500"
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mt-2">
                {o.outfit_images.map((img) => (
                  <div key={img.id} className="relative w-20 h-20">
                    <img
                      src={`${SUPABASE_URL}/storage/v1/object/public/${BUCKET}/${img.storage_path}`}
                      alt=""
                      className="w-full h-full object-cover rounded border border-line"
                    />
                    <button
                      onClick={() => removeImage(img.id)}
                      className="absolute -top-1 -right-1 bg-ink text-paper rounded-full p-0.5"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
                <label className="w-20 h-20 flex items-center justify-center border border-dashed border-line rounded cursor-pointer hover:bg-line/30 text-muted">
                  <CloudArrowUp size={20} />
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void uploadImage(o.id, f);
                    }}
                  />
                </label>
              </div>

              {o.outfit_images.length === 0 && (
                <p className="text-xs text-muted flex items-center gap-1 mt-2">
                  <ImageIcon size={14} /> Нет фото — добавь хотя бы одно
                </p>
              )}
            </li>
          ))}
        </ul>
      </main>
      <Footer />
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  required,
  textarea,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  textarea?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-muted">{label}</span>
      {textarea ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          rows={3}
          className="rounded-lg border border-line px-3 py-2 text-sm focus:border-ink outline-none"
        />
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          className="rounded-lg border border-line px-3 py-2 text-sm focus:border-ink outline-none"
        />
      )}
    </label>
  );
}
