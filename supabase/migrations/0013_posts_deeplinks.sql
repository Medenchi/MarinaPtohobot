create table if not exists public.posts (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  created_at timestamptz not null default now(),
  clicks integer not null default 0
);

alter table public.posts enable row level security;

create policy posts_mama_all on public.posts
  for all to authenticated
  using (public.app_role() in ('admin', 'mama'))
  with check (public.app_role() in ('admin', 'mama'));

create policy posts_anon_read on public.posts
  for select to anon
  using (true);

create policy posts_anon_update on public.posts
  for update to anon
  using (true)
  with check (true);

create or replace function public.increment_post_clicks(p_code text)
returns void
language plpgsql
security definer
as $$
begin
  update public.posts set clicks = clicks + 1 where code = p_code;
end;
$$;
