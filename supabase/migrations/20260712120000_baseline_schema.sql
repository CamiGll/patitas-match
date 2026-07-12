-- Baseline: esquema existente capturado desde el proyecto live (plan-00, tarea 6).
-- Generado consultando information_schema/pg_constraint el 2026-07-12.
-- RLS queda deliberadamente deshabilitado en esta fase (ver plan-01 / PRD NFR-S1).

create table if not exists public.perros (
    id bigserial primary key,
    nombre varchar(100) not null,
    descripcion_original text,
    edad varchar(50),
    energia varchar(50),
    necesita_patio boolean default false,
    apto_ninos boolean default true,
    apto_gatos boolean default true,
    creado_en timestamptz default now()
);

create table if not exists public.adoptantes (
    id bigserial primary key,
    nombre varchar(100) not null,
    tiene_ninos boolean default false,
    tiene_gatos boolean default false,
    tipo_vivienda varchar(100),
    creado_en timestamptz default now()
);

create table if not exists public.historial_matches (
    id bigserial primary key,
    perro_id bigint references public.perros (id) on delete cascade,
    adoptante_id bigint references public.adoptantes (id) on delete cascade,
    porcentaje_afinidad integer not null,
    apto boolean not null,
    motivo text,
    evaluado_en timestamptz default now()
);
