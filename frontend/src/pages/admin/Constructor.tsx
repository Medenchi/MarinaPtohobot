import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowSquareOut,
  CheckCircle,
  Eye,
  FloppyDisk,
  Plus,
  Trash,
} from "@phosphor-icons/react";
import {
  getFlow,
  previewFlow,
  publishFlow,
  unpublishFlow,
  updateFlow,
} from "@/lib/api";
import {
  BLOCK_GROUPS,
  BLOCK_SCHEMAS,
  type BlockField,
  schemaFor,
} from "@/lib/blockSchemas";
import { classNames, shortId } from "@/lib/util";
import { TextField, TextArea, Switch } from "@/components/Field";
import Footer from "@/components/Footer";
import type { BlockNode, Flow, FlowGraph } from "@/types";

const PREVIEW_KEY = "marina:preview-tg-id";

export default function Constructor() {
  const { id = "" } = useParams<{ id: string }>();
  const [flow, setFlow] = useState<Flow | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFlow(id)
      .then((f) => {
        if (!f.graph || !Array.isArray(f.graph.nodes)) {
          f.graph = { nodes: [], edges: [] };
        }
        setFlow(f);
      })
      .catch((err) => setError(err.message || String(err)));
  }, [id]);

  const debouncedSave = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (!flow || !dirty) return;
    window.clearTimeout(debouncedSave.current);
    debouncedSave.current = window.setTimeout(() => void persist(), 800);
    return () => window.clearTimeout(debouncedSave.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flow, dirty]);

  async function persist() {
    if (!flow) return;
    setSaving(true);
    setError(null);
    try {
      const r = await updateFlow(flow.id, {
        name: flow.name,
        description: flow.description,
        graph: flow.graph,
      });
      setFlow((prev) => (prev ? { ...prev, version: r.version, updated_at: r.updated_at } : prev));
      setSavedAt(new Date());
      setDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  function mutate(updater: (graph: FlowGraph) => FlowGraph) {
    setFlow((prev) => (prev ? { ...prev, graph: updater(prev.graph) } : prev));
    setDirty(true);
  }

  function addNode(type: string) {
    const newId = shortId(type.replace(/_/g, ""));
    const node: BlockNode = { id: newId, type, params: {}, next: null };
    mutate((g) => ({ ...g, nodes: [...g.nodes, node] }));
    setSelectedId(newId);
  }

  function updateNode(nodeId: string, patch: Partial<BlockNode>) {
    mutate((g) => ({
      ...g,
      nodes: g.nodes.map((n) => (n.id === nodeId ? { ...n, ...patch } : n)),
    }));
  }

  function updateNodeParam(nodeId: string, key: string, value: unknown) {
    mutate((g) => ({
      ...g,
      nodes: g.nodes.map((n) =>
        n.id === nodeId ? { ...n, params: { ...n.params, [key]: value } } : n,
      ),
    }));
  }

  function removeNode(nodeId: string) {
    mutate((g) => ({
      ...g,
      nodes: g.nodes
        .filter((n) => n.id !== nodeId)
        .map((n) => ({
          ...n,
          next: n.next === nodeId ? null : n.next,
          params: scrubRefs(n.params, nodeId),
        })),
    }));
    if (selectedId === nodeId) setSelectedId(null);
  }

  function moveNode(nodeId: string, dir: -1 | 1) {
    mutate((g) => {
      const idx = g.nodes.findIndex((n) => n.id === nodeId);
      if (idx < 0) return g;
      const target = idx + dir;
      if (target < 0 || target >= g.nodes.length) return g;
      const nodes = [...g.nodes];
      [nodes[idx], nodes[target]] = [nodes[target], nodes[idx]];
      return { ...g, nodes };
    });
  }

  async function publish() {
    if (!flow) return;
    if (dirty) await persist();
    setSaving(true);
    try {
      const r = await publishFlow(flow.id);
      setFlow((prev) => (prev ? { ...prev, is_published: true, version: r.version } : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function unpublish() {
    if (!flow) return;
    setSaving(true);
    try {
      await unpublishFlow(flow.id);
      setFlow((prev) => (prev ? { ...prev, is_published: false } : prev));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function preview() {
    if (!flow) return;
    if (dirty) await persist();
    let stored = localStorage.getItem(PREVIEW_KEY) || "";
    if (!stored) {
      const input = prompt(
        "Чтобы видеть превью в Telegram — введи свой числовой Telegram id (узнать у @userinfobot). " +
          "Он сохранится в браузере.",
      );
      if (!input) return;
      const n = Number(input.trim());
      if (!Number.isInteger(n) || n <= 0) {
        alert("Это не похоже на корректный telegram id.");
        return;
      }
      stored = String(n);
      localStorage.setItem(PREVIEW_KEY, stored);
    }
    try {
      await previewFlow(flow.id, Number(stored));
      alert("Превью поставлено в очередь. Бот сейчас пришлёт его в Telegram.");
    } catch (err) {
      alert(err instanceof Error ? err.message : String(err));
    }
  }

  if (error && !flow) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-red-600">
        {error}
      </div>
    );
  }
  if (!flow) {
    return <div className="min-h-screen flex items-center justify-center text-sm text-muted">Загрузка…</div>;
  }

  const selected = flow.graph.nodes.find((n) => n.id === selectedId) || null;

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <header className="border-b border-line bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center gap-3">
          <Link to="/admin" className="text-xs text-muted hover:text-ink">
            ← к флоу
          </Link>
          <input
            className="flex-1 min-w-[200px] bg-transparent border-none text-base font-medium focus:outline-none"
            value={flow.name}
            onChange={(e) => {
              setFlow({ ...flow, name: e.target.value });
              setDirty(true);
            }}
          />
          <span className="text-xs text-muted">
            {saving ? "сохранение…" : dirty ? "не сохранено" : savedAt ? `сохранено ${savedAt.toLocaleTimeString()}` : `v${flow.version}`}
          </span>
          <button onClick={() => void persist()} className="btn-outline px-3 py-1.5 text-xs">
            <FloppyDisk size={14} weight="thin" /> Сохранить
          </button>
          <button onClick={() => void preview()} className="btn-outline px-3 py-1.5 text-xs">
            <Eye size={14} weight="thin" /> Превью
          </button>
          {flow.is_published ? (
            <button onClick={() => void unpublish()} className="btn-outline px-3 py-1.5 text-xs">
              <ArrowSquareOut size={14} weight="thin" /> Снять с публикации
            </button>
          ) : (
            <button onClick={() => void publish()} className="btn-primary px-3 py-1.5 text-xs">
              <CheckCircle size={14} weight="thin" /> Опубликовать
            </button>
          )}
        </div>
        {error && <p className="max-w-6xl mx-auto px-4 pb-2 text-xs text-red-600">{error}</p>}
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6 grid grid-cols-1 md:grid-cols-[200px_1fr_320px] gap-4">
        <aside className="space-y-3">
          {BLOCK_GROUPS.map((group) => (
            <div key={group.id}>
              <h3 className="text-[10px] uppercase tracking-tighter text-muted mb-1">{group.title}</h3>
              <ul className="space-y-1">
                {BLOCK_SCHEMAS.filter((s) => s.group === group.id).map((s) => (
                  <li key={s.type}>
                    <button
                      onClick={() => addNode(s.type)}
                      className="w-full text-left text-xs px-2 py-1.5 rounded border border-line bg-white hover:border-ink"
                    >
                      <span className="inline-flex items-center gap-1">
                        <Plus size={12} weight="thin" /> {s.title}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </aside>

        <section>
          <TextArea
            label="Описание флоу"
            value={flow.description || ""}
            onChange={(e) => {
              setFlow({ ...flow, description: e.target.value });
              setDirty(true);
            }}
            rows={2}
          />
          <h2 className="text-xs uppercase tracking-tighter text-muted mt-4 mb-2">Блоки</h2>
          {flow.graph.nodes.length === 0 ? (
            <p className="card text-sm text-muted">
              Добавь первый блок слева. Обычно начинают с триггера «Команда» (например /start) и
              ведут стрелочками к следующему.
            </p>
          ) : (
            <ol className="space-y-2">
              {flow.graph.nodes.map((node, i) => {
                const schema = schemaFor(node.type);
                return (
                  <li key={node.id}>
                    <button
                      onClick={() => setSelectedId(node.id)}
                      className={classNames(
                        "w-full text-left card transition-colors",
                        selectedId === node.id ? "border-ink" : "hover:border-ink/40",
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted">{i + 1}</span>
                            <span className="font-medium truncate">{schema?.title || node.type}</span>
                            <span className="text-[10px] text-muted font-mono">{node.id}</span>
                          </div>
                          <p className="text-xs text-muted truncate">
                            {summaryFor(node, schema?.fields)}
                          </p>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              moveNode(node.id, -1);
                            }}
                            className="text-xs text-muted hover:text-ink px-1"
                            title="Выше"
                          >
                            ↑
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              moveNode(node.id, 1);
                            }}
                            className="text-xs text-muted hover:text-ink px-1"
                            title="Ниже"
                          >
                            ↓
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeNode(node.id);
                            }}
                            className="text-muted hover:text-red-600 px-1"
                            title="Удалить"
                          >
                            <Trash size={14} weight="thin" />
                          </button>
                        </div>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ol>
          )}
        </section>

        <aside>
          {selected ? (
            <Inspector
              node={selected}
              allNodes={flow.graph.nodes}
              onChange={(patch) => updateNode(selected.id, patch)}
              onParam={(k, v) => updateNodeParam(selected.id, k, v)}
            />
          ) : (
            <div className="card text-sm text-muted">Выбери блок чтобы редактировать.</div>
          )}
        </aside>
      </main>

      <Footer />
    </div>
  );
}

function scrubRefs(params: Record<string, unknown>, removedId: string): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(params)) {
    if (typeof v === "string" && v === removedId) {
      out[k] = null;
    } else {
      out[k] = v;
    }
  }
  return out;
}

function summaryFor(node: BlockNode, fields?: BlockField[]): string {
  if (!fields) return "";
  const first = fields.find((f) => ["text", "textarea", "node-ref"].includes(f.kind));
  if (!first) return "";
  const v = node.params[first.key];
  if (typeof v === "string") return v.slice(0, 80);
  return "";
}

function Inspector({
  node,
  allNodes,
  onChange,
  onParam,
}: {
  node: BlockNode;
  allNodes: BlockNode[];
  onChange: (patch: Partial<BlockNode>) => void;
  onParam: (key: string, value: unknown) => void;
}) {
  const schema = schemaFor(node.type);
  const otherNodes = useMemo(() => allNodes.filter((n) => n.id !== node.id), [allNodes, node.id]);

  return (
    <div className="card space-y-3 sticky top-4">
      <div>
        <h3 className="serif-heading text-lg">{schema?.title || node.type}</h3>
        <p className="text-xs text-muted">{schema?.description}</p>
        <p className="text-[10px] text-muted font-mono mt-1">id: {node.id}</p>
      </div>

      {schema?.hasNext && (
        <NodeRef
          label="Следующий блок"
          value={(node.next as string | null) ?? null}
          options={otherNodes}
          onChange={(v) => onChange({ next: v })}
        />
      )}

      {schema?.fields.map((f) => (
        <FieldRenderer
          key={f.key}
          field={f}
          value={node.params[f.key]}
          onChange={(v) => onParam(f.key, v)}
          allNodes={otherNodes}
        />
      ))}
    </div>
  );
}

function FieldRenderer({
  field,
  value,
  onChange,
  allNodes,
}: {
  field: BlockField;
  value: unknown;
  onChange: (v: unknown) => void;
  allNodes: BlockNode[];
}) {
  if (field.kind === "text") {
    return (
      <TextField
        label={field.label}
        hint={field.hint}
        placeholder={field.placeholder}
        value={(value as string) || ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (field.kind === "textarea") {
    return (
      <TextArea
        label={field.label}
        hint={field.hint}
        placeholder={field.placeholder}
        value={(value as string) || ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (field.kind === "number") {
    return (
      <TextField
        label={field.label}
        hint={field.hint}
        type="number"
        placeholder={field.placeholder}
        value={(value as number | string) ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
      />
    );
  }
  if (field.kind === "boolean") {
    return (
      <Switch
        label={field.label}
        hint={field.hint}
        checked={Boolean(value)}
        onChange={onChange}
      />
    );
  }
  if (field.kind === "node-ref") {
    return (
      <NodeRef
        label={field.label}
        value={(value as string | null) ?? null}
        options={allNodes}
        onChange={onChange}
      />
    );
  }
  if (field.kind === "options-list") {
    return <OptionsListEditor label={field.label} value={value} onChange={onChange} />;
  }
  if (field.kind === "buttons") {
    return (
      <ButtonsEditor
        label={field.label}
        value={value}
        onChange={onChange}
        allNodes={allNodes}
      />
    );
  }
  if (field.kind === "filters") {
    return <FiltersEditor label={field.label} value={value} onChange={onChange} />;
  }
  if (field.kind === "kv") {
    return <KvEditor label={field.label} value={value} onChange={onChange} />;
  }
  return null;
}

function NodeRef({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string | null;
  options: BlockNode[];
  onChange: (v: string | null) => void;
}) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value || null)}
        className="w-full border border-line rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:border-ink"
      >
        <option value="">— не задан —</option>
        {options.map((n) => {
          const schema = schemaFor(n.type);
          return (
            <option key={n.id} value={n.id}>
              {schema?.title || n.type} ({n.id})
            </option>
          );
        })}
      </select>
    </label>
  );
}

type Option = { text?: string; value?: string };
function OptionsListEditor({
  label,
  value,
  onChange,
}: {
  label: string;
  value: unknown;
  onChange: (v: Option[]) => void;
}) {
  const arr: Option[] = Array.isArray(value) ? (value as Option[]) : [];
  function update(i: number, patch: Partial<Option>) {
    const out = [...arr];
    out[i] = { ...out[i], ...patch };
    onChange(out);
  }
  return (
    <div>
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <div className="space-y-1">
        {arr.map((opt, i) => (
          <div key={i} className="flex gap-1">
            <input
              className="flex-1 border border-line rounded px-2 py-1 text-xs"
              placeholder="Текст"
              value={opt.text || ""}
              onChange={(e) => update(i, { text: e.target.value })}
            />
            <input
              className="w-24 border border-line rounded px-2 py-1 text-xs"
              placeholder="Значение"
              value={opt.value || ""}
              onChange={(e) => update(i, { value: e.target.value })}
            />
            <button
              onClick={() => onChange(arr.filter((_, j) => j !== i))}
              className="text-muted hover:text-red-600 px-1"
            >
              ×
            </button>
          </div>
        ))}
        <button
          onClick={() => onChange([...arr, { text: "", value: "" }])}
          className="text-xs text-muted hover:text-ink"
        >
          + добавить вариант
        </button>
      </div>
    </div>
  );
}

type ButtonRow = { text?: string; next?: string | null; value?: string; url?: string };
function ButtonsEditor({
  label,
  value,
  onChange,
  allNodes,
}: {
  label: string;
  value: unknown;
  onChange: (v: ButtonRow[]) => void;
  allNodes: BlockNode[];
}) {
  const arr: ButtonRow[] = Array.isArray(value) ? (value as ButtonRow[]) : [];
  function update(i: number, patch: Partial<ButtonRow>) {
    const out = [...arr];
    out[i] = { ...out[i], ...patch };
    onChange(out);
  }
  return (
    <div>
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <div className="space-y-2">
        {arr.map((row, i) => (
          <div key={i} className="border border-line rounded p-2 space-y-1 bg-white">
            <div className="flex items-center gap-1">
              <input
                className="flex-1 border border-line rounded px-2 py-1 text-xs"
                placeholder="Текст кнопки"
                value={row.text || ""}
                onChange={(e) => update(i, { text: e.target.value })}
              />
              <button
                onClick={() => onChange(arr.filter((_, j) => j !== i))}
                className="text-muted hover:text-red-600 px-1"
              >
                ×
              </button>
            </div>
            <input
              className="w-full border border-line rounded px-2 py-1 text-xs"
              placeholder="URL (если нужна ссылочная кнопка)"
              value={row.url || ""}
              onChange={(e) => update(i, { url: e.target.value })}
            />
            <select
              className="w-full border border-line rounded px-2 py-1 text-xs bg-white"
              value={row.next || ""}
              onChange={(e) => update(i, { next: e.target.value || null })}
            >
              <option value="">→ переход: не задан</option>
              {allNodes.map((n) => {
                const s = schemaFor(n.type);
                return (
                  <option key={n.id} value={n.id}>
                    → {s?.title || n.type} ({n.id})
                  </option>
                );
              })}
            </select>
          </div>
        ))}
        <button
          onClick={() => onChange([...arr, { text: "", next: null }])}
          className="text-xs text-muted hover:text-ink"
        >
          + добавить кнопку
        </button>
      </div>
    </div>
  );
}

type Filter = { column?: string; op?: string; value?: string };
function FiltersEditor({
  label,
  value,
  onChange,
}: {
  label: string;
  value: unknown;
  onChange: (v: Filter[]) => void;
}) {
  const arr: Filter[] = Array.isArray(value) ? (value as Filter[]) : [];
  function update(i: number, patch: Partial<Filter>) {
    const out = [...arr];
    out[i] = { ...out[i], ...patch };
    onChange(out);
  }
  return (
    <div>
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <div className="space-y-1">
        {arr.map((f, i) => (
          <div key={i} className="flex gap-1">
            <input
              className="flex-1 border border-line rounded px-2 py-1 text-xs"
              placeholder="колонка"
              value={f.column || ""}
              onChange={(e) => update(i, { column: e.target.value })}
            />
            <select
              className="w-24 border border-line rounded px-2 py-1 text-xs bg-white"
              value={f.op || "eq"}
              onChange={(e) => update(i, { op: e.target.value })}
            >
              <option value="eq">=</option>
              <option value="neq">≠</option>
              <option value="ilike">ilike</option>
              <option value="in">in</option>
              <option value="gt">&gt;</option>
              <option value="lt">&lt;</option>
              <option value="is">is</option>
            </select>
            <input
              className="flex-1 border border-line rounded px-2 py-1 text-xs"
              placeholder="{{vars.x}}"
              value={f.value || ""}
              onChange={(e) => update(i, { value: e.target.value })}
            />
            <button
              onClick={() => onChange(arr.filter((_, j) => j !== i))}
              className="text-muted hover:text-red-600 px-1"
            >
              ×
            </button>
          </div>
        ))}
        <button
          onClick={() => onChange([...arr, { column: "", op: "eq", value: "" }])}
          className="text-xs text-muted hover:text-ink"
        >
          + фильтр
        </button>
      </div>
    </div>
  );
}

function KvEditor({
  label,
  value,
  onChange,
}: {
  label: string;
  value: unknown;
  onChange: (v: Record<string, string>) => void;
}) {
  const obj: Record<string, string> =
    value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, string>)
      : {};
  const entries = Object.entries(obj);
  function update(i: number, key: string, val: string) {
    const next: Record<string, string> = {};
    entries.forEach(([k, v], idx) => {
      if (idx === i) {
        next[key] = val;
      } else {
        next[k] = v;
      }
    });
    onChange(next);
  }
  function remove(i: number) {
    const next: Record<string, string> = {};
    entries.forEach(([k, v], idx) => {
      if (idx !== i) next[k] = v;
    });
    onChange(next);
  }
  function add() {
    onChange({ ...obj, "": "" });
  }
  return (
    <div>
      <span className="block text-xs uppercase tracking-tighter text-muted mb-1">{label}</span>
      <div className="space-y-1">
        {entries.map(([k, v], i) => (
          <div key={i} className="flex gap-1">
            <input
              className="w-1/3 border border-line rounded px-2 py-1 text-xs"
              placeholder="key"
              value={k}
              onChange={(e) => update(i, e.target.value, v)}
            />
            <input
              className="flex-1 border border-line rounded px-2 py-1 text-xs"
              placeholder="value"
              value={v}
              onChange={(e) => update(i, k, e.target.value)}
            />
            <button onClick={() => remove(i)} className="text-muted hover:text-red-600 px-1">
              ×
            </button>
          </div>
        ))}
        <button onClick={add} className="text-xs text-muted hover:text-ink">
          + поле
        </button>
      </div>
    </div>
  );
}
