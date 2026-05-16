# Marina Photo — Telegram Bot + Mini App

Полный стек для проекта фотографа Марины Заугольниковой:

- **Бот**: aiogram 3.25+ с цветными кнопками и премиум-кастомными эмодзи
- **Мини-аппа / Сайт**: Vite + React + Tailwind, Phosphor Icons, чисто чёрно-белый дизайн
- **Админка**: простой вход по паролю (без email-регистрации)
- **БД + Storage**: Supabase (PostgreSQL + 3 bucket'а)

## Структура репо

```
backend/        Python — бот + админ-API (FastAPI)
frontend/       Vite/React — лендинг, мини-аппа, ридер PDF, админка
supabase/       SQL миграции (запускать в SQL Editor)
.github/        CI и деплой на GH Pages
```

## Сценарии бота

- `/start` — главное меню
- `/start obraz` — квиз из 7 вопросов → результаты в мини-аппе
- `/start pint` — бесплатные курсы / материалы

## Деплой

### Supabase (один раз)
1. Создай проект (Frankfurt eu-central-1)
2. SQL Editor → выполни `supabase/migrations/0001_init.sql`
3. SQL Editor → выполни `supabase/migrations/0002_storage.sql`
4. *(опционально)* `0004_seed.sql` — демо-данные
5. Скопируй URL, anon key, service_role key

### Бот + API (VPS)
```sh
cd backend
cp .env.example .env
# заполни BOT_TOKEN, SUPABASE_*, ADMIN_PASSWORD, JWT_SECRET
cd ..
docker compose up -d --build
```

### Фронтенд (GitHub Pages)
1. Variables: `VITE_SUPABASE_URL`, `VITE_API_URL` (например `https://api.marina.denchy.cyou`)
2. Secrets: `VITE_SUPABASE_ANON_KEY`
3. Settings → Pages → Source: GitHub Actions
4. Custom domain: `marina.denchy.cyou` (Save → дождись DNS check → включи Enforce HTTPS)
5. Push в `main` → workflow задеплоит на `marina.denchy.cyou`

### DNS — поддомен `marina` на Cloudflare → GitHub Pages
В Cloudflare на зоне `denchy.cyou`:
1. DNS → **Add record**
   - Type: **CNAME**
   - Name: `marina` (только сабдомен, без `.denchy.cyou`)
   - Target: `medenchi.github.io` (твой GitHub username + `.github.io`, без слэшей)
   - Proxy status: **DNS only** (серое облачко). После того как GitHub Pages выдаст HTTPS-сертификат, можно включить proxy (оранжевое облачко) для CDN/защиты.
   - TTL: Auto
2. Сохрани. Проверь `dig marina.denchy.cyou +short` — должен показать `medenchi.github.io` и IP-адреса GitHub Pages.
3. В репо: Settings → Pages → Custom domain → `marina.denchy.cyou` → Save.
4. Подожди 5–15 минут пока GitHub выпустит SSL-сертификат (зелёная галка появится в Pages settings).
5. Поставь галку **Enforce HTTPS**.

Файл `frontend/public/CNAME` уже содержит `marina.denchy.cyou` — workflow его копирует в билд, GitHub Pages его читает.

## Локальная разработка

### Бэк
```sh
cd backend
poetry install
poetry run python -m app.main
```

### Фронт
```sh
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Иконки

В боте — премиум-кастомные эмодзи через `icon_custom_emoji_id` (Bot API 9.4).
Получить ID кастомного эмодзи: пересылаешь его боту `@get_emoji_id_robot`, кладёшь
в `.env` как `EMOJI_*`. Если поле пустое — бот красиво откатывается на текст с
обычным эмодзи в префиксе.

На сайте — [Phosphor Icons](https://phosphoricons.com).
