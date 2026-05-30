-- 0013_marina_real_categories.sql
--
-- Реальные категории Марины Заугольниковой по её сайту zaugolnikova.ru.
-- Удаляем мои выдуманные love-story/беременность/семейная, ставим то,
-- что реально снимает Марина:
--   КОНТЕНТ (для соцсетей, экспертов)
--   ПОРТРЕТ (индивидуальная)
--   РЕПОРТАЖ (мероприятия)
--
-- Старые значения оставляем — бот их не валит, но Марина в админке /admin/categories
-- может их удалить вручную.

-- Добавляем новые kind-значения если их ещё нет
insert into public.outfit_categories(kind, value, sort_order) values
  ('occasions', 'контент', 10),
  ('occasions', 'портрет', 20),
  ('occasions', 'репортаж', 30),
  ('occasions', 'личный бренд', 40),
  ('occasions', 'эксперт', 50),
  ('occasions', 'предметная', 60),
  ('shoot_types', 'студия с естественным светом', 10),
  ('shoot_types', 'локация на улице', 20),
  ('shoot_types', 'дома у клиента', 30),
  ('shoot_types', 'мероприятие', 40),
  ('shoot_types', 'выезд', 50)
on conflict (kind, value) do nothing;

-- Гарантируем, что новые значения видны в верхней части списка
update public.outfit_categories set sort_order = sort_order
where kind in ('occasions', 'shoot_types');
