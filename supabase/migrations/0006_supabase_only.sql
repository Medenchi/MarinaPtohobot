-- ============================================================
-- Supabase-only architecture
-- ============================================================
-- All HTTP/admin operations move from FastAPI to direct Supabase
-- calls (supabase-js + Edge Functions). This migration:
--   1) adds an app_role() helper that reads the custom `app_role`
--      claim from the JWT minted by the admin-login Edge Function,
--   2) installs RLS policies for every table the constructor and
--      content panels touch, with two app roles: `admin` (Denis)
--      and `mama` (Marina). The service_role key used by the bot
--      bypasses RLS as usual.
--   3) creates `bot_preview_requests` so the constructor's
--      "Preview" button writes a row that the bot polls and uses
--      to send a draft flow to Denis.
--   4) sets storage.objects RLS for write access by app role.

-- ---------- helper: extract app_role from JWT -----------------

create or replace function public.app_role() returns text
  language sql stable
  as $$
    select coalesce(
      nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'app_role',
      null
    )
  $$;

-- ---------- preview requests ---------------------------------
-- Constructor inserts here. Bot polls (or subscribes) and renders
-- the included graph for the target telegram user.

create table if not exists public.bot_preview_requests (
  id uuid primary key default gen_random_uuid(),
  flow_id uuid references public.bot_flows(id) on delete cascade,
  graph jsonb not null,
  target_telegram_id bigint not null,
  status text not null default 'pending', -- pending | sent | error
  error text,
  created_at timestamptz not null default now(),
  processed_at timestamptz
);
create index if not exists bot_preview_requests_status_idx
  on public.bot_preview_requests(status, created_at);

alter table public.bot_preview_requests enable row level security;

-- ---------- per-table RLS policies ---------------------------
-- Pattern: admin can do everything for "flow"/"runtime" tables.
-- Mama can do everything for "content" tables. Both can read
-- analytics. Service role bypasses all of this automatically.

-- bot_flows: admin-only
drop policy if exists bot_flows_admin_all on public.bot_flows;
create policy bot_flows_admin_all on public.bot_flows
  for all using (public.app_role() = 'admin')
  with check (public.app_role() = 'admin');

-- bot_preview_requests: admin-only (only Denis previews)
drop policy if exists bot_preview_admin_all on public.bot_preview_requests;
create policy bot_preview_admin_all on public.bot_preview_requests
  for all using (public.app_role() = 'admin')
  with check (public.app_role() = 'admin');

-- bot_sessions: admin can read (debug/stats); writes only via service_role
drop policy if exists bot_sessions_admin_read on public.bot_sessions;
create policy bot_sessions_admin_read on public.bot_sessions
  for select using (public.app_role() = 'admin');

-- bookings: both roles can read; mama manages (mark read / delete)
drop policy if exists bookings_admin_read on public.bookings;
create policy bookings_admin_read on public.bookings
  for select using (public.app_role() in ('admin', 'mama'));

drop policy if exists bookings_mama_write on public.bookings;
create policy bookings_mama_write on public.bookings
  for update using (public.app_role() = 'mama')
  with check (public.app_role() = 'mama');

drop policy if exists bookings_mama_delete on public.bookings;
create policy bookings_mama_delete on public.bookings
  for delete using (public.app_role() = 'mama');

-- bot_events: read-only for both roles (Stats page)
drop policy if exists bot_events_read on public.bot_events;
create policy bot_events_read on public.bot_events
  for select using (public.app_role() in ('admin', 'mama'));

-- bot_users: read-only for admin
drop policy if exists bot_users_admin_read on public.bot_users;
create policy bot_users_admin_read on public.bot_users
  for select using (public.app_role() = 'admin');

-- outfits: keep public read (published only), add mama full access for any row
drop policy if exists outfits_mama_all on public.outfits;
create policy outfits_mama_all on public.outfits
  for all using (public.app_role() = 'mama')
  with check (public.app_role() = 'mama');

-- also let admin read outfits (constructor may want to preview filters)
drop policy if exists outfits_admin_read on public.outfits;
create policy outfits_admin_read on public.outfits
  for select using (public.app_role() = 'admin');

-- outfit_images: mama full access
drop policy if exists outfit_images_mama_all on public.outfit_images;
create policy outfit_images_mama_all on public.outfit_images
  for all using (public.app_role() = 'mama')
  with check (public.app_role() = 'mama');

drop policy if exists outfit_images_admin_read on public.outfit_images;
create policy outfit_images_admin_read on public.outfit_images
  for select using (public.app_role() = 'admin');

-- courses: mama full access
drop policy if exists courses_mama_all on public.courses;
create policy courses_mama_all on public.courses
  for all using (public.app_role() = 'mama')
  with check (public.app_role() = 'mama');

drop policy if exists courses_admin_read on public.courses;
create policy courses_admin_read on public.courses
  for select using (public.app_role() = 'admin');

-- course_files: mama full access
drop policy if exists course_files_mama_all on public.course_files;
create policy course_files_mama_all on public.course_files
  for all using (public.app_role() = 'mama')
  with check (public.app_role() = 'mama');

drop policy if exists course_files_admin_read on public.course_files;
create policy course_files_admin_read on public.course_files
  for select using (public.app_role() = 'admin');

-- ---------- storage write policies ---------------------------
-- All three buckets keep public-read (from 0002_storage.sql).
-- Writes are gated on app_role. service_role bypasses these.

drop policy if exists "outfit-images mama write" on storage.objects;
create policy "outfit-images mama write" on storage.objects
  for insert with check (
    bucket_id = 'outfit-images' and public.app_role() = 'mama'
  );
drop policy if exists "outfit-images mama update" on storage.objects;
create policy "outfit-images mama update" on storage.objects
  for update using (bucket_id = 'outfit-images' and public.app_role() = 'mama')
  with check (bucket_id = 'outfit-images' and public.app_role() = 'mama');
drop policy if exists "outfit-images mama delete" on storage.objects;
create policy "outfit-images mama delete" on storage.objects
  for delete using (bucket_id = 'outfit-images' and public.app_role() = 'mama');

drop policy if exists "course-files mama write" on storage.objects;
create policy "course-files mama write" on storage.objects
  for insert with check (
    bucket_id = 'course-files' and public.app_role() = 'mama'
  );
drop policy if exists "course-files mama update" on storage.objects;
create policy "course-files mama update" on storage.objects
  for update using (bucket_id = 'course-files' and public.app_role() = 'mama')
  with check (bucket_id = 'course-files' and public.app_role() = 'mama');
drop policy if exists "course-files mama delete" on storage.objects;
create policy "course-files mama delete" on storage.objects
  for delete using (bucket_id = 'course-files' and public.app_role() = 'mama');

-- outfit-pdfs: service_role only (bot uploads generated PDFs)
-- No INSERT/UPDATE/DELETE policy means anon/auth get denied;
-- service_role still bypasses RLS.
