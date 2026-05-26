import { Link } from "react-router-dom";
import { GearSix, Kanban } from "@phosphor-icons/react";
import Footer from "@/components/Footer";

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-20">
        <h1 className="serif-heading text-5xl sm:text-7xl mb-3">Marina Photo</h1>
        <p className="text-muted text-sm tracking-tighter mb-12">
          Telegram-бот для подбора образов на съёмку
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md w-full">
          <Link
            to="/admin"
            className="card hover:bg-ink hover:text-paper transition-colors group"
          >
            <Kanban size={28} weight="thin" className="mb-3 opacity-80 group-hover:opacity-100" />
            <h2 className="serif-heading text-xl mb-1">Конструктор</h2>
            <p className="text-xs opacity-60">Настройка флоу бота</p>
          </Link>
          <Link
            to="/mama"
            className="card hover:bg-ink hover:text-paper transition-colors group"
          >
            <GearSix size={28} weight="thin" className="mb-3 opacity-80 group-hover:opacity-100" />
            <h2 className="serif-heading text-xl mb-1">Контент</h2>
            <p className="text-xs opacity-60">Образы, курсы, заявки</p>
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}
