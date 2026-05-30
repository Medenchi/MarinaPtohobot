import { useEffect, useState } from "react";
import { statsDeeplinks, statsEvents, statsOverview, type DeeplinkStat, type StatsCounts } from "@/lib/api";
import MamaLayout from "./Layout";

export default function Stats() {
  const [stats, setStats] = useState<StatsCounts | null>(null);
  const [events, setEvents] = useState<Record<string, number>>({});
  const [deeplinks, setDeeplinks] = useState<DeeplinkStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([statsOverview("mama"), statsEvents("mama"), statsDeeplinks("mama")])
      .then(([s, e, d]) => {
        setStats(s);
        setEvents(e);
        setDeeplinks(d);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <MamaLayout>
        <p className="text-sm text-muted">Загрузка…</p>
      </MamaLayout>
    );
  }
  if (error || !stats) {
    return (
      <MamaLayout>
        <p className="text-sm text-red-600">
          {error || "Не получилось загрузить статистику"}
        </p>
      </MamaLayout>
    );
  }

  return (
    <MamaLayout>
      <h2 className="serif-heading text-2xl mb-4">Статистика</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-6">
        <Stat label="Всего юзеров" value={stats.users_total} />
        <Stat label="Заявок" value={stats.bookings_total} />
        <Stat label="Непрочитанных" value={stats.bookings_unread} />
        <Stat label="PDF сгенерировано" value={stats.pdfs_generated} />
      </div>

      <h3 className="text-xs uppercase tracking-tighter text-muted mb-2">События</h3>
      {Object.keys(events).length === 0 ? (
        <p className="card text-sm text-muted">Пока ни одного события.</p>
      ) : (
        <ul className="card divide-y divide-line">
          {Object.entries(events)
            .sort((a, b) => b[1] - a[1])
            .map(([k, v]) => (
              <li key={k} className="flex justify-between py-2 text-sm">
                <span>{k}</span>
                <span className="font-mono">{v}</span>
              </li>
            ))}
        </ul>
      )}

      <h3 className="text-xs uppercase tracking-tighter text-muted mb-2 mt-6">
        🔗 Источники переходов (deep-links)
      </h3>
      {deeplinks.length === 0 ? (
        <p className="card text-sm text-muted">
          Никто ещё не переходил по реферальной ссылке. Используй формат:<br />
          <code className="text-xs">t.me/{`{bot_username}`}?start=ref_pin_42</code> — где
          <code className="text-xs">ref_pin_42</code> — любой id (для каждого поста в Pinterest свой).
        </p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-line">
                <th className="py-1 pr-3">Ref</th>
                <th className="py-1 pr-3 text-right">Запусков</th>
                <th className="py-1 pr-3 text-right">Уникальных</th>
                <th className="py-1 pr-3 text-right">Последний</th>
              </tr>
            </thead>
            <tbody>
              {deeplinks.map((d) => (
                <tr key={d.ref} className="border-b border-line/30 last:border-0">
                  <td className="py-2 pr-3 font-mono text-xs">{d.ref}</td>
                  <td className="py-2 pr-3 text-right font-medium">{d.count}</td>
                  <td className="py-2 pr-3 text-right text-muted">{d.unique_users}</td>
                  <td className="py-2 pr-3 text-right text-xs text-muted">
                    {new Date(d.last_at).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </MamaLayout>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-tighter text-muted">{label}</div>
      <div className="serif-heading text-3xl">{value}</div>
    </div>
  );
}
