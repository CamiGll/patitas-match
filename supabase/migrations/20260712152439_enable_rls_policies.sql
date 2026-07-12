-- Plan-01 task 2: RLS on all tables. From here on the bare anon key sees nothing.

alter table public.perros enable row level security;
alter table public.adoptantes enable row level security;
alter table public.historial_matches enable row level security;
alter table public.profiles_staff enable row level security;

-- security definer para poder leer profiles_staff sin que su propia RLS interfiera
create function public.is_staff() returns boolean
language sql stable security definer set search_path = public
as $$ select exists (select 1 from profiles_staff where user_id = auth.uid()) $$;

-- adoptantes: cada uno ve/edita/crea SOLO su fila; staff lee todas
create policy adoptantes_select_own on public.adoptantes
    for select using (user_id = auth.uid());
create policy adoptantes_update_own on public.adoptantes
    for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy adoptantes_insert_own on public.adoptantes
    for insert with check (user_id = auth.uid());
create policy adoptantes_staff_select on public.adoptantes
    for select using (public.is_staff());

-- perros: staff todo; la lectura de 'disponibles' por adoptantes llega en plan-02
create policy perros_staff_all on public.perros
    for all using (public.is_staff()) with check (public.is_staff());

-- historial_matches: staff todo; adoptante lee solo matches de su propia fila
create policy matches_staff_all on public.historial_matches
    for all using (public.is_staff()) with check (public.is_staff());
create policy matches_select_own on public.historial_matches
    for select using (
        exists (
            select 1 from public.adoptantes a
            where a.id = adoptante_id and a.user_id = auth.uid()
        )
    );

-- profiles_staff: solo ver la fila propia; sin INSERT/UPDATE/DELETE (se gestiona con service role)
create policy staff_select_own on public.profiles_staff
    for select using (user_id = auth.uid());
