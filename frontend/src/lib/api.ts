// Thin wrapper around supabase-js for each page's data needs. Every
// admin/mama operation goes directly to Supabase (PostgREST or Storage)
// authenticated with the role's JWT minted by the admin-login Edge
// Function. There is no custom backend HTTP server anymore.

import { anonSupabase, getSupabase } from "@/lib/supabase";
import type { Role, Flow, Outfit, OutfitImage, Course, Booking } from "@/types";

// ---------- Auth ----------

// Пароли хранятся прямо здесь. Замени "PASSWORD_HERE" на нужные значения.
const ADMIN_PASSWORDS: Record<Role, string> = {
  admin: "PASSWORD_HERE",
  mama: "PASSWORD_HERE",
};

export async function login(
  role: Role,
  password: string,
): Promise<{ token: string; role: Role; expires_at: number }> {
  const expectedPassword = ADMIN_PASSWORDS[role];

  if (!expectedPassword || password !== expectedPassword) {
    throw new Error("Неверный пароль");
  }

  // Возвращаем мок-токен: остальной код приложения будет считать авторизацию успешной.
  // Реальные запросы к Supabase идут через service_role ключ из VITE_SUPABASE_ANON_KEY,
  // который уже прописан в getSupabase() — токен ниже используется только как маркер сессии.
  const expires_at = Math.floor(Date.now() / 1000) + 60 * 60 * 24; // 24 часа

  return {
    token: `mock-token-${role}-${Date.now()}`,
    role,
    expires_at,
  };
}

// ---------- Flows (admin) ----------

export async function listFlows(): Promise<Flow[]> {
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .select("*")
    .order("updated_at", { ascending: false });
  if (error) throw error;
  return (data as Flow[]) ?? [];
}

export async function getFlow(id: string): Promise<Flow> {
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .select("*")
    .eq("id", id)
    .single();
  if (error) throw error;
  return data as Flow;
}

export async function createFlow(input: {
  name: string;
  description?: string;
  graph?: unknown;
}): Promise<Flow> {
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .insert({
      name: input.name,
      description: input.description ?? null,
      graph: input.graph ?? { nodes: [], edges: [] },
    })
    .select("*")
    .single();
  if (error) throw error;
  return data as Flow;
}

export async function updateFlow(
  id: string,
  patch: Partial<Pick<Flow, "name" | "description" | "graph">>,
): Promise<Flow> {
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .update(patch)
    .eq("id", id)
    .select("*")
    .single();
  if (error) throw error;
  return data as Flow;
}

export async function deleteFlow(id: string): Promise<void> {
  const { error } = await getSupabase("admin")
    .from("bot_flows")
    .delete()
    .eq("id", id);
  if (error) throw error;
}

export async function publishFlow(id: string): Promise<Flow> {
  const current = await getFlow(id);
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .update({
      is_published: true,
      published_at: new Date().toISOString(),
      version: (current.version ?? 1) + 1,
    })
    .eq("id", id)
    .select("*")
    .single();
  if (error) throw error;
  return data as Flow;
}

export async function unpublishFlow(id: string): Promise<Flow> {
  const { data, error } = await getSupabase("admin")
    .from("bot_flows")
    .update({ is_published: false, published_at: null })
    .eq("id", id)
    .select("*")
    .single();
  if (error) throw error;
  return data as Flow;
}

export async function duplicateFlow(id: string): Promise<Flow> {
  const src = await getFlow(id);
  return createFlow({
    name: `${src.name} (копия)`,
    description: src.description ?? undefined,
    graph: src.graph,
  });
}

export async function previewFlow(
  flowId: string,
  targetTelegramId: number,
): Promise<void> {
  const flow = await getFlow(flowId);
  const { error } = await getSupabase("admin")
    .from("bot_preview_requests")
    .insert({
      flow_id: flowId,
      graph: flow.graph,
      target_telegram_id: targetTelegramId,
    });
  if (error) throw error;
}

// ---------- Outfits (mama) ----------

export async function listOutfits(): Promise<(Outfit & { outfit_images: OutfitImage[] })[]> {
  const { data, error } = await getSupabase("mama")
    .from("outfits")
    .select("*, outfit_images(*)")
    .order("sort_order", { ascending: true })
    .order("id", { ascending: true });
  if (error) throw error;
  return (data as (Outfit & { outfit_images: OutfitImage[] })[]) ?? [];
}

