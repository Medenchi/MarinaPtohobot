import { useEffect, useState } from "react";
import { Pencil, Plus, Trash, UploadSimple, X } from "@phosphor-icons/react";
import {
  deleteOutfit,
  deleteOutfitImage,
  listOutfits,
  outfitImageUrl,
  uploadOutfitImage,
  upsertOutfit,
} from "@/lib/api";
import { TextArea, TextField, Switch } from "@/components/Field";
import MamaLayout from "./Layout";
import type { Outfit, OutfitImage } from "@/types";

type OutfitWithImages = Outfit & { outfit_images: OutfitImage[] };

export default function Outfits() {
  const [outfits, setOutfits] = useState<OutfitWithImages[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<OutfitWithImages | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const rows = await listOutfits();
      setOutfits(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
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
      await upsertOutfit(o);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function remove(id: number) {
    if (!confirm("Удалить образ?")) return;
    try {
      await deleteOutfit(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function uploadImage(outfitId: number, file: File) {
    try {
      await uploadOutfitImage(outfitId, file);
      await load();
      // Re-open the same outfit with refreshed images.
      const fresh = (await listOutfits()).find((o) => o.id === outfitId);
      if (fresh) setEditing(fresh);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function removeImage(img: OutfitImage) {
    if (!confirm("Удалить картинку?")) return;
    try {
      await deleteOutfitImage(img);
      await load();
      if (editing) {
        const fresh = (await listOutfits()).find((o) => o.id === editing.id);
        if (fresh) setEditing(fresh);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  if (editing) {
    return (
      <MamaLayout>
        <OutfitForm
          initial={editing}
          onSave={save}
          onCancel={() => setEditing(null)}
          onUploadImage={uploadImage}
          onRemoveImage={removeImage}
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
              outfit_images: [],
            })
          }
          className="btn-primary"
        >
          <Plus size={14} weight="thin" /> Добавить образ
        </button>
      </div>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      {loading ? (
        <p className="text-sm text-muted">Загрузка…</p>
      ) : outfits.length === 0 ? (
        <p className="card text-sm text-muted text-center py-12">Пока ни одного образа.</p>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {outfits.map((o) => (
            <li key={o.id} className="card">
              {o.outfit_images?.[0] && (
                <img
                  src={outfitImageUrl(o.outfit_images[0].storage_path)}
                  alt=""
                  className="w-full h-32 object-cover rounded mb-2"
                />
              )}
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
  onRemoveImage,
  error,
}: {
  initial: OutfitWithImages;
  onSave: (o: Partial<Outfit>) => Promise<void>;
  onCancel: () => void;
  onUploadImage: (id: number, f: File) => Promise<void>;
  onRemoveImage: (img: OutfitImage) => Promise<void>;
  error?: string | null;
}) {
  const [form, setForm] = useState<OutfitWithImages>(initial);
  function patch<K extends keyof OutfitWithImages>(key: K, value: OutfitWithImages[K]) {
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
          <div className="flex flex-wrap gap-2 mb-2">
            {(form.outfit_images || []).map((img) => (
              <div key={img.id} className="relative">
                <img
                  src={outfitImageUrl(img.storage_path)}
                  alt=""
                  className="w-20 h-20 object-cover rounded border border-line"
                />
                <button
                  onClick={() => void onRemoveImage(img)}
                  className="absolute -top-1 -right-1 bg-white border border-line rounded-full p-0.5 hover:text-red-600"
                  title="Удалить картинку"
                >
                  <X size={10} weight="thin" />
                </button>
              </div>
            ))}
            {(form.outfit_images || []).length === 0 && (
              <p className="text-xs text-muted">пока пусто</p>
            )}
          </div>
          <label className="btn-outline cursor-pointer">
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
