-- Family Circle: execute once in Supabase SQL Editor after creating a project.
-- DO NOT use a service-role key in the browser. Keep email confirmation enabled.
create extension if not exists pgcrypto;
create table if not exists public.family_members (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null check (char_length(display_name) between 2 and 60),
  role text not null default 'member' check (role in ('admin','member')),
  created_at timestamptz not null default now(),
  active boolean not null default true
);
create or replace function public.is_family_member()
returns boolean language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.family_members where user_id=auth.uid() and active=true)
$$;
create or replace function public.is_family_admin()
returns boolean language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.family_members where user_id=auth.uid() and role='admin' and active=true)
$$;
create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  kind text not null check (kind in ('direct','group')),
  title text,
  direct_key text unique,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  check ((kind='direct' and direct_key is not null) or (kind='group' and direct_key is null and char_length(title) between 2 and 64))
);
create table if not exists public.conversation_members (
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references public.family_members(user_id) on delete cascade,
  joined_at timestamptz not null default now(),
  primary key(conversation_id,user_id)
);
create or replace function public.can_read_conversation(cid uuid)
returns boolean language sql stable security definer set search_path='' as $$
  select public.is_family_member() and exists(
    select 1 from public.conversation_members cm
    where cm.conversation_id=cid and cm.user_id=auth.uid()
  )
$$;
create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  sender_id uuid not null references public.family_members(user_id),
  body text not null check(char_length(btrim(body)) between 1 and 4000),
  created_at timestamptz not null default now()
);
create index if not exists messages_conversation_time_idx on public.messages(conversation_id, created_at);
create table if not exists public.family_photos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.family_members(user_id),
  storage_path text not null unique,
  caption text not null default '' check(char_length(caption)<=120),
  created_at timestamptz not null default now()
);
create table if not exists public.family_invites (
  code_hash text primary key,
  email text not null,
  created_by uuid not null references public.family_members(user_id),
  expires_at timestamptz not null,
  redeemed_at timestamptz,
  redeemed_by uuid references auth.users(id),
  created_at timestamptz not null default now()
);
create index if not exists invite_email_idx on public.family_invites(email);
alter table public.family_members enable row level security;
alter table public.conversations enable row level security;
alter table public.conversation_members enable row level security;
alter table public.messages enable row level security;
alter table public.family_photos enable row level security;
alter table public.family_invites enable row level security;
create policy members_read on public.family_members for select to authenticated using (public.is_family_member() or user_id=auth.uid());
create policy conversations_read on public.conversations for select to authenticated using (public.can_read_conversation(id));
create policy cm_read on public.conversation_members for select to authenticated using (public.can_read_conversation(conversation_id));
create policy messages_read on public.messages for select to authenticated using (public.can_read_conversation(conversation_id));
create policy messages_write on public.messages for insert to authenticated with check (sender_id=auth.uid() and public.can_read_conversation(conversation_id));
create policy photos_read on public.family_photos for select to authenticated using (public.is_family_member());
create policy photos_add on public.family_photos for insert to authenticated with check (user_id=auth.uid() and public.is_family_member() and storage_path like (auth.uid()::text||'/%'));
-- Invite records have no direct client policy (fail closed). Only RPC functions access them.
create or replace function public.issue_family_invite(invite_email text)
returns text language plpgsql security definer set search_path='' as $$
declare code text; email_value text;
begin
  if not public.is_family_admin() then raise exception 'Access denied'; end if;
  email_value:=lower(btrim(invite_email));
  if email_value !~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$' or char_length(email_value)>254 then raise exception 'Invalid email'; end if;
  code:=encode(extensions.gen_random_bytes(24),'hex');
  insert into public.family_invites(code_hash,email,created_by,expires_at)
  values(encode(extensions.digest(code,'sha256'),'hex'),email_value,auth.uid(),now()+interval '48 hours');
  return code;
