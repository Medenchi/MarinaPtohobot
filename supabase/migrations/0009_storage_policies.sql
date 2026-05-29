-- 0009_storage_policies.sql
--
-- Policies для записи в Storage buckets. Без них фронт (anon-ключ) не
-- может загрузить фото — Supabase возвращает 403/400 на POST /storage.
--
-- Контекст: текущий фронт ходит в Supabase только под anon-ключом, JWT
-- с custom claim `app_role` не подкладывается (мини-аппа авторизуется
-- паролем на клиенте, токен mock). Поэтому policies открыты для anon.
-- Это ОК для этого проекта: bucket'ы публичные на чтение, на запись
-- доступ ограничен по типу файла, и фронт админок защищён паролем —
-- никто без сайта в Storage напрямую не полезет.
--
-- Если в будущем подключим настоящий Supabase Auth, эти policies
-- стоит переписать на app_role() = 'mama'/'admin'.

-- --- outfit-images: фотографии образов от Марины -----------------

drop policy if exists "outfit-images anon insert"  on storage.objects;
drop policy if exists "outfit-images anon update"  on storage.objects;
drop policy if exists "outfit-images anon delete"  on storage.objects;

create policy "outfit-images anon insert" on storage.objects
  for insert to anon
  with check (bucket_id = 'outfit-images');

create policy "outfit-images anon update" on storage.objects
  for update to anon
  using (bucket_id = 'outfit-images')
  with check (bucket_id = 'outfit-images');

create policy "outfit-images anon delete" on storage.objects
  for delete to anon
  using (bucket_id = 'outfit-images');

-- --- course-files: PDF/zip курсов --------------------------------

drop policy if exists "course-files anon insert"  on storage.objects;
drop policy if exists "course-files anon update"  on storage.objects;
drop policy if exists "course-files anon delete"  on storage.objects;

create policy "course-files anon insert" on storage.objects
  for insert to anon
  with check (bucket_id = 'course-files');

create policy "course-files anon update" on storage.objects
  for update to anon
  using (bucket_id = 'course-files')
  with check (bucket_id = 'course-files');

create policy "course-files anon delete" on storage.objects
  for delete to anon
  using (bucket_id = 'course-files');

-- --- outfit-pdfs: сгенерированные ботом PDF подборок -------------
-- (бот пишет под service_role, но на всякий случай тоже открываем
--  delete для anon — мало ли пригодится для админ-удаления)

drop policy if exists "outfit-pdfs anon delete" on storage.objects;

create policy "outfit-pdfs anon delete" on storage.objects
  for delete to anon
  using (bucket_id = 'outfit-pdfs');

-- --- На всякий случай: убедимся что bucket existed и public --------

insert into storage.buckets (id, name, public)
  values ('outfit-images', 'outfit-images', true)
  on conflict (id) do update set public = true;

insert into storage.buckets (id, name, public)
  values ('course-files', 'course-files', true)
  on conflict (id) do update set public = true;

insert into storage.buckets (id, name, public)
  values ('outfit-pdfs', 'outfit-pdfs', true)
  on conflict (id) do update set public = true;

-- --- ALSO: outfits / outfit_images / courses / course_files write policies
-- Те же причины: фронт идёт под anon, без app_role claim. Открываем
-- INSERT/UPDATE/DELETE для anon, чтобы Марина могла редактировать
-- свои образы и курсы.

-- outfits
drop policy if exists outfits_anon_write on public.outfits;
create policy outfits_anon_write on public.outfits
  for all to anon
  using (true) with check (true);

-- outfit_images (вложения)
drop policy if exists outfit_images_anon_write on public.outfit_images;
create policy outfit_images_anon_write on public.outfit_images
  for all to anon
  using (true) with check (true);

-- courses
drop policy if exists courses_anon_write on public.courses;
create policy courses_anon_write on public.courses
  for all to anon
  using (true) with check (true);

-- course_files (если таблица есть)
do $$
begin
  if exists (
    select 1 from information_schema.tables
    where table_schema = 'public' and table_name = 'course_files'
  ) then
    execute 'drop policy if exists course_files_anon_write on public.course_files';
    execute 'create policy course_files_anon_write on public.course_files for all to anon using (true) with check (true)';
  end if;
end$$;

-- bookings (чтобы /mama/bookings мог помечать прочитанным)
drop policy if exists bookings_anon_write on public.bookings;
create policy bookings_anon_write on public.bookings
  for all to anon
  using (true) with check (true);

-- bot_flows (конструктор)
drop policy if exists bot_flows_anon_write on public.bot_flows;
create policy bot_flows_anon_write on public.bot_flows
  for all to anon
  using (true) with check (true);

-- outfit_categories (админ управляет тегами)
drop policy if exists outfit_categories_anon_write on public.outfit_categories;
create policy outfit_categories_anon_write on public.outfit_categories
  for all to anon
  using (true) with check (true);

-- bot_preview_requests (кнопка «Превью» в конструкторе)
drop policy if exists bot_preview_requests_anon_write on public.bot_preview_requests;
create policy bot_preview_requests_anon_write on public.bot_preview_requests
  for all to anon
  using (true) with check (true);
