// Спрощенный клиент Supabase для прямой работы без Edge Functions
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { Role } from "@/types";

export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn("Переменные Supabase не заданы в Vercel!");
}

export function tokenFor(role: Role): string | null {
  return "mock-token";
}

export function setToken(role: Role, token: string) {}

export function clearToken(role: Role) {}

// Главный клиент, который теперь использует service_role и имеет полные права админа
export const anonSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
});

// Заставляем функцию getSupabase всегда возвращать админский клиент anonSupabase
export function getSupabase(role: Role): SupabaseClient {
  return anonSupabase;
}
