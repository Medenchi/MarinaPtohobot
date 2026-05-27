import { useEffect, useState } from "react";
import { Pencil, Plus, Trash, UploadSimple } from "@phosphor-icons/react";
import {
  deleteCourse,
  listCourses,
  uploadCourseFile,
  upsertCourse,
} from "@/lib/api";
import { TextArea, TextField, Switch } from "@/components/Field";
import MamaLayout from "./Layout";
import type { Course } from "@/types";

export default function Courses() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Course | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const rows = await listCourses();
      setCourses(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);

  async function save(c: Partial<Course>) {
    setError(null);
    try {
      await upsertCourse(c);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function remove(id: number) {
    if (!confirm("Удалить курс?")) return;
    try {
      await deleteCourse(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function uploadFile(courseId: number, file: File) {
    try {
      await uploadCourseFile(courseId, file);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  if (editing) {
    return (
      <MamaLayout>
        <CourseForm
          initial={editing}
          onSave={save}
          onCancel={() => setEditing(null)}
          onUploadFile={uploadFile}
          error={error}
        />
      </MamaLayout>
    );
  }

  return (
    <MamaLayout>
      <div className="flex justify-between items-center mb-4">
        <h2 className="serif-heading text-2xl">Курсы</h2>
        <button
          onClick={() =>
            setEditing({
              id: 0,
              slug: "",
              title: "",
              description: "",
              storage_path: null,
              cover_path: null,
              preview_pages: 3,
              is_published: true,
              sort_order: 0,
            })
          }
          className="btn-primary"
        >
          <Plus size={14} weight="thin" /> Новый курс
        </button>
      </div>
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}
      {loading ? (
        <p className="text-sm text-muted">Загрузка…</p>
      ) : courses.length === 0 ? (
        <p className="card text-sm text-muted text-center py-12">Пока пусто.</p>
      ) : (
        <ul className="space-y-2">
          {courses.map((c) => (
            <li key={c.id} className="card flex justify-between items-start gap-2">
              <div className="min-w-0">
                <h3 className="font-medium truncate">{c.title}</h3>
                <p className="text-xs text-muted truncate">{c.description}</p>
                <p className="text-[10px] text-muted">slug: {c.slug}</p>
                {!c.is_published && <span className="text-[10px] text-red-600">черновик</span>}
              </div>
              <div className="flex gap-1 shrink-0">
                <button onClick={() => setEditing(c)} className="text-muted hover:text-ink">
                  <Pencil size={16} weight="thin" />
                </button>
                <button onClick={() => remove(c.id)} className="text-muted hover:text-red-600">
                  <Trash size={16} weight="thin" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </MamaLayout>
  );
}

function CourseForm({
  initial,
  onSave,
  onCancel,
  onUploadFile,
  error,
}: {
  initial: Course;
  onSave: (c: Partial<Course>) => Promise<void>;
  onCancel: () => void;
  onUploadFile: (id: number, f: File) => Promise<void>;
  error?: string | null;
}) {
  const [form, setForm] = useState<Course>(initial);
  function patch<K extends keyof Course>(key: K, value: Course[K]) {
    setForm((p) => ({ ...p, [key]: value }));
  }
  return (
    <div className="card space-y-3 max-w-2xl mx-auto">
      <h2 className="serif-heading text-2xl">{form.id ? "Редактировать курс" : "Новый курс"}</h2>
      <TextField label="Slug" value={form.slug} onChange={(e) => patch("slug", e.target.value)} />
      <TextField label="Название" value={form.title} onChange={(e) => patch("title", e.target.value)} />
      <TextArea label="Описание" value={form.description || ""} onChange={(e) => patch("description", e.target.value)} />
      <TextField
        label="Preview-страниц"
        type="number"
        value={form.preview_pages}
        onChange={(e) => patch("preview_pages", Number(e.target.value))}
      />
      <Switch label="Опубликован" checked={form.is_published} onChange={(v) => patch("is_published", v)} />

      {form.id > 0 && (
        <div>
          <span className="block text-xs uppercase tracking-tighter text-muted mb-1">PDF файл</span>
          <p className="text-xs text-muted mb-1">
            {form.storage_path || "не загружен"}
          </p>
          <label className="btn-outline cursor-pointer">
            <UploadSimple size={14} weight="thin" /> Загрузить PDF
            <input
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void onUploadFile(form.id, f);
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
