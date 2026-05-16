import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock } from "@phosphor-icons/react";
import { api } from "@/lib/api";
import Footer from "@/components/Footer";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api<{ token: string }>("/api/admin/login", {
        method: "POST",
        body: JSON.stringify({ password }),
      });
      sessionStorage.setItem("admin_token", res.token);
      navigate("/admin/dashboard");
    } catch {
      setError("Неверный пароль");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-xs flex flex-col gap-4"
      >
        <div className="flex flex-col items-center mb-4">
          <Lock size={32} weight="thin" />
          <h1 className="serif-heading text-2xl mt-2">Админка</h1>
        </div>

        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoFocus
          required
          className="rounded-lg border border-line px-4 py-3 text-sm focus:border-ink outline-none"
        />

        {error && <p className="text-sm text-red-500 text-center">{error}</p>}

        <button
          type="submit"
          disabled={loading || !password}
          className="btn-primary"
        >
          {loading ? "Проверяю..." : "Войти"}
        </button>
      </form>
      <Footer />
    </div>
  );
}
