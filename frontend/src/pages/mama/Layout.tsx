import type { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { CalendarBlank, ChartBar, Images, Package } from "@phosphor-icons/react";
import { clearToken } from "@/lib/supabase";
import { classNames } from "@/lib/util";
import Footer from "@/components/Footer";

const ITEMS = [
  { to: "/mama", label: "Образы", Icon: Images, exact: true },
  { to: "/mama/courses", label: "Курсы", Icon: Package },
  { to: "/mama/bookings", label: "Заявки", Icon: CalendarBlank },
  { to: "/mama/stats", label: "Статистика", Icon: ChartBar },
];

export default function MamaLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  function logout() {
    clearToken("mama");
    navigate("/mama/login");
  }
  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <header className="border-b border-line bg-white">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
          <h1 className="serif-heading text-xl flex-1">Marina Photo · контент</h1>
          <Link to="/" className="text-xs text-muted hover:text-ink">
            на главную
          </Link>
          <button onClick={logout} className="text-xs text-muted hover:text-ink">
            выйти
          </button>
        </div>
        <nav className="max-w-5xl mx-auto px-4 flex gap-1 overflow-x-auto">
          {ITEMS.map(({ to, label, Icon, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                classNames(
                  "px-3 py-2 text-xs uppercase tracking-tighter border-b-2 flex items-center gap-1",
                  isActive
                    ? "border-ink text-ink"
                    : "border-transparent text-muted hover:text-ink",
                )
              }
            >
              <Icon size={14} weight="thin" /> {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-6">{children}</main>
      <Footer />
    </div>
  );
}
