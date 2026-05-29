-- 0010_outfit_gender_and_pdf.sql
--
-- 1. Добавляет колонку outfits.gender (для разделения мужских и женских
--    образов в флоу-подборщике).
-- 2. Расширяет CHECK в outfit_categories новым kind = 'gender' и сидит
--    два значения: 'женское', 'мужское'.
-- 3. Сидит 4 базовых женских образа-плейсхолдера (если outfits пустая),
--    чтобы Марина сразу могла протестировать флоу на /start, не дожидаясь
--    своих фотографий.

-- ---- 1) outfits.gender -------------------------------------------------
alter table public.outfits
  add column if not exists gender text not null default '';

create index if not exists outfits_gender_idx
  on public.outfits(gender);

-- ---- 2) Новый kind 'gender' в outfit_categories -----------------------
do $$
begin
  -- Drop old check (имя автогенеренное, ищем по pattern)
  perform 1
  from pg_constraint c
  join pg_class t on t.oid = c.conrelid
  where t.relname = 'outfit_categories'
    and c.contype = 'c'
    and pg_get_constraintdef(c.oid) ilike '%kind%';
  -- Безопаснее найти по имени, которое генерит Postgres
  if exists (
    select 1 from information_schema.check_constraints
    where constraint_schema = 'public'
      and constraint_name like 'outfit_categories_kind_check'
  ) then
    alter table public.outfit_categories
      drop constraint outfit_categories_kind_check;
  end if;
end$$;

alter table public.outfit_categories
  add constraint outfit_categories_kind_check
  check (kind in (
    'colors','styles','seasons','occasions',
    'body_types','budgets','shoot_types','gender'
  ));

insert into public.outfit_categories(kind, value, sort_order) values
  ('gender','женское',10),
  ('gender','мужское',20)
on conflict (kind, value) do nothing;