end; $$;
create or replace function public.redeem_family_invite(invite_code text, preferred_name text)
returns boolean language plpgsql security definer set search_path='' as $$
declare invitation public.family_invites%rowtype; verified_email text;
begin
  if auth.uid() is null then raise exception 'Access denied'; end if;
  select lower(email) into verified_email from auth.users
  where id=auth.uid() and email_confirmed_at is not null;
  if verified_email is null then raise exception 'Confirm your email before joining'; end if;
  if char_length(btrim(preferred_name)) not between 2 and 60 then raise exception 'Invalid name'; end if;
  if exists(select 1 from public.family_members where user_id=auth.uid()) then raise exception 'Account already registered'; end if;
  select * into invitation from public.family_invites
  where code_hash=encode(extensions.digest(lower(btrim(invite_code)),'sha256'),'hex')
  and redeemed_at is null and expires_at>now() and email=verified_email for update;
  if not found then raise exception 'Invitation invalid or expired'; end if;
  insert into public.family_members(user_id,display_name,role) values(auth.uid(),btrim(preferred_name),'member');
  update public.family_invites set redeemed_at=now(),redeemed_by=auth.uid() where code_hash=invitation.code_hash;
  return true;
end; $$;
create or replace function public.start_direct_chat(other_id uuid)
returns uuid language plpgsql security definer set search_path='' as $$
declare cid uuid; key_value text;
begin
  if not public.is_family_member() or other_id=auth.uid() or not exists(select 1 from public.family_members where user_id=other_id and active) then raise exception 'Access denied'; end if;
  key_value:=least(auth.uid()::text,other_id::text)||':'||greatest(auth.uid()::text,other_id::text);
  insert into public.conversations(kind,direct_key,created_by)
  values('direct',key_value,auth.uid())
  on conflict (direct_key) do update set direct_key=excluded.direct_key returning id into cid;
  insert into public.conversation_members(conversation_id,user_id) values(cid,auth.uid()),(cid,other_id) on conflict do nothing;
  return cid;
end; $$;
create or replace function public.create_family_group(group_title text,family_user_ids uuid[])
returns uuid language plpgsql security definer set search_path='' as $$
declare cid uuid; desired_count integer; valid_count integer;
begin
  if not public.is_family_member() or char_length(btrim(group_title)) not between 2 and 64 then raise exception 'Access denied'; end if;
  desired_count:=coalesce(cardinality(family_user_ids),0);
  if desired_count>30 then raise exception 'Too many participants'; end if;
  select count(distinct user_id) into valid_count from public.family_members
  where user_id=any(family_user_ids) and active=true and user_id<>auth.uid();
  if desired_count<>valid_count then raise exception 'Some participants are invalid'; end if;
  insert into public.conversations(kind,title,created_by) values('group',btrim(group_title),auth.uid()) returning id into cid;
  insert into public.conversation_members(conversation_id,user_id)
  select cid,user_id from (select auth.uid() as user_id union select unnest(family_user_ids)) x;
  return cid;
end; $$;
revoke all on public.family_invites from anon,authenticated;
revoke all on public.family_members,public.conversations,public.conversation_members,public.messages,public.family_photos from anon;
grant select on public.family_members,public.conversations,public.conversation_members,public.messages,public.family_photos to authenticated;
grant insert on public.messages,public.family_photos to authenticated;
revoke all on function public.is_family_member(),public.is_family_admin(),public.can_read_conversation(uuid),public.issue_family_invite(text),public.redeem_family_invite(text,text),public.start_direct_chat(uuid),public.create_family_group(text,uuid[]) from public,anon;
grant execute on function public.is_family_member(),public.is_family_admin(),public.can_read_conversation(uuid),public.issue_family_invite(text),public.redeem_family_invite(text,text),public.start_direct_chat(uuid),public.create_family_group(text,uuid[]) to authenticated;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('family-gallery','family-gallery',false,5242880,array['image/jpeg','image/png','image/webp'])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;
create policy family_image_read on storage.objects for select to authenticated
using(bucket_id='family-gallery' and public.is_family_member());
create policy family_image_upload on storage.objects for insert to authenticated
with check(bucket_id='family-gallery' and public.is_family_member() and (storage.foldername(name))[1]=auth.uid()::text);
create policy family_image_delete on storage.objects for delete to authenticated
using(bucket_id='family-gallery' and public.is_family_member() and (storage.foldername(name))[1]=auth.uid()::text);
alter publication supabase_realtime add table public.messages;
-- BOOTSTRAP: after YOUR email-verified signup, run ONCE, replacing email:
-- insert into public.family_members(user_id,display_name,role)
-- select id,'مدیر خانواده','admin' from auth.users
-- where email='your-real-email@example.com' and email_confirmed_at is not null;
-- Never commit real family email addresses, invite codes, or API secrets.
