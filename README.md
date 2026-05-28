# Marina Photo — Telegram Bot + Constructor + Content Admin

Полный стек для проекта фотографа Марины Заугольниковой:

- **Бот**: aiogram 3.25+, движок исполняет блочный граф из Supabase
- **Сайт**: Vite + React + Tailwind, две роли — конструктор (`/admin`) и контент (`/mama`)
- **Авторизация**: одна Supabase Edge Function `admin-login` выдаёт JWT с claim `app_role`; RLS-политики на таблицах
- **БД + Storage**: Supabase (PostgreSQL + 3 bucket'а)
- **Никакого FastAPI сервера**: фронт ходит в Supabase напрямую через `supabase-js`, бот пишет/читает Supabase через `service_role`. Между мини-аппой и ботом — таблица `bot_preview_requests`.

## Структура репо

```
backend/        Python — только бот (polling Telegram + поллер превью)
frontend/       Vite/React — лендинг, конструктор, mama-админка
supabase/
  migrations/   SQL миграции (выполнять в SQL Editor по порядку)
  functions/    Deno Edge Functions (admin-login)
.github/        CI и деплой на GH Pages
```

## Поток данных

1. **Денис** заходит на `/admin/login`, вводит `ADMIN_PASSWORD`.
   - Frontend → POST `https://<project>.supabase.co/functions/v1/admin-login`
   - Edge Function → возвращает JWT с `app_role: admin`
   - Frontend кладёт токен в `localStorage` и шлёт его в Authorization-хедере всех Supabase-запросов
   - RLS-политики проверяют `app_role` через `public.app_role()` и пропускают только админа на `bot_flows`, `bot_preview_requests` и т.д.
2. **Конструктор** редактирует флоу → `bot_flows.graph` (jsonb). Нажатие "Превью" → INSERT в `bot_preview_requests`.
3. **Бот** (на VPS) каждые 2 сек поллит `bot_preview_requests` с `status='pending'` и шлёт превью Денису в Telegram.
4. **Опубликованный** флоу (`is_published=true`) исполняется ботом для всех остальных пользователей.
5. **Марина** заходит на `/mama/login` — тот же Edge Function, но с `MAMA_PASSWORD` → JWT с `app_role: mama`. Может управлять `outfits`, `courses`, `bookings`. RLS отделяет её от админских таблиц.

## Деплой

### Supabase (один раз)
1. Создай проект (Frankfurt eu-central-1)
2. SQL Editor → выполни миграции **по порядку**:
   - `supabase/migrations/0001_init.sql`
   - `supabase/migrations/0002_storage.sql`
   - `supabase/migrations/0005_constructor.sql`
   - `supabase/migrations/0006_supabase_only.sql`   ← новое (RLS + bot_preview_requests)
3. *(опционально)* `0004_seed.sql` — демо-образы
4. Деплой Edge Function (нужен установленный `supabase` CLI):
   ```sh
   supabase login
   supabase link --project-ref <project_ref>
   supabase functions deploy admin-login --no-verify-jwt
   supabase secrets set \
     APP_ADMIN_PASSWORD='...' \
     APP_MAMA_PASSWORD='...' \
     APP_JWT_SECRET='<JWT_Secret из Settings → API>'
   ```
5. Скопируй URL, anon key, service_role key — пригодится для VPS и фронта

### Бот (VPS)
```sh
cd backend
cp .env.example .env
# заполни BOT_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, BOT_OWNER_TELEGRAM_ID
poetry install
poetry run python -m app.main
```

### Фронтенд (GitHub Pages)
1. Variables: `VITE_SUPABASE_URL`
2. Secrets: `VITE_SUPABASE_ANON_KEY`
3. Settings → Pages → Source: GitHub Actions
4. Custom domain: `marinazau.denchy.cyou` (Save → дождись DNS check → включи Enforce HTTPS)
5. Push в `main` → workflow задеплоит на `marinazau.denchy.cyou`

### DNS — поддомен `marinazau` на Cloudflare → GitHub Pages
В Cloudflare на зоне `denchy.cyou`:
1. DNS → **Add record**
   - Type: **CNAME**
   - Name: `marinazau` (только сабдомен, без `.denchy.cyou`)
   - Target: `medenchi.github.io` (твой GitHub username + `.github.io`, без слэшей)
   - Proxy status: **DNS only** (серое облачко). После того как GitHub Pages выдаст HTTPS-сертификат, можно включить proxy (оранжевое облачко) для CDN/защиты.
   - TTL: Auto
2. Сохрани. Проверь `dig marinazau.denchy.cyou +short` — должен показать `medenchi.github.io` и IP-адреса GitHub Pages.
3. В репо: Settings → Pages → Custom domain → `marinazau.denchy.cyou` → Save.
4. Подожди 5–15 минут пока GitHub выпустит SSL-сертификат (зелёная галка появится в Pages settings).
5. Поставь галку **Enforce HTTPS**.

Файл `frontend/public/CNAME` уже содержит `marinazau.denchy.cyou` — Vite копирует его в `dist/` при билде, GitHub Pages его читает.

## Локальная разработка

### Бэк (только бот)
```sh
cd backend
poetry install
poetry run python -m app.main
```

### Фронт
```sh
cd frontend
cp .env.example .env.local   # пропиши VITE_SUPABASE_URL и VITE_SUPABASE_ANON_KEY
npm install
npm run dev
```

Логин на сайте бьёт прямо в задеплоенную Supabase Edge Function — отдельный бэкенд для разработки фронта не нужен.

## Иконки

В боте — премиум-кастомные эмодзи через `icon_custom_emoji_id` (Bot API 9.4).
Получить ID кастомного эмодзи: пересылаешь его боту `@get_emoji_id_robot`, кладёшь
в `.env` как `EMOJI_*`. Если поле пустое — бот красиво откатывается на текст с
обычным эмодзи в префиксе.

На сайте — [Phosphor Icons](https://phosphoricons.com).
