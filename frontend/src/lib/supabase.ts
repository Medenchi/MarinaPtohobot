import { createClient } from "@supabase/supabase-js";

export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

export function tokenFor(...args: any[]): string | null {
  return "mock-token";
}

export function setToken(...args: any[]) {}

export function clearToken(...args: any[]) {}

export const anonSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
});

// Функция принимает ЛЮБЫЕ аргументы и просто отдает админский клиент базы данных
export function getSupabase(...args: any[]): any {
  return anonSupabase;
}
