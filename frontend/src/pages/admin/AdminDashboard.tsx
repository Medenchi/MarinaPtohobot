import { Link, useNavigate } from "react-router-dom";
import { TShirt, GraduationCap, SignOut } from "@phosphor-icons/react";
import Footer from "@/components/Footer";
import { useEffect } from "react";

export default function AdminDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    if (!sessionStorage.getItem("admin_token")) {
      navigate("/admin");
    }
  }, [navigate]);

  function logout() {
    sessionStorage.removeItem("admin_token");
    navigate("/admin");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-6 py-4 border-b border-line flex items-center justify-between">
        <h1 className="serif-heading text-xl">Админка</h1>
        <button
          onClick={logout}
          className="text-sm text-muted flex items-center gap-1 hover:text-ink"
        >
          <SignOut size={16} weight="bold" /> Выйти
        </button>
      </header>

      <main className="flex-1 px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
          <Link
            to="/admin/outfits"
            className="card flex items-center gap-4 hover:bg-line/30 transition-colors"
          >
            <TShirt size={36} weight="thin" />
            <div>
              <h2 className="serif-heading text-lg">Образы</h2>
              <p className="text-sm text-muted">
                Управление каталогом образов
              </p>
            </div>
          </Link>

          <Link
            to="/admin/courses"
            className="card flex items-center gap-4 hover:bg-line/30 transition-colors"
          >
            <GraduationCap size={36} weight="thin" />
            <div>
              <h2 className="serif-heading text-lg">Курсы</h2>
              <p className="text-sm text-muted">
                Бесплатные материалы и файлы
              </p>
            </div>
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}
