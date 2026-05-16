-- ============================================================
-- Seed data — optional. Run to get a working demo immediately.
-- ============================================================

insert into public.outfits
  (title, description, colors, styles, seasons, occasions, body_types, budgets, shoot_types, price_hint, sort_order)
values
  ('Тотал блэк',
   'Чёрное платье миди + ботильоны. Идеально для студийной съёмки.',
   'black', 'romantic,business', 'autumn,winter', 'photoshoot,party',
   'pear,hourglass', 'medium', 'studio',
   'до 8 000 ₽', 10),
  ('Прованс на улице',
   'Лёгкое бежевое платье + кеды. Романтичные кадры в природных локациях.',
   'beige,white', 'romantic,casual', 'summer,spring', 'photoshoot,everyday',
   'hourglass,rectangle', 'low', 'street',
   'до 4 000 ₽', 20),
  ('Деловая пресса',
   'Костюм в полоску + ботинки. Хорошо в людных локациях/городе.',
   'black,white,gray', 'business', 'all', 'photoshoot,everyday',
   'rectangle,hourglass', 'high', 'crowd,street',
   '15 000 ₽+', 30),
  ('Спорт-минимал',
   'Базовый трикотаж + кроссовки. Подходит для динамичной съёмки.',
   'gray,black,white', 'sport,casual', 'all', 'photoshoot,everyday',
   'rectangle,athletic', 'low', 'street,studio',
   'до 5 000 ₽', 40),
  ('Тёплая палитра',
   'Шерстяное пальто кэмел + ботинки. Зимняя локация в городе.',
   'beige,brown', 'romantic,casual', 'autumn,winter', 'photoshoot,party',
   'hourglass,pear', 'medium', 'street,crowd',
   '10 000 ₽', 50);

insert into public.courses (slug, title, short_description, description, sort_order)
values
  ('pose-basics',
   'База поз для фотосессии',
   'Бесплатный гайд: 15 базовых поз, которые работают всегда.',
   'PDF-гайд с примерами и подсказками. Подойдёт новичкам и опытным моделям.',
   10),
  ('color-palette',
   'Как подобрать цвета под себя',
   'Короткий курс по цветотипам и сочетаниям.',
   'Подробно разбираем 4 цветотипа и собираем гардероб под каждый.',
   20);
