-- ============================================================
-- Storage buckets: outfit-images, course-files, outfit-pdfs
-- All buckets are public-read; writes go through service_role
-- (our FastAPI admin API). No anon writes.
-- ============================================================

insert into storage.buckets (id, name, public)
  values ('outfit-images', 'outfit-images', true)
  on conflict (id) do update set public = true;

insert into storage.buckets (id, name, public)
  values ('course-files', 'course-files', true)
  on conflict (id) do update set public = true;

insert into storage.buckets (id, name, public)
  values ('outfit-pdfs', 'outfit-pdfs', true)
  on conflict (id) do update set public = true;

-- Public read policies (one per bucket)
drop policy if exists "outfit-images public read" on storage.objects;
create policy "outfit-images public read" on storage.objects
  for select using (bucket_id = 'outfit-images');

drop policy if exists "course-files public read" on storage.objects;
create policy "course-files public read" on storage.objects
  for select using (bucket_id = 'course-files');

drop policy if exists "outfit-pdfs public read" on storage.objects;
create policy "outfit-pdfs public read" on storage.objects
  for select using (bucket_id = 'outfit-pdfs');
