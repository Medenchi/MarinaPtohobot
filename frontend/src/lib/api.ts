// Tiny fetch wrapper. Stores JWT per role in localStorage and decorates every
// request automatically. The backend serves both /admin/* and /mama/* under
// the same /api/admin prefix; only the dependency injection on each route
// decides which role(s) it accepts.

import type { Role } from "@/types";

const STORAGE_PREFIX = "marina:token:";

// Read API URL from either VITE_API_URL (used in CI / GH Pages vars) or
// VITE_API_BASE_URL (legacy fallback). Trailing slash trimmed.
export const API_BASE = (
  (import.meta.env.VITE_API_URL as string | undefined) ||
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  "http://localhost:8000"
).replace(/\/$/, "");

export function tokenFor(role: Role): string | null {
  return localStorage.getItem(STORAGE_PREFIX + role);
}

export function setToken(role: Role, token: string) {
  localStorage.setItem(STORAGE_PREFIX + role, token);
}

export function clearToken(role: Role) {
  localStorage.removeItem(STORAGE_PREFIX + role);
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function call<T>(
  role: Role,
  method: string,
  path: string,
  body?: unknown,
  isForm = false,
): Promise<T> {
  const headers: Record<string, string> = {};
  const t = tokenFor(role);
  if (t) headers.Authorization = `Bearer ${t}`;
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (isForm) {
      payload = body as FormData;
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }
  const resp = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });
  const text = await resp.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!resp.ok) {
    const msg =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : text || `HTTP ${resp.status}`;
    throw new ApiError(resp.status, msg);
  }
  return data as T;
}

export const api = {
  async login(role: Role, password: string) {
    return call<{ token: string; role: Role }>("admin", "POST", "/api/admin/login", {
      role,
      password,
    });
  },
  // Bound calls for the constructor (admin role)
  admin: {
    get: <T>(p: string) => call<T>("admin", "GET", p),
    post: <T>(p: string, body?: unknown) => call<T>("admin", "POST", p, body),
    patch: <T>(p: string, body?: unknown) => call<T>("admin", "PATCH", p, body),
    del: <T>(p: string) => call<T>("admin", "DELETE", p),
  },
  // Bound calls for the content panel (mama role)
  mama: {
    get: <T>(p: string) => call<T>("mama", "GET", p),
    post: <T>(p: string, body?: unknown, isForm = false) =>
      call<T>("mama", "POST", p, body, isForm),
    patch: <T>(p: string, body?: unknown) => call<T>("mama", "PATCH", p, body),
    del: <T>(p: string) => call<T>("mama", "DELETE", p),
  },
};
