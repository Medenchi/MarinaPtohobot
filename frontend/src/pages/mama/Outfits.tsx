import { useEffect, useState } from "react";
import { Pencil, Plus, Trash, UploadSimple } from "@phosphor-icons/react";
import { api, API_BASE, tokenFor } from "@/lib/api";
import { TextArea, TextField, Switch } from "@/components/Field";
import MamaLayout from "./Layout";
import type { Outfit } from "@/types";

export default function Outfits() {
  const [outfits, setOutfits] = useState<Outfit[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Outfit | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const rows = await api.mama.get<Outfit[]>("/api/admin/outfits");
      setOutfits(rows);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);

  async function save(o: Partial<Outfit>) {
    setError(null);
    try {
      if ("id" in o && o.id) {
        await api.mama.patch(`/api/admin/outfits/${o.id}`, o);
      } else {
        await api.mama.post("/api/admin/outfits", o);
      }
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function remove(id: number) {
    if (!confirm("Удалить образ?")) return;
    await api.mama.del(`/api/admin/outfits/${id}`);
    await load();
  }

  async function uploadImage(outfitId: number, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const token = tokenFor("mama");
    const resp = await fetch(`${API_BASE}/api/admin/outfits/${outfitId}/images`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    });
    if (!resp.ok) {
      alert("Не удалось загрузить");
      return;
    }
    await load();
  }

  if (editing) {
    return (
      <MamaLayout>
        <OutfitForm
          initial={editing}
          onSave={save}
          onCancel={() => setEditing(null)}
          onUploadImage={uploadImage}
          error={error}
        />
      </MamaLayout>
    );
  }

  return (
    <MamaLayout>
      <div className="flex justify-between items-center mb-4">
        <h2 className="serif-heading text-2xl">Образы</h2>
        <button
          onClick={() =>
            setEditing({
              id: 0,
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
              pinterest_url: "",
              tags: null,
              sort_order: 0,
              is_published: true,
            })
          }
          className="btn-primary"
        >
          <Plus size={14} weight="thin" /> Добавить образ
        </button>
      </div>
      {loading ? (
        <p className="text-sm text-muted">Загрузка…</p>
      ) : outfits.length === 0 ? (
        <p className="card text-sm text-muted text-center py-12">Пока ни одного образа.</p>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {outfits.map((o) => (
            <li key={o.id} className="card">
              <div className="flex justify-between items-start gap-2">
                <div className="min-w-0">
                  <h3 className="font-medium truncate">{o.title}</h3>
                  <p className="text-xs text-muted truncate">{o.description}</p>
                  <p className="text-[10px] text-muted mt-1">
                    {[o.colors, o.styles, o.seasons].filter(Boolean).join(" · ")}
                  </p>
                  {!o.is_published && (
                    <span className="text-[10px] text-red-600">черновик</span>
                  )}
                </div>
                <div className="flex gap-1 shrink-0">
                  <button
                    onClick={() => setEditing(o)}
                    className="text-muted hover:text-ink"
                    title="Редактировать"
                  >
                    <Pencil size={16} weight="thin" />
                  </button>
                  <button
                    onClick={() => remove(o.id)}
                    className="text-muted hover:text-red-600"
                    title="Удалить"
                  >
                    <Trash size={16} weight="thin" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </MamaLayout>
  );
}

function OutfitForm({
  initial,
  onSave,
  onCancel,
  onUploadImage,
  error,
}: {
  initial: Outfit;
  onSave: (o: Partial<Outfit>) => Promise<void>;
  onCancel: () => void;
  onUploadImage: (id: number, f: File) => Promise<void>;
  error?: string | null;
}) {
  const [form, setForm] = useState<Outfit>(initial);
  function patch<K extends keyof Outfit>(key: K, value: Outfit[K]) {
    setForm((p) => ({ ...p, [key]: value }));
  }
  return (
    <div className="card space-y-3 max-w-2xl mx-auto">
      <h2 className="serif-heading text-2xl">{form.id ? "Редактировать образ" : "Новый образ"}</h2>
      <TextField
        label="Название"
        value={form.title}
        onChange={(e) => patch("title", e.target.value)}
      />
      <TextArea
        label="Описание"
        value={form.description || ""}
        onChange={(e) => patch("description", e.target.value)}
      />
      <div className="grid grid-cols-2 gap-2">
        <TextField label="Цвета (через ,)" value={form.colors} onChange={(e) => patch("colors", e.target.value)} />
        <TextField label="Стили (через ,)" value={form.styles} onChange={(e) => patch("styles", e.target.value)} />
        <TextField label="Сезоны (через ,)" value={form.seasons} onChange={(e) => patch("seasons", e.target.value)} />
        <TextField label="Поводы (через ,)" value={form.occasions} onChange={(e) => patch("occasions", e.target.value)} />
        <TextField label="Фигура (через ,)" value={form.body_types} onChange={(e) => patch("body_types", e.target.value)} />
        <TextField label="Бюджет (через ,)" value={form.budgets} onChange={(e) => patch("budgets", e.target.value)} />
        <TextField label="Тип съёмки (через ,)" value={form.shoot_types} onChange={(e) => patch("shoot_types", e.target.value)} />
        <TextField label="Цена (текст)" value={form.price_hint || ""} onChange={(e) => patch("price_hint", e.target.value)} />
      </div>
      <TextField
        label="Ссылка на образ"
        value={form.external_url || ""}
        onChange={(e) => patch("external_url", e.target.value)}
      />
      <TextField
        label="Pinterest борда"
        value={form.pinterest_url || ""}
        onChange={(e) => patch("pinterest_url", e.target.value)}
      />
      <Switch
        label="Опубликован"
        checked={form.is_published}
        onChange={(v) => patch("is_published", v)}
      />

      {form.id > 0 && (
        <div>
          <span className="block text-xs uppercase tracking-tighter text-muted mb-1">Картинки</span>
          <div className="flex flex-wrap gap-2">
            {(form.outfit_images || []).map((img) => (
              <span key={img.id} className="text-[10px] text-muted">{img.storage_path}</span>
            ))}
          </div>
          <label className="btn-outline mt-2 cursor-pointer">
            <UploadSimple size={14} weight="thin" /> Загрузить картинку
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void onUploadImage(form.id, f);
                e.target.value = "";
              }}
            />
          </label>
        </div>
      )}

      {error && <p className="text-xs text-red-600">{error}</p>}

      <div className="flex gap-2 justify-end pt-2">
        <button onClick={onCancel} className="btn-outline">
          Отмена
        </button>
        <button onClick={() => void onSave(form)} className="btn-primary">
          Сохранить
        </button>
      </div>
    </div>
  );
}
