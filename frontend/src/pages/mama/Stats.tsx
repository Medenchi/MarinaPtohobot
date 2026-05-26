import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import MamaLayout from "./Layout";
import type { StatsOverview } from "@/types";

export default function Stats() {
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.mama
      .get<StatsOverview>("/api/admin/stats/overview")
      .then(setStats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <MamaLayout>
        <p className="text-sm text-muted">Загрузка…</p>
      </MamaLayout>
    );
  }
  if (!stats) {
    return (
      <MamaLayout>
        <p className="text-sm text-red-600">Не получилось загрузить статистику</p>
      </MamaLayout>
    );
  }

  return (
    <MamaLayout>
      <h2 className="serif-heading text-2xl mb-4">Статистика</h2>
      <p className="text-xs text-muted mb-6">
        Период: последние 30 дней · с {new Date(stats.since).toLocaleDateString()}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-6">
        <Stat label="Всего юзеров" value={stats.users_total} />
        <Stat label="Новых" value={stats.users_new} />
        <Stat label="Заявок" value={stats.bookings_total} />
        <Stat label="Непрочитанных" value={stats.bookings_unread} />
        <Stat label="PDF сгенерировано" value={stats.pdf_generated} />
      </div>

      <h3 className="text-xs uppercase tracking-tighter text-muted mb-2">События</h3>
      <ul className="card divide-y divide-line">
        {Object.entries(stats.events_by_type).map(([k, v]) => (
          <li key={k} className="flex justify-between py-2 text-sm">
            <span>{k}</span>
            <span className="font-mono">{v}</span>
          </li>
        ))}
      </ul>

      {stats.messages_per_day.length > 0 && (
        <>
          <h3 className="text-xs uppercase tracking-tighter text-muted mt-6 mb-2">
            Сообщений по дням
          </h3>
          <ul className="card divide-y divide-line">
            {stats.messages_per_day.map(([day, count]) => (
              <li key={day} className="flex justify-between py-2 text-sm">
                <span>{day}</span>
                <span className="font-mono">{count}</span>
              </li>
            ))}
          </ul>
        </>
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
