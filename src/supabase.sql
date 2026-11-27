-- 端末間の同期のサーバー側(Supabase プロジェクト neuro-flashcards、フランクフルト)。
-- 2026-11-27 に、動いているデータベースから定義を読み出して記録した(この時点のサーバーと同じ内容)。
-- 仕組み:同期コードの SHA-256 を owner にして、{キー k, 項目 sk} ごとに値 v と時刻 t を1行で持つ。
--        push は時刻 t が新しいときだけ上書きし、seq を進める。pull は前回の seq より後の行を返す。
-- テーブルは RLS を有効にしてポリシーなし(anon は直接読めない)。anon が呼べるのは sync_pull と sync_push だけ。

create extension if not exists pgcrypto with schema extensions;

create sequence if not exists public.sync_seq;

create table if not exists public.sync_items (
  owner text   not null,
  k     text   not null,
  sk    text   not null,
  v     jsonb,
  t     bigint not null,
  seq   bigint not null default nextval('public.sync_seq'),
  primary key (owner, k, sk)
);
create index if not exists sync_items_owner_seq on public.sync_items (owner, seq);
alter table public.sync_items enable row level security;
revoke all on public.sync_items from anon, authenticated;

create or replace function public.sync_owner(p_code text)
 returns text
 language plpgsql
 immutable
 set search_path to ''
as $function$
begin
  if p_code is null or p_code !~ '^[A-Z2-9]{20,64}$' then
    raise exception 'bad code';
  end if;
  return encode(extensions.digest('neuro-flashcards:' || p_code, 'sha256'), 'hex');
end $function$;

create or replace function public.sync_pull(p_code text, p_since bigint)
 returns jsonb
 language plpgsql
 stable security definer
 set search_path to ''
as $function$
declare o text := public.sync_owner(p_code);
begin
  return jsonb_build_object(
    'items', coalesce((select jsonb_agg(jsonb_build_object('k', k, 'sk', sk, 'v', v, 't', t, 'seq', seq) order by seq)
                       from (select * from public.sync_items
                             where owner = o and seq > coalesce(p_since, 0)
                             order by seq limit 5000) q), '[]'::jsonb),
    'more', (select count(*) > 5000 from (select 1 from public.sync_items
             where owner = o and seq > coalesce(p_since, 0) limit 5001) c));
end $function$;

create or replace function public.sync_push(p_code text, p_items jsonb)
 returns bigint
 language plpgsql
 security definer
 set search_path to ''
as $function$
declare o text := public.sync_owner(p_code);
begin
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) > 3000 then
    raise exception 'bad items';
  end if;
  if length(p_items::text) > 3000000 then raise exception 'too large'; end if;
  insert into public.sync_items as s (owner, k, sk, v, t)
  select o, left(x->>'k', 100), left(coalesce(x->>'sk', ''), 1000),
         case when x->'v' = 'null'::jsonb then null else x->'v' end,
         (x->>'t')::bigint
  from jsonb_array_elements(p_items) x
  where x->>'k' like 'neuro-%' and x->>'t' is not null
  on conflict (owner, k, sk) do update
    set v = excluded.v, t = excluded.t, seq = nextval('public.sync_seq')
    where excluded.t > s.t;
  return coalesce((select max(seq) from public.sync_items where owner = o), 0);
end $function$;

revoke all on function public.sync_owner(text) from public, anon, authenticated;
revoke all on function public.sync_pull(text, bigint) from public;
revoke all on function public.sync_push(text, jsonb) from public;
grant execute on function public.sync_pull(text, bigint) to anon, authenticated;
grant execute on function public.sync_push(text, jsonb) to anon, authenticated;
