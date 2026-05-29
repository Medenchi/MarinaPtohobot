-- 0007_session_flow_guard.sql
--
-- Защищает bot_sessions от FK-ошибки 23503 при ссылке на удалённый
-- bot_flows.id. Делает две вещи:
--
-- 1. На уровне FK: ON DELETE SET NULL (вместо CASCADE/RESTRICT).
--    Если миграция 0005 уже применена с правильной семантикой — drop+add
--    безопасны, потому что `if exists`.
-- 2. На уровне триггера: BEFORE INSERT/UPDATE на bot_sessions —
--    если NEW.flow_id указывает на несуществующую строку, обнуляем его.
--    Это страховка от гонок и от ситуаций «вручную удалили flow в SQL Editor».

-- 1) Пересоздаём FK
do $$
begin
  if exists (
    select 1
    from information_schema.table_constraints
    where table_schema = 'public'
      and table_name = 'bot_sessions'
      and constraint_name = 'bot_sessions_flow_id_fkey'
  ) then
    alter table public.bot_sessions
      drop constraint bot_sessions_flow_id_fkey;
  end if;
end$$;

alter table public.bot_sessions
  add constraint bot_sessions_flow_id_fkey
  foreign key (flow_id) references public.bot_flows(id) on delete set null;

-- 2) Триггер-страховка
create or replace function public.bot_sessions_clamp_flow_id()
returns trigger
language plpgsql
as $$
begin
  if new.flow_id is not null
     and not exists (select 1 from public.bot_flows f where f.id = new.flow_id) then
    -- логируем в Postgres, чтобы было видно в логах supabase
    raise notice 'bot_sessions: stale flow_id=% cleared for telegram_id=%',
      new.flow_id, new.telegram_id;
    new.flow_id := null;
    new.current_node_id := null;
    new.awaiting_input := false;
  end if;
  return new;
end;
$$;

drop trigger if exists bot_sessions_clamp_flow_id on public.bot_sessions;
create trigger bot_sessions_clamp_flow_id
  before insert or update on public.bot_sessions
  for each row execute function public.bot_sessions_clamp_flow_id();

-- 3) Лечим текущие данные (если в строках уже сидит мертвый id)
update public.bot_sessions s
   set flow_id = null,
       current_node_id = null,
       awaiting_input = false
 where flow_id is not null
   and not exists (select 1 from public.bot_flows f where f.id = s.flow_id);
