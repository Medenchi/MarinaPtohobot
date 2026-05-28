import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn("Переменные Supabase не заданы в Vercel!");
}

export function tokenFor(): string | null {
  return "mock-token";
}

export function setToken() {}

export function clearToken() {}

export const anonSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
});

export function getSupabase(): SupabaseClient {
  return anonSupabase;
}
