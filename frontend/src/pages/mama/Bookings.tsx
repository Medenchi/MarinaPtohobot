import { useEffect, useState } from "react";
import { Check, Trash } from "@phosphor-icons/react";
import { api } from "@/lib/api";
import { classNames } from "@/lib/util";
import MamaLayout from "./Layout";
import type { Booking } from "@/types";

export default function Bookings() {
  const [rows, setRows] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  async function load() {
    setLoading(true);
    try {
      const data = await api.mama.get<Booking[]>(
        `/api/admin/bookings?only_unread=${filter === "unread"}`,
      );
      setRows(data);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, [filter]);

  async function markRead(id: number) {
    await api.mama.post(`/api/admin/bookings/${id}/read`);
    await load();
  }
  async function remove(id: number) {
    if (!confirm("Удалить заявку?")) return;
    await api.mama.del(`/api/admin/bookings/${id}`);
    await load();
  }

  return (
    <MamaLayout>
      <div className="flex justify-between items-center mb-4">
        <h2 className="serif-heading text-2xl">Заявки</h2>
        <div className="flex border border-line rounded overflow-hidden text-xs">
          <button
            onClick={() => setFilter("all")}
            className={classNames(
              "px-3 py-1.5",
              filter === "all" ? "bg-ink text-paper" : "bg-white text-muted",
            )}
          >
            Все
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={classNames(
              "px-3 py-1.5",
              filter === "unread" ? "bg-ink text-paper" : "bg-white text-muted",
            )}
          >
            Непрочитанные
          </button>
        </div>
      </div>
      {loading ? (
        <p className="text-sm text-muted">Загрузка…</p>
      ) : rows.length === 0 ? (
        <p className="card text-sm text-muted text-center py-12">Пока ни одной заявки.</p>
      ) : (
        <ul className="space-y-2">
          {rows.map((b) => (
            <li key={b.id} className={classNames("card", !b.is_read && "border-ink")}>
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {b.full_name || b.telegram_username || `tg:${b.telegram_id}`}
                    </span>
                    {!b.is_read && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-ink text-paper">
                        новая
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted">
                    {[b.shoot_type, b.preferred_date, b.phone].filter(Boolean).join(" · ")}
                  </p>
                  {b.notes && <p className="text-sm mt-1 whitespace-pre-wrap">{b.notes}</p>}
                  {Object.keys(b.payload || {}).length > 0 && (
                    <pre className="text-[10px] text-muted bg-paper p-2 rounded mt-2 overflow-x-auto">
                      {JSON.stringify(b.payload, null, 2)}
                    </pre>
                  )}
                  <p className="text-[10px] text-muted mt-1">
                    {new Date(b.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  {!b.is_read && (
                    <button
                      onClick={() => markRead(b.id)}
                      className="text-muted hover:text-ink"
                      title="Прочитано"
                    >
                      <Check size={16} weight="thin" />
                    </button>
                  )}
                  <button
                    onClick={() => remove(b.id)}
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
