# 📚 Документация Marina Photo

Тут вся документация по проекту. Если попал сюда впервые — читай в этом
порядке.

## По ролям

| Кто ты | Что читать |
|---|---|
| 👩‍💼 **Марина** (контент-админ) | [`MAMA_GUIDE.md`](./MAMA_GUIDE.md) — как заливать образы, теги, фото, курсы |
| 🛠 **Денис** (владелец / разработчик) | [`ADMIN_GUIDE.md`](./ADMIN_GUIDE.md) — конструктор, категории, мини-конструктор в боте |
| 🧠 Разработчик, который правит флоу JSON руками | [`FLOW_FORMAT.md`](./FLOW_FORMAT.md) — полная спецификация формата |

## Шаблоны флоу

| Файл | Что |
|---|---|
| [`flows/marina_preshoot_brief.json`](./flows/marina_preshoot_brief.json) | Готовый бриф «перед съёмкой» — 29 узлов, 0 ошибок валидатора |

## Структура проекта

```
backend/                  Бот (aiogram 3) — единственный Python-процесс
  app/bot/runtime/        Движок исполнения флоу
    engine.py             - главный роутер aiogram
    blocks.py             - реализации всех типов блоков
    registry.py           - кеш published-флоу
    state.py              - сессии в Supabase
    validator.py          - AI-валидатор (правила)
    mini_constructor.py   - /builder в Telegram
    preview.py            - поллер bot_preview_requests
    keyboards.py          - inline / reply клавиатуры
    vars.py               - {{vars.x}}, {{user.first_name}}
    pdf.py                - генерация PDF подборок

frontend/                 React + Vite + Tailwind
  src/pages/
    Landing.tsx           публичный лендинг
    Login.tsx             /admin/login и /mama/login (один компонент, разные роли)
    admin/
      FlowList.tsx        список флоу
      Constructor.tsx     визуальный редактор графа
      Categories.tsx      справочник тэгов
    mama/
      Outfits.tsx         каталог образов с DropZone + TagPicker
      Courses.tsx         каталог курсов
      Bookings.tsx        заявки
      Stats.tsx           статистика
      Layout.tsx          общий лейаут /mama
  src/components/
    GraphCanvas.tsx       SVG-канвас с верёвочками
    VarsPanel.tsx         📖 панель переменных
    TagPicker.tsx         multi-select тегов
    AuthGuard.tsx         защита роутов
    Field.tsx             общие input/textarea/switch
    Footer.tsx
  src/lib/
    api.ts                все запросы к Supabase
    supabase.ts           создание клиента
    blockSchemas.ts       схемы полей для каждого типа блока
    blockTemplates.ts     12 готовых под-графов под флоу Марины
    seedGraph.ts          стартовый шаблон для пустого флоу
    validator.ts          AI-валидатор на TS (тот же что в Python)
    util.ts               classNames, shortId, ...

supabase/
  migrations/             SQL миграции (выполнять в SQL Editor по порядку)
  functions/admin-login/  Edge Function: пароль → JWT

docs/                     эта папка
```

## Поток данных

```
Клиент в Telegram
   ↓ (polling)
Бот на Wispbyte
   ↓ читает published bot_flows.graph (кеш 30 сек)
   ↓ исполняет блоки → пишет в bot_sessions / bot_events / bookings
Supabase (PostgreSQL + Storage + Edge Functions)
   ↑ supabase-js (anon key + JWT с app_role)
Сайт marinazau.denchy.cyou
   ↑ /admin/* (Денис) и /mama/* (Марина) — две роли, одна Edge Function admin-login
```

Никакого FastAPI / отдельного backend HTTP. Бот пишет в Supabase
service_role-ключом, фронт — anon key с JWT, всё разграничивается RLS-политиками
по `app_role`.

## Деплой одной строкой

```sh
git push origin main
# → GitHub Actions:
#    - Backend CI: ruff check + ruff format --check
#    - Frontend CI: tsc + eslint
#    - Deploy frontend to GitHub Pages → marinazau.denchy.cyou
# → На VPS/Wisp перезапустить контейнер бота (он сам делает git pull)
```
