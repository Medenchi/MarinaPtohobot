// One Supabase client per role. We mint a custom JWT through the
// `admin-login` Edge Function and attach it as Authorization to every
// REST/Storage call. Row Level Security on the database side gates
// what each role can read/write — see supabase/migrations/0006*.sql.

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { Role } from "@/types";

const STORAGE_PREFIX = "marina:token:";

export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // Surface this loud in dev — the deploy will inject these via GitHub Pages vars.
  // eslint-disable-next-line no-console
  console.warn(
    "VITE_SUPABASE_URL and/or VITE_SUPABASE_ANON_KEY are not set. " +
      "Frontend will fail to talk to Supabase.",
  );
}

export function tokenFor(role: Role): string | null {
  return localStorage.getItem(STORAGE_PREFIX + role);
}

export function setToken(role: Role, token: string) {
  localStorage.setItem(STORAGE_PREFIX + role, token);
}

export function clearToken(role: Role) {
  localStorage.removeItem(STORAGE_PREFIX + role);
}

// Build a Supabase client for the given role. The anon key remains
// the "apikey" header (PostgREST requires it) while Authorization
// carries the role-specific JWT. supabase-js merges the two and
// PostgREST treats the JWT as the authenticated session.
export function getSupabase(role: Role): SupabaseClient {
  const token = tokenFor(role);
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
    global: { headers },
  });
}

// Anon client (no user JWT). Used for the public landing or for the
// Edge Function login call where we don't have a token yet.
export const anonSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false,
    detectSessionInUrl: false,
  },
});
