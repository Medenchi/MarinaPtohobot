import { useEffect, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { tokenFor } from "@/lib/supabase";
import type { Role } from "@/types";

export default function AuthGuard({
  role,
  loginPath,
  children,
}: {
  role: Role;
  loginPath: string;
  children: ReactNode;
}) {
  const navigate = useNavigate();
  useEffect(() => {
    if (!tokenFor(role)) navigate(loginPath, { replace: true });
  }, [role, loginPath, navigate]);
  if (!tokenFor(role)) return null;
  return <>{children}</>;
}
