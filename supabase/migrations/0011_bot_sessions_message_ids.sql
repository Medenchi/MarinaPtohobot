-- 0011_bot_sessions_message_ids.sql
-- Список id сообщений бота для удаления через блок delete_last_message / clear_chat.

alter table public.bot_sessions
  add column if not exists bot_message_ids jsonb not null default '[]'::jsonb;