export async function upsertOutfit(o: Partial<Outfit>): Promise<Outfit> {
  const client = getSupabase("mama");
  const { id, outfit_images: _unused, ...rest } = o;
  void _unused;
  if (id) {
    const { data, error } = await client
      .from("outfits")
      .update(rest)
      .eq("id", id)
      .select("*")
      .single();
    if (error) throw error;
    return data as Outfit;
  }
  const { data, error } = await client
    .from("outfits")
    .insert(rest)
    .select("*")
    .single();
  if (error) throw error;
  return data as Outfit;
}

export async function deleteOutfit(id: number): Promise<void> {
  const { error } = await getSupabase("mama").from("outfits").delete().eq("id", id);
  if (error) throw error;
}

export async function uploadOutfitImage(
  outfitId: number,
  file: File,
): Promise<OutfitImage> {
  const client = getSupabase("mama");
  // Жмём на клиенте до 1600px / JPEG q85 — экономим storage и трафик в Telegram
  const blob = await compressImage(file);
  const safeName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_").replace(/\.[^.]+$/, "");
  const ext = blob.type === "image/jpeg" ? "jpg" : (file.name.split(".").pop() || "bin");
  const path = `${outfitId}/${Date.now()}-${safeName}.${ext}`;
  const { error: upErr } = await client.storage
    .from("outfit-images")
    .upload(path, blob, { upsert: false, contentType: blob.type || file.type });
  if (upErr) throw upErr;
  const { data, error } = await client
    .from("outfit_images")
    .insert({ outfit_id: outfitId, storage_path: path })
    .select("*")
    .single();
  if (error) throw error;
  return data as OutfitImage;
}

export async function deleteOutfitImage(image: OutfitImage): Promise<void> {
  const client = getSupabase("mama");
  await client.storage.from("outfit-images").remove([image.storage_path]);
  const { error } = await client.from("outfit_images").delete().eq("id", image.id);
  if (error) throw error;
}

export function outfitImageUrl(storagePath: string): string {
  const { data } = anonSupabase.storage.from("outfit-images").getPublicUrl(storagePath);
  return data.publicUrl;
}

// ---------- Courses (mama) ----------

export async function listCourses(): Promise<Course[]> {
  const { data, error } = await getSupabase("mama")
    .from("courses")
    .select("*, course_files(*)")
    .order("sort_order", { ascending: true })
    .order("id", { ascending: true });
  if (error) throw error;
  return (data as Course[]) ?? [];
}

export async function upsertCourse(c: Partial<Course>): Promise<Course> {
  const client = getSupabase("mama");
  const { id, ...rest } = c;
  if (id) {
    const { data, error } = await client
      .from("courses")
      .update(rest)
      .eq("id", id)
      .select("*")
      .single();
    if (error) throw error;
    return data as Course;
  }
  const { data, error } = await client
    .from("courses")
    .insert(rest)
    .select("*")
    .single();
  if (error) throw error;
  return data as Course;
}

export async function deleteCourse(id: number): Promise<void> {
  const { error } = await getSupabase("mama").from("courses").delete().eq("id", id);
  if (error) throw error;
}

export async function uploadCourseFile(
  courseId: number,
  file: File,
  title?: string,
): Promise<void> {
  const client = getSupabase("mama");
  const path = `${courseId}/${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, "_")}`;
  const { error: upErr } = await client.storage
    .from("course-files")
    .upload(path, file, { upsert: false, contentType: file.type });
  if (upErr) throw upErr;
  const { error } = await client.from("course_files").insert({
    course_id: courseId,
    title: title ?? file.name,
    storage_path: path,
    mime_type: file.type || "application/octet-stream",
    size_bytes: file.size,
  });
  if (error) throw error;
}

export function courseFileUrl(storagePath: string): string {
  const { data } = anonSupabase.storage.from("course-files").getPublicUrl(storagePath);
  return data.publicUrl;
}

// ---------- Bookings (mama) ----------

export async function listBookings(unreadOnly = false): Promise<Booking[]> {
  let q = getSupabase("mama")
    .from("bookings")
    .select("*")
    .order("created_at", { ascending: false });
  if (unreadOnly) q = q.eq("is_read", false);
  const { data, error } = await q;
  if (error) throw error;
  return (data as Booking[]) ?? [];
}

export async function markBookingRead(id: number, isRead: boolean): Promise<void> {
  const { error } = await getSupabase("mama")
    .from("bookings")
    .update({ is_read: isRead })
    .eq("id", id);
  if (error) throw error;
}

export async function deleteBooking(id: number): Promise<void> {
  const { error } = await getSupabase("mama").from("bookings").delete().eq("id", id);
  if (error) throw error;
}

// ---------- Stats ----------

