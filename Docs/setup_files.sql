-- Optional: lets the Homework Check chat box (student-portal/src/pages/ChatBox.tsx) keep a
-- student's attached files in their account and move them to/from a dashboard.
-- Without this the chat box still works; it just keeps files in the browser only.
-- Run once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
--
-- (The AI tutor does NOT need this. The Python server stores tutor submissions itself in a
--  private "submissions" bucket with the service key.)

-- 1) One row per file a student moves between the chat box and the dashboard
create table if not exists public.files (
  id          bigint generated always as identity primary key,
  user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
  location    text not null check (location in ('chat', 'dashboard')),
  name        text not null,
  path        text not null,            -- object path inside the homework-files bucket
  size        bigint not null default 0,
  type        text not null default '',
  origin      text not null,            -- 'upload' | 'chat' | 'dashboard' | 'submission'
  created_at  timestamptz not null default now()
);

alter table public.files enable row level security;

create policy "students read their own files" on public.files
  for select to authenticated using (user_id = auth.uid());
create policy "students add their own files" on public.files
  for insert to authenticated with check (user_id = auth.uid());
create policy "students delete their own files" on public.files
  for delete to authenticated using (user_id = auth.uid());

-- The chat box listens for new rows (files sent from the dashboard)
alter publication supabase_realtime add table public.files;

-- 2) Private bucket; each student may only touch objects under their own "<auth uid>/" folder
insert into storage.buckets (id, name, public)
values ('homework-files', 'homework-files', false)
on conflict (id) do nothing;

create policy "students upload to their folder" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'homework-files' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "students read their folder" on storage.objects
  for select to authenticated
  using (bucket_id = 'homework-files' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "students delete from their folder" on storage.objects
  for delete to authenticated
  using (bucket_id = 'homework-files' and (storage.foldername(name))[1] = auth.uid()::text);
