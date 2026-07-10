# Plan 02 — Dog Listing, Detail & Lifecycle

| | |
|---|---|
| **Status** | ⚪ Drafted |
| **Depends on** | plan-01 |
| **PRD sections** | §4.3 (FR-2.1…2.6), §4.4 |
| **Default model** | Sonnet; task 1 partly `[haiku]`; no opus expected |
| **Estimated effort** | ~3 sessions |

## Goal

Dogs become manageable records with a lifecycle: staff browse/search all dogs, open a detail page with photos and match history, correct AI-extracted fields, and move dogs through the rescue state machine. Adopters see a gallery of `disponible` dogs only.

## Out of scope

Matching changes (plan-03), adopter applications/"I want this dog" button (belongs with FR-3.5 flow), notifications (plan-04), image editing/cropping.

## Context the implementer needs

- Auth guards (`require_login`, `require_staff`) and per-user clients exist from plan-01.
- State machine (PRD §4.4): `rescatado → en_recuperacion → disponible → en_proceso → en_transito → adoptado`, plus `devuelto` reachable from `en_proceso`/`en_transito`/`adoptado`, and `devuelto → en_recuperacion|disponible`.
- Supabase Storage is the photo store; bucket access must respect roles.

## Tasks

### 1. Migration: lifecycle + new dog fields `[sonnet]`
- [ ] Add to `perros`: `estado varchar not null default 'rescatado'` + CHECK constraint with the 7 states; `tamano varchar` CHECK `('chico','mediano','grande')`; `apto_perros bool default true`; `experiencia_requerida varchar` CHECK `('ninguna','algo','mucha')` default `'ninguna'`; `actualizado_en timestamptz default now()`.
- [ ] Trigger to auto-set `actualizado_en` on UPDATE. `[haiku]`
- [ ] `fotos_perros` table: `id bigint pk`, `perro_id fk not null`, `storage_path text not null`, `orden int default 0`. RLS: staff ALL; authenticated SELECT when the dog is `disponible` (join to `perros`).
- [ ] RLS addition on `perros`: authenticated users SELECT rows where `estado = 'disponible'` (this is the policy deliberately deferred from plan-01).
- [ ] Backfill existing dogs to `estado = 'disponible'`.
- [ ] Extend `PerfilPerro` with `tamano` and `apto_perros` (Literal types) so intake extracts them; update intake insert + golden set.

**Acceptance:** migration applies; adopter JWT can select `disponible` dogs and their photos, nothing else.

### 2. State machine module `[sonnet]`
- [ ] `src/lifecycle.py`: `TRANSICIONES: dict[str, set[str]]` encoding PRD §4.4 exactly; `puede_transicionar(desde, hacia) -> bool`; `transicionar(perro_id, nuevo_estado, client)` that validates then updates.
- [ ] Unit tests: every valid transition passes, a representative set of invalid ones (e.g., `rescatado → adoptado`) raise.

**Acceptance:** tests green; invalid transitions impossible through app code.

### 3. Storage bucket + photo upload `[sonnet]`
- [ ] Create bucket `fotos-perros` (via migration `insert into storage.buckets` or documented dashboard step — prefer migration). Private bucket; storage policies: staff write; public/authenticated read only for photos of `disponible` dogs — if the join-policy on storage objects proves awkward, acceptable fallback: bucket public-read, since photos of adoptable dogs are not sensitive; record the choice here.
- [ ] `src/photos.py`: upload (max 5 per dog, basic size/type check), list URLs (signed or public per bucket choice), delete.

**Acceptance:** staff uploads 2 photos to a dog; they render on list/detail; upload of a 6th is refused.

### 4. Staff dog list page `[sonnet]`
- [ ] `pages/3_Perros.py` (staff): table/cards of all dogs with thumbnail, `nombre`, `estado` (colored badge), `edad`, `energia`, `tamano`; filters (estado, energia, edad, apto flags) + name search; click-through to detail.

**Acceptance:** filters combine correctly; page loads with 50 seeded dogs without pagination pain (st.dataframe or paginated cards — implementer's choice).

### 5. Dog detail & edit page `[sonnet]`
- [ ] `pages/4_Perro.py?id=` (staff): full profile, `descripcion_original`, photo gallery + upload, match history table for this dog, edit form for all AI-extracted fields (human-in-the-loop, FR-2.4).
- [ ] Track corrections: on save, write changed-field names to a `correcciones jsonb` column on `perros` (add in task 1's migration) — this is the ground truth for the extraction-accuracy metric (PRD §6).
- [ ] Estado control: selectbox offering ONLY valid next states via `lifecycle.py`, with confirmation.

**Acceptance:** editing `energia` persists and logs the correction; estado widget never offers an illegal transition.

### 6. Adopter gallery `[sonnet]`
- [ ] `pages/5_Adoptar.py` (login required, adopter-friendly): card gallery of `disponible` dogs — photo, name, age, energy, compatibility icons. Read-only. Detail expander per dog (no staff data: no match history, no original clinical text if it contains sensitive info — show a cleaned public description field? Keep simple: show `descripcion_original`).

**Acceptance:** adopter sees only `disponible` dogs; a dog moved to `en_proceso` disappears from the gallery on refresh.

## Verification

Full staff loop: register dog (starts `rescatado`) → recovery → disponible (+ photos) → appears in adopter gallery → move to `en_proceso` → disappears from gallery. Match history visible on the detail page. All tests green.

## Risks / hard sections

- Storage RLS policies are the fiddliest bit; the documented public-read fallback keeps this plan unblocked.
- Streamlit query-param routing for the detail page (`st.query_params`) — keep it simple, fall back to a selectbox on the list page if params fight reruns.
