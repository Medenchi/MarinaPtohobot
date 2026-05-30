/**
 * Веб-BotFather: управление дочерними ботами.
 *
 * Возможности (всё через прямой вызов api.telegram.org с фронта):
 *  - список ботов из child_bots (Supabase)
 *  - добавить бот по токену → автоматически тянет getMe
 *  - переименовать (setMyName)
 *  - сменить описание (setMyDescription)
 *  - сменить short description (setMyShortDescription)
 *  - загрузить аватарку (setMyProfilePhoto)
 *  - редактировать команды бота (setMyCommands)
 *  - включить/выключить в пуле поллинга
 *  - привязать к конкретному флоу (flow_id)
 *  - удалить из пула
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowsClockwise,
  CheckCircle,
  Image as ImageIcon,
  Pencil,
  Plus,
  Power,
  Trash,
  XCircle,
} from "@phosphor-icons/react";
import {
  createChildBot,
  deleteChildBot,
  listChildBots,
  listFlows,
  tgDeleteMyCommands,
  tgGetMe,
  tgGetMyCommands,
  tgGetMyDescription,
  tgGetMyName,
  tgGetMyShortDescription,
  tgSetMyCommands,
  tgSetMyDescription,
  tgSetMyName,
  tgSetMyProfilePhoto,
  tgSetMyShortDescription,
  updateChildBot,
  type ChildBot,
} from "@/lib/api";
import type { Flow } from "@/types";
import { TextField, TextArea, Switch } from "@/components/Field";
import Footer from "@/components/Footer";

export default function Bots() {
  const [bots, setBots] = useState<ChildBot[]>([]);
  const [flows, setFlows] = useState<Flow[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<ChildBot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newToken, setNewToken] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    setLoading(true);
    try {
      const [bs, fs] = await Promise.all([listChildBots(), listFlows()]);
      setBots(bs);
      setFlows(fs);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { void reload(); }, []);

  async function addBot() {
    const token = newToken.trim();
    if (!token.includes(":") || token.length < 30) {
      setError("Похоже, это не валидный токен.");
      return;
    }
    setBusy(true);
    try {
      // 1) проверяем getMe и получаем username
      const me = await tgGetMe(token);
      // 2) сохраняем
      const row = await createChildBot(token);
      await updateChildBot(row.id, {
        bot_username: me.username,
        display_name: me.first_name,
      });
      setNewToken("");
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function toggle(b: ChildBot) {
    await updateChildBot(b.id, { is_enabled: !b.is_enabled });
    await reload();
  }

  async function remove(id: number) {
    if (!confirm("Удалить бот из пула? Сам бот в Telegram останется (его удалит только BotFather).")) return;
    await deleteChildBot(id);
    await reload();
  }

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <header className="border-b border-line bg-white">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link to="/admin" className="text-xs text-muted hover:text-ink">← к флоу</Link>
          <h1 className="serif-heading text-xl">Мои боты</h1>
          <span className="text-xs text-muted">Веб-BotFather</span>
          <button onClick={() => void reload()} className="ml-auto text-xs text-muted hover:text-ink">
            <ArrowsClockwise size={12} weight="thin" className="inline" /> обновить
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6 space-y-6">
        {error && (
          <p className="card text-xs text-red-600 border-red-200 bg-red-50">{error}</p>
        )}

        {/* Добавление */}
        <section className="card space-y-2">
          <h2 className="serif-heading text-lg">Добавить бота</h2>
          <p className="text-xs text-muted">
            Получи токен у <a href="https://t.me/BotFather" className="underline">@BotFather</a>{" "}
            и вставь сюда. Бот появится в пуле и начнёт поллиться после перезапуска контейнера.
          </p>
          <div className="flex gap-2">
            <input
              className="flex-1 border border-line rounded px-3 py-2 text-sm font-mono"
              placeholder="123456:ABC-DEF..."
              value={newToken}
              onChange={(e) => setNewToken(e.target.value)}
            />
            <button onClick={() => void addBot()} disabled={busy} className="btn-primary">
              <Plus size={14} weight="thin" /> Добавить
            </button>
          </div>
        </section>

        {/* Список */}
        <section>
          <h2 className="serif-heading text-lg mb-2">Подключённые боты ({bots.length})</h2>
          {loading ? <p className="text-sm text-muted">Загрузка…</p>
            : bots.length === 0 ? (
              <p className="card text-sm text-muted">Пока ни одного. Добавь через форму выше.</p>
            ) : (
              <ul className="space-y-2">
                {bots.map((b) => (
                  <li key={b.id} className="card">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-medium">
                          {b.display_name || "Без имени"}
                          {b.bot_username && (
                            <span className="text-muted text-xs ml-2 font-normal">@{b.bot_username}</span>
                          )}
                          {b.is_enabled
                            ? <CheckCircle size={14} weight="fill" className="inline ml-2 text-green-600" />
                            : <XCircle size={14} weight="fill" className="inline ml-2 text-muted" />}
                        </div>
                        <div className="text-xs text-muted truncate">
                          id={b.id} · token: <code className="text-[10px]">{b.token.slice(0, 14)}…</code>
                          {b.flow_id && <span> · флоу: <code>{b.flow_id.slice(0, 8)}</code></span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button onClick={() => setEditing(b)} className="btn-outline px-3 py-1 text-xs">
                          <Pencil size={12} weight="thin" /> Редактировать
                        </button>
                        <button onClick={() => void toggle(b)} className="btn-outline px-2 py-1 text-xs" title={b.is_enabled ? "Выключить" : "Включить"}>
                          <Power size={12} weight="thin" />
                        </button>
                        <button onClick={() => void remove(b.id)} className="btn-outline px-2 py-1 text-xs text-red-600" title="Удалить из пула">
                          <Trash size={12} weight="thin" />
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
        </section>
      </main>

      {editing && (
        <BotEditor
          bot={editing}
          flows={flows}
          onClose={() => setEditing(null)}
          onSaved={() => { void reload(); setEditing(null); }}
        />
      )}

      <Footer />
    </div>
  );
}

// ============ Редактор бота (модал) ============

function BotEditor({
  bot, flows, onClose, onSaved,
}: { bot: ChildBot; flows: Flow[]; onClose: () => void; onSaved: () => void }) {
  const [tab, setTab] = useState<"profile" | "commands" | "settings">("profile");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [shortDesc, setShortDesc] = useState("");
  const [commands, setCommands] = useState<{ command: string; description: string }[]>([]);
  const [lang, setLang] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState(bot.display_name || "");
  const [enabled, setEnabled] = useState(bot.is_enabled);
  const [flowId, setFlowId] = useState(bot.flow_id || "");

  async function loadFromTg() {
    setBusy(true);
    setMsg(null);
    try {
      const [n, d, sd, cmds] = await Promise.all([
        tgGetMyName(bot.token, lang),
        tgGetMyDescription(bot.token, lang),
        tgGetMyShortDescription(bot.token, lang),
        tgGetMyCommands(bot.token, lang),
      ]);
      setName(n.name);
      setDesc(d.description);
      setShortDesc(sd.short_description);
      setCommands(cmds);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => { void loadFromTg(); /* eslint-disable-next-line */ }, [lang]);

  async function saveProfile() {
    setBusy(true); setMsg(null);
    try {
      if (name) await tgSetMyName(bot.token, name, lang);
      if (desc !== undefined) await tgSetMyDescription(bot.token, desc, lang);
      if (shortDesc !== undefined) await tgSetMyShortDescription(bot.token, shortDesc, lang);
      setMsg("✅ Сохранено в Telegram");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveAvatar(file: File) {
    setBusy(true); setMsg(null);
    try {
      await tgSetMyProfilePhoto(bot.token, file);
      setMsg("✅ Аватарка обновлена");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveCommands() {
    setBusy(true); setMsg(null);
    try {
      const filtered = commands.filter((c) => c.command.trim() && c.description.trim());
      if (filtered.length === 0) {
        await tgDeleteMyCommands(bot.token, lang);
      } else {
        await tgSetMyCommands(bot.token, filtered, lang);
      }
      setMsg("✅ Команды обновлены");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function saveSettings() {
    setBusy(true); setMsg(null);
    try {
      await updateChildBot(bot.id, {
        display_name: displayName,
        is_enabled: enabled,
        flow_id: flowId || null,
      });
      setMsg("✅ Сохранено");
      onSaved();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-auto">
        <header className="flex items-center justify-between p-4 border-b border-line sticky top-0 bg-white">
          <div>
            <h3 className="serif-heading text-xl">{displayName || "Бот"}</h3>
            <p className="text-xs text-muted">@{bot.bot_username || "—"}</p>
          </div>
          <button onClick={onClose} className="text-muted hover:text-ink text-sm">закрыть</button>
        </header>

        <div className="border-b border-line px-4 flex gap-1">
          {(["profile", "commands", "settings"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-xs ${tab === t ? "border-b-2 border-ink font-medium" : "text-muted hover:text-ink"}`}
            >
              {t === "profile" ? "Профиль" : t === "commands" ? "Команды" : "Настройки пула"}
            </button>
          ))}
        </div>

        <div className="p-4 space-y-3 text-sm">
          {msg && (
            <p className={`text-xs ${msg.startsWith("✅") ? "text-green-700" : "text-red-600"}`}>{msg}</p>
          )}

          {tab === "profile" && (
            <>
              <div className="flex gap-2 items-end">
                <TextField label="Язык (пусто = по умолчанию)" placeholder="ru / en / ..." value={lang} onChange={(e) => setLang(e.target.value)} />
                <button onClick={() => void loadFromTg()} disabled={busy} className="btn-outline text-xs px-3 py-1.5">
                  <ArrowsClockwise size={12} weight="thin" /> Прочитать из TG
                </button>
              </div>
              <TextField label="Имя бота (64 симв)" value={name} onChange={(e) => setName(e.target.value)} />
              <TextField label="Краткое описание (120 симв, показывается в превью)" value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} />
              <TextArea label="Описание (512 симв, в профиле)" value={desc} onChange={(e) => setDesc(e.target.value)} rows={4} />
              <div className="flex justify-between items-center">
                <label className="btn-outline cursor-pointer text-xs">
                  <ImageIcon size={12} weight="thin" /> Загрузить аватарку
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) void saveAvatar(f);
                      e.target.value = "";
                    }}
                  />
                </label>
                <button onClick={() => void saveProfile()} disabled={busy} className="btn-primary text-xs">
                  Сохранить профиль
                </button>
              </div>
            </>
          )}

          {tab === "commands" && (
            <>
              <p className="text-xs text-muted">
                Команды показываются юзеру при наборе «/». Префикс «/» не пиши — он добавится автоматически.
              </p>
              <CommandsEditor commands={commands} onChange={setCommands} />
              <div className="flex justify-end">
                <button onClick={() => void saveCommands()} disabled={busy} className="btn-primary text-xs">
                  Сохранить команды
                </button>
              </div>
            </>
          )}

          {tab === "settings" && (
            <>
              <TextField label="Отображаемое имя (в админке)" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
              <Switch label="Включён в пуле поллинга" checked={enabled} onChange={setEnabled} />
              <label className="block">
                <span className="block text-xs uppercase tracking-tighter text-muted mb-1">Привязать к флоу (опц.)</span>
                <select
                  value={flowId}
                  onChange={(e) => setFlowId(e.target.value)}
                  className="w-full border border-line rounded px-3 py-2 text-sm bg-white"
                >
                  <option value="">— использовать главный published-флоу —</option>
                  {flows.map((f) => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </label>
              <details className="text-xs text-muted">
                <summary className="cursor-pointer">Показать токен</summary>
                <code className="block mt-1 break-all">{bot.token}</code>
              </details>
              <div className="flex justify-end">
                <button onClick={() => void saveSettings()} disabled={busy} className="btn-primary text-xs">
                  Сохранить настройки
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function CommandsEditor({
  commands, onChange,
}: { commands: { command: string; description: string }[]; onChange: (c: { command: string; description: string }[]) => void }) {
  function update(i: number, patch: Partial<{ command: string; description: string }>) {
    const out = [...commands];
    out[i] = { ...out[i], ...patch };
    onChange(out);
  }
  return (
    <div className="space-y-1">
      {commands.map((c, i) => (
        <div key={i} className="flex gap-1">
          <span className="text-muted text-xs pt-2">/</span>
          <input
            className="w-32 border border-line rounded px-2 py-1 text-xs font-mono"
            placeholder="start"
            value={c.command}
            onChange={(e) => update(i, { command: e.target.value.replace(/^\//, "").trim() })}
          />
          <input
            className="flex-1 border border-line rounded px-2 py-1 text-xs"
            placeholder="Что делает команда"
            value={c.description}
            onChange={(e) => update(i, { description: e.target.value })}
          />
          <button
            onClick={() => onChange(commands.filter((_, j) => j !== i))}
            className="text-muted hover:text-red-600 px-1"
          >×</button>
        </div>
      ))}
      <button
        onClick={() => onChange([...commands, { command: "", description: "" }])}
        className="text-xs text-muted hover:text-ink"
      >+ команда</button>
    </div>
  );
}
