-- El linter marca is_staff() ejecutable por anon vía RPC. Las políticas la evalúan
-- con el rol del consultante, así que authenticated conserva EXECUTE; anon no la
-- necesita (sus consultas pasan a devolver error de permiso en vez de vacío — ok).
revoke execute on function public.is_staff() from public, anon;
