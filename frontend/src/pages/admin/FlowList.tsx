import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CaretRight,
  CloudArrowUp,
  Copy,
  DownloadSimple,
  Plus,
  Sparkle,
  Trash,
  UploadSimple,
} from "@phosphor-icons/react";
import {
  createFlow,
  deleteFlow,
  duplicateFlow,
  getFlow,
  listFlows,
} from "@/lib/api";
import { clearToken } from "@/lib/supabase";
import { downloadJson, readJsonFile } from "@/lib/util";
import { SEED_GRAPH } from "@/lib/seedGraph";
import Footer from "@/components/Footer";
import type { FlowSummary } from "@/types";

export default function FlowList() {
  const [flows, setFlows] = useState<FlowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const rows = await listFlows();
      setFlows(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);

  async function newFlow() {
    setBusy(true);
    try {
      const f = await createFlow({
        name: "Новый флоу",
        description: "",
        graph: { nodes: [], edges: [] },
      });
      navigate(`/admin/flows/${f.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function seedFlow() {
    setBusy(true);
    try {
      const f = await createFlow({
        name: "Стартовый флоу: квиз + образы",
        description:
          "Шаблон: /start → серия вопросов → подбор образов из таблицы outfits → выдача с водяным знаком.",
        graph: SEED_GRAPH,
      });
      navigate(`/admin/flows/${f.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function duplicate(id: string) {
    setBusy(true);
    try {
      await duplicateFlow(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function exportFlow(id: string, name: string) {
    const f = await getFlow(id);
    downloadJson(
      { name: f.name, description: f.description, graph: f.graph },
      `${name.replace(/\s+/g, "_")}.flow.json`,
    );
  }

  async function importFlow(file: File) {
    setBusy(true);
    try {
      const data = await readJsonFile<{ name?: string; description?: string; graph: unknown }>(file);
      const f = await createFlow({
        name: data.name || file.name.replace(/\.flow\.json$/, ""),
        description: data.description ?? undefined,
        graph: data.graph,
      });
      navigate(`/admin/flows/${f.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function removeFlow(id: string) {
    if (!confirm("Удалить флоу?")) return;
    setBusy(true);
    try {
      await deleteFlow(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    clearToken("admin");
    navigate("/admin/login");
  }

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <header className="border-b border-line bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="serif-heading text-xl">Конструктор</h1>
          <div className="flex gap-3">
            <Link to="/admin/bots" className="text-xs text-muted hover:text-ink">
              боты
            </Link>
            <Link to="/admin/categories" className="text-xs text-muted hover:text-ink">
              категории
            </Link>
            <Link to="/" className="text-xs text-muted hover:text-ink">
              ← на главную
            </Link>
            <button onClick={logout} className="text-xs text-muted hover:text-ink">
              выйти
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <div className="flex flex-wrap gap-2 mb-6">
          <button onClick={newFlow} className="btn-primary" disabled={busy}>
            <Plus size={16} weight="thin" /> Новый флоу
          </button>
          <button onClick={seedFlow} className="btn-outline" disabled={busy}>
            <Sparkle size={16} weight="thin" /> Стартовый шаблон
          </button>
          <label className="btn-outline cursor-pointer">
            <UploadSimple size={16} weight="thin" /> Импорт
            <input
              type="file"
              accept="application/json,.json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) void importFlow(f);
                e.target.value = "";
              }}
            />
          </label>
        </div>

        {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

        {loading ? (
          <p className="text-sm text-muted">Загрузка…</p>
        ) : flows.length === 0 ? (
          <div className="card text-center text-sm text-muted py-12">
            Пока ни одного флоу. Создай новый или вставь стартовый шаблон.
          </div>
        ) : (
          <ul className="space-y-2">
            {flows.map((f) => (
              <li key={f.id} className="card flex items-center gap-3">
                <Link to={`/admin/flows/${f.id}`} className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{f.name}</span>
                    {f.is_published && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-ink text-paper">
                        опубликован
                      </span>
                    )}
                    <span className="text-[10px] text-muted">v{f.version}</span>
                  </div>
                  {f.description && (
                    <p className="text-xs text-muted truncate">{f.description}</p>
                  )}
                </Link>
                <button
                  onClick={() => duplicate(f.id)}
                  className="text-muted hover:text-ink"
                  title="Дублировать"
                >
                  <Copy size={18} weight="thin" />
                </button>
                <button
                  onClick={() => exportFlow(f.id, f.name)}
                  className="text-muted hover:text-ink"
                  title="Экспорт"
                >
                  <DownloadSimple size={18} weight="thin" />
                </button>
                <button
                  onClick={() => removeFlow(f.id)}
                  className="text-muted hover:text-red-600"
                  title="Удалить"
                >
                  <Trash size={18} weight="thin" />
                </button>
                <Link
                  to={`/admin/flows/${f.id}`}
                  className="text-ink"
                  title="Открыть"
                >
                  <CaretRight size={18} weight="thin" />
                </Link>
              </li>
            ))}
          </ul>
        )}

        <p className="text-xs text-muted mt-6 inline-flex items-center gap-1">
          <CloudArrowUp size={14} weight="thin" /> Сохранения автоматические. Публикация — внутри
          флоу.
        </p>
      </main>
      <Footer />
    </div>
  );
}
