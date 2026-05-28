// Supabase Edge Function — admin-login.
// Verifies a password for the admin or mama role and returns a JWT
// signed with the Supabase project's JWT secret. The JWT carries a
// custom `app_role` claim which RLS policies inspect via
// public.app_role() — see supabase/migrations/0006_supabase_only.sql.
//
// Required function secrets (set via Supabase dashboard or
// `supabase secrets set`):
//   APP_ADMIN_PASSWORD   — password for Denis (admin role)
//   APP_MAMA_PASSWORD    — password for Marina (mama role)
//   APP_JWT_SECRET       — copy of the project's JWT Secret
//                          (Project Settings → API → JWT Settings)
//   APP_JWT_TTL_SECONDS  — optional, default 86400 (24h)
//
// Deploy:
//   supabase functions deploy admin-login --no-verify-jwt
// (--no-verify-jwt lets unauthenticated requests hit this function;
// the function itself does the password check.)
//
// Invoke from the browser:
//   POST https://<project>.functions.supabase.co/admin-login
//   body: { "role": "admin"|"mama", "password": "..." }
//   200  -> { "token": "...", "role": "admin"|"mama", "expires_at": <unix> }
//   401  -> { "error": "Invalid credentials" }

import { create, getNumericDate } from "https://deno.land/x/djwt@v3.0.2/mod.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

function json(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: corsHeaders });
}

async function makeKey(secret: string): Promise<CryptoKey> {
  return await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return json(405, { error: "Method Not Allowed" });
  }

  const adminPassword = Deno.env.get("APP_ADMIN_PASSWORD") ?? "";
  const mamaPassword = Deno.env.get("APP_MAMA_PASSWORD") ?? "";
  const jwtSecret = Deno.env.get("APP_JWT_SECRET") ?? "";
  const ttlSeconds = Number(Deno.env.get("APP_JWT_TTL_SECONDS") ?? "86400");

  if (!jwtSecret) {
    return json(500, {
      error:
        "Server is not configured: APP_JWT_SECRET is missing. Set it in the function secrets.",
    });
  }
  if (!adminPassword && !mamaPassword) {
    return json(500, {
      error:
        "Server is not configured: neither APP_ADMIN_PASSWORD nor APP_MAMA_PASSWORD is set.",
    });
  }

  let body: { role?: string; password?: string };
  try {
    body = await req.json();
  } catch {
    return json(400, { error: "Body must be JSON: { role, password }" });
  }

  const role = body.role;
  const password = body.password ?? "";

  if (role !== "admin" && role !== "mama") {
    return json(400, { error: "role must be 'admin' or 'mama'" });
  }

  const expected = role === "admin" ? adminPassword : mamaPassword;
  if (!expected || password !== expected) {
    return json(401, { error: "Invalid credentials" });
  }

  const key = await makeKey(jwtSecret);
  const exp = getNumericDate(ttlSeconds);
  const iat = Math.floor(Date.now() / 1000);

  const token = await create(
    { alg: "HS256", typ: "JWT" },
    {
      iss: "supabase",
      aud: "authenticated",
      // Standard Supabase role — PostgREST requires this to switch from anon.
      role: "authenticated",
      // Our custom claim, read by public.app_role() in SQL.
      app_role: role,
      sub: `app:${role}`,
      iat,
      exp,
    },
    key,
  );

  return json(200, { token, role, expires_at: exp });
});