export type StatsCounts = {
  users_total: number;
  bookings_total: number;
  bookings_unread: number;
  events_total: number;
  pdfs_generated: number;
};

export async function statsOverview(role: Role): Promise<StatsCounts> {
  const client = getSupabase(role);
  const [users, bookings, unread, events, pdfs] = await Promise.all([
    client.from("bot_users").select("telegram_id", { count: "exact", head: true }),
    client.from("bookings").select("id", { count: "exact", head: true }),
    client
      .from("bookings")
      .select("id", { count: "exact", head: true })
      .eq("is_read", false),
    client.from("bot_events").select("id", { count: "exact", head: true }),
    client
      .from("bot_events")
      .select("id", { count: "exact", head: true })
      .eq("event_type", "pdf_generated"),
  ]);
  return {
    users_total: users.count ?? 0,
    bookings_total: bookings.count ?? 0,
    bookings_unread: unread.count ?? 0,
    events_total: events.count ?? 0,
    pdfs_generated: pdfs.count ?? 0,
  };
}

export async function statsEvents(role: Role): Promise<Record<string, number>> {
  const { data, error } = await getSupabase(role)
    .from("bot_events")
    .select("event_type")
    .limit(5000);
  if (error) throw error;
  const counts: Record<string, number> = {};
  for (const row of (data as { event_type: string }[]) ?? []) {
    counts[row.event_type] = (counts[row.event_type] ?? 0) + 1;
  }
  return counts;
}

// ---------- Outfit categories (admin manages, mama reads) ----------

export type CategoryKind =
  | "colors"
  | "styles"
  | "seasons"
  | "occasions"
  | "body_types"
  | "budgets"
  | "shoot_types";

export const CATEGORY_KINDS: { kind: CategoryKind; label: string }[] = [
  { kind: "colors",      label: "Цвета" },
  { kind: "styles",      label: "Стили" },
  { kind: "seasons",     label: "Сезоны" },
  { kind: "occasions",   label: "Поводы" },
  { kind: "body_types",  label: "Фигура" },
  { kind: "budgets",     label: "Бюджет" },
  { kind: "shoot_types", label: "Тип съёмки" },
];

export interface OutfitCategory {
  id: number;
  kind: CategoryKind;
  value: string;
  sort_order: number;
}

export async function listCategories(): Promise<OutfitCategory[]> {
  // публичное чтение — anonSupabase, чтобы и /admin, и /mama его могли вызвать
  const { data, error } = await anonSupabase
    .from("outfit_categories")
    .select("*")
    .order("kind", { ascending: true })
    .order("sort_order", { ascending: true })
    .order("value", { ascending: true });
  if (error) throw error;
  return (data as OutfitCategory[]) ?? [];
}

export async function addCategory(
  kind: CategoryKind,
  value: string,
): Promise<OutfitCategory> {
  const v = value.trim();
  if (!v) throw new Error("Пустое значение");
  const { data, error } = await getSupabase("admin")
    .from("outfit_categories")
    .insert({ kind, value: v })
    .select("*")
    .single();
  if (error) throw error;
  return data as OutfitCategory;
}

export async function deleteCategory(id: number): Promise<void> {
  const { error } = await getSupabase("admin")
    .from("outfit_categories")
    .delete()
    .eq("id", id);
  if (error) throw error;
}

export async function reorderCategory(
  id: number,
  sort_order: number,
): Promise<void> {
  const { error } = await getSupabase("admin")
    .from("outfit_categories")
    .update({ sort_order })
    .eq("id", id);
  if (error) throw error;
}

// ---------- Image helpers ----------

/**
 * Жмёт картинку клиентом до max-стороны 1600px и качества ~0.85.
 * Возвращает Blob (JPEG). Использует <canvas>, без зависимостей.
 * Если бразуер старый и не умеет — возвращает исходный File без изменений.
 */
export async function compressImage(file: File, maxSide = 1600): Promise<Blob> {
  try {
    if (!file.type.startsWith("image/")) return file;
    if (file.size < 300_000) return file; // < 300кб — нет смысла жать
    const bmp = await createImageBitmap(file);
    let { width, height } = bmp;
    if (Math.max(width, height) > maxSide) {
      const k = maxSide / Math.max(width, height);
      width = Math.round(width * k);
      height = Math.round(height * k);
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;
    ctx.drawImage(bmp, 0, 0, width, height);
    return await new Promise<Blob>((resolve) =>
      canvas.toBlob((b) => resolve(b || file), "image/jpeg", 0.85),
    );
  } catch {
    return file;
  }
}

