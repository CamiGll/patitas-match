-- Plan-01 task 1: adopter self-registration schema + staff roles.

alter table public.adoptantes
    add column user_id uuid unique references auth.users (id),
    add column email varchar(255),
    add column descripcion_original text,
    add column tiene_patio boolean default false,
    add column tiene_perros boolean default false,
    add column horas_fuera int,
    add column nivel_actividad varchar(20),
    add column experiencia varchar(20),
    add column acepta_notificaciones boolean default true;

-- Seed adopters predate auth (no user_id, test data) — remove them; their
-- historial_matches rows cascade. Real adopters arrive via self-registration.
delete from public.adoptantes;

alter table public.adoptantes
    add constraint adoptantes_tipo_vivienda_check
        check (tipo_vivienda in ('casa', 'departamento')),
    add constraint adoptantes_nivel_actividad_check
        check (nivel_actividad in ('alto', 'medio', 'bajo')),
    add constraint adoptantes_experiencia_check
        check (experiencia in ('ninguna', 'algo', 'mucha')),
    add constraint adoptantes_horas_fuera_check
        check (horas_fuera between 0 and 24);

-- Normalize existing perros test rows, then add the missing enum checks.
update public.perros set energia = 'bajo' where energia = 'baja';
update public.perros set energia = 'medio'
    where energia is null or energia not in ('alto', 'medio', 'bajo');
update public.perros set edad = 'adulto'
    where edad is null or edad not in ('cachorro', 'adulto', 'senior');

alter table public.perros
    add constraint perros_edad_check check (edad in ('cachorro', 'adulto', 'senior')),
    add constraint perros_energia_check check (energia in ('alto', 'medio', 'bajo'));

-- Staff role: presence of a row = staff (FR-1.5, simplest viable).
create table public.profiles_staff (
    user_id uuid primary key references auth.users (id)
);
