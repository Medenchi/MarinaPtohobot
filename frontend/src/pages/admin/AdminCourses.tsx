import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Trash,
  PencilSimple,
  X,
  CloudArrowUp,
  File as FileIcon,
} from "@phosphor-icons/react";
import { api, apiUpload } from "@/lib/api";
import Footer from "@/components/Footer";
import Spinner from "@/components/Spinner";

interface CourseFile {
  id: number;
  title: string;
  storage_path: string;
  mime_type: string;
  size_bytes: number | null;
}

interface Course {
  id: number;
  slug: string;
  title: string;
  short_description: string | null;
  description: string | null;
  cover_path: string | null;
  sort_order: number;
  is_published: boolean;
  course_files: CourseFile[];
}

const empty: Omit<Course, "id" | "course_files"> = {
  slug: "",
  title: "",
  short_description: "",
  description: "",
  cover_path: null,
  sort_order: 0,
  is_published: true,
};

export default function AdminCourses() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Course | null>(null);
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
      const data = await api<Course[]>("/api/admin/courses");
      setCourses(data);
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

  function openEdit(c: Course) {
    setEditing(c);
    setForm({
      slug: c.slug,
      title: c.title,
      short_description: c.short_description || "",
      description: c.description || "",
      cover_path: c.cover_path,
      sort_order: c.sort_order,
      is_published: c.is_published,
    });
  }

  async function save(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (editing) {
        await api(`/api/admin/courses/${editing.id}`, {
          method: "PATCH",
          body: JSON.stringify(form),
        });
      } else {
        await api("/api/admin/courses", {
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
    if (!confirm("Удалить курс?")) return;
    await api(`/api/admin/courses/${id}`, { method: "DELETE" });
    await load();
  }

  async function uploadFile(courseId: number, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", file.name);
    await apiUpload(`/api/admin/courses/${courseId}/files`, fd);
    await load();
  }

  async function removeFile(fileId: number) {
    await api(`/api/admin/course-files/${fileId}`, { method: "DELETE" });
    await load();
  }

  if (loading) return <Spinner />;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-line flex items-center justify-between">
        <Link to="/admin/dashboard" className="flex items-center gap-2 text-sm">
          <ArrowLeft size={16} weight="bold" /> Назад
        </Link>
        <h1 className="serif-heading text-xl">Курсы</h1>
        <button
          onClick={openCreate}
          className="text-sm flex items-center gap-1 hover:underline"
        >
          <Plus size={16} weight="bold" /> Создать
        </button>
      </header>

      <main className="flex-1 px-6 py-6 max-w-4xl mx-auto w-full">
        {error && <p className="text-red-500 mb-4">{error}</p>}

        {(editing || form.title || form.slug) && (
          <form onSubmit={save} className="card mb-6 space-y-3">
            <div className="flex items-center justify-between mb-2">
              <h2 className="serif-heading text-lg">
                {editing ? "Редактировать курс" : "Новый курс"}
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
              label="Slug (латиницей, для ссылок)"
              value={form.slug}
              onChange={(v) => setForm({ ...form, slug: v })}
              required
            />
            <Field
              label="Название"
              value={form.title}
              onChange={(v) => setForm({ ...form, title: v })}
              required
            />
            <Field
              label="Короткое описание"
              value={form.short_description || ""}
              onChange={(v) => setForm({ ...form, short_description: v })}
            />
            <Field
              label="Полное описание"
              value={form.description || ""}
              onChange={(v) => setForm({ ...form, description: v })}
              textarea
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
          {courses.map((c) => (
            <li key={c.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="serif-heading text-lg">
                    {c.title}
                    {!c.is_published && (
                      <span className="ml-2 text-xs text-muted">(скрыт)</span>
                    )}
                  </h3>
                  {c.short_description && (
                    <p className="text-sm text-muted">{c.short_description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => openEdit(c)}
                    className="p-2 text-muted hover:text-ink"
                  >
                    <PencilSimple size={16} />
                  </button>
                  <button
                    onClick={() => remove(c.id)}
                    className="p-2 text-muted hover:text-red-500"
                  >
                    <Trash size={16} />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                {c.course_files.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between text-sm py-1 border-b border-line/50 last:border-0"
                  >
                    <span className="flex items-center gap-2 truncate">
                      <FileIcon size={14} />
                      {f.title}
                    </span>
                    <button
                      onClick={() => removeFile(f.id)}
                      className="text-muted hover:text-red-500 p-1"
                    >
                      <Trash size={14} />
                    </button>
                  </div>
                ))}
                <label className="flex items-center gap-2 cursor-pointer text-sm text-muted hover:text-ink py-2 border border-dashed border-line rounded px-3">
                  <CloudArrowUp size={16} />
                  Загрузить файл (pdf, видео, картинка...)
                  <input
                    type="file"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void uploadFile(c.id, f);
                    }}
                  />
                </label>
              </div>
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
