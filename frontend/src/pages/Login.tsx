import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "@phosphor-icons/react";
import { login } from "@/lib/api";
import { setToken } from "@/lib/supabase";
import { TextField } from "@/components/Field";
import Footer from "@/components/Footer";
import type { Role } from "@/types";

interface Props {
  role: Role;
  title: string;
  subtitle: string;
  successRedirect: string;
}

export default function LoginPage({ role, title, subtitle, successRedirect }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await login(role, password);
      setToken(role, resp.token);
      navigate(successRedirect, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не получилось войти");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-paper">
      <main className="flex-1 flex flex-col items-center justify-center px-6">
        <form onSubmit={submit} className="card w-full max-w-sm space-y-4">
          <div>
            <h1 className="serif-heading text-2xl">{title}</h1>
            <p className="text-xs text-muted mt-1">{subtitle}</p>
          </div>
          <TextField
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            autoComplete="current-password"
            required
          />
          {error && <p className="text-xs text-red-600">{error}</p>}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "…" : "Войти"} <ArrowRight size={16} weight="thin" />
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
}
