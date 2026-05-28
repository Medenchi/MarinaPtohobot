import { useEffect, useState } from "react";
import { statsEvents, statsOverview, type StatsCounts } from "@/lib/api";
import MamaLayout from "./Layout";

export default function Stats() {
  const [stats, setStats] = useState<StatsCounts | null>(null);
  const [events, setEvents] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([statsOverview("mama"), statsEvents("mama")])
      .then(([s, e]) => {
        setStats(s);
        setEvents(e);
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
