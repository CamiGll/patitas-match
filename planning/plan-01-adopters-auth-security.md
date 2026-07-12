# Plan 01 — Adopter Self-Registration, Auth & RLS

| | |
|---|---|
| **Status** | 🔵 In progress (2026-07-12) |
| **Depends on** | plan-00 |
| **PRD sections** | §4.2 (FR-1.1…1.6), §7.1 |
| **Default model** | Sonnet; tasks 2 and 5 tagged `[opus]` |
| **Estimated effort** | ~3–4 sessions |

## Goal

Adopters create accounts (email+password), describe their home in free text, get an AI-parsed editable profile, and can only see/edit their own data. Staff log in and see everything. RLS is on with real policies; the anon key alone can no longer read or write anything.

## Out of scope

Dog browsing for adopters (plan-02), matching changes (plan-03), password-reset email templates beyond Supabase defaults, staff management UI (staff flag set manually in SQL).

## Context the implementer needs

- Structure from plan-00 (`src/` modules, migrations via Supabase CLI).
- Streamlit is multipage via a `pages/` directory; session state via `st.session_state`.
- **Key model:** in Streamlit everything runs server-side, but RLS only applies when queries carry the *user's* JWT. So: after login, create the per-user client with `create_client(url, anon_key)` + `client.postgrest.auth(session.access_token)`. Keep a separate service-role client (new secret `SUPABASE_SERVICE_KEY`) used ONLY inside staff-gated code paths.
- Auth decision locked: email + password (00-assessment.md).

## Implementation notes (2026-07-12)

- **Execution order deviates from task order to protect the deployed app:** all code (tasks 3–6) is written before the RLS migration (task 2) is applied, and the git push happens immediately after RLS turns on — single Supabase project means the old deployed app breaks the moment RLS is enabled.
- **`tiene_patio bool default false` added to the task-1 migration** — omitted from the column list but required by `PerfilAdoptante` (task 3), the profile form (task 6), and plan-03 matching.
- **Profile form includes a `nombre` input** — `adoptantes.nombre` is NOT NULL and `PerfilAdoptante` doesn't extract it.
- Migrations are applied via the Supabase MCP (no DB password available for `supabase db push`); local migration files are kept in lockstep and `supabase_migrations.schema_migrations` is synced so future CLI use is consistent.
- Test users for RLS verification are created via REST signup and email-confirmed via SQL (no inbox needed). Test accounts: `camila.galli10+test-adopter@gmail.com` (adopter with profile) and `+test-staff` (in `profiles_staff`).
- **Verified 2026-07-12:** full RLS matrix (bare anon: all denied; adopter JWT: own row only, cannot impersonate `user_id`, cannot write dogs; staff JWT: sees all, writes dogs) + Playwright UI flows (logged-out gate, adopter "solo staff" gate, profile page prefill, staff intake scoring a real self-registered adopter). Security advisors: only the intentional `is_staff()`-executable-by-authenticated WARN (policies evaluate it as the querying role; it reveals only the caller's own status).
- **Known limitation (accepted):** the session lives in `st.session_state`, so a full browser reload (F5) logs the user out; in-app sidebar navigation preserves it. Cookie-based persistence would be a new plan.
- `SUPABASE_SERVICE_KEY` is wired in `service_client()` but **no secret is set yet** — nothing in plan-01 needs it at runtime; add it (dashboard → Settings → API → service_role) when plan-04 system actions arrive.

## Tasks

### 1. Migration: adopter schema + roles `[sonnet]`
- [x] New migration adding to `adoptantes`: `user_id uuid unique references auth.users(id)`, `email varchar`, `descripcion_original text`, `tiene_perros bool default false`, `horas_fuera int`, `nivel_actividad varchar`, `experiencia varchar`, `acepta_notificaciones bool default true`.
- [x] CHECK constraints for enum-like fields: `tipo_vivienda in ('casa','departamento')`, `nivel_actividad in ('alto','medio','bajo')`, `experiencia in ('ninguna','algo','mucha')`. Also add the missing checks on `perros` (`edad`, `energia`) — data is test data; fix any violating rows in the migration.
- [x] `profiles_staff` table: `user_id uuid primary key references auth.users(id)` — presence = staff. (Simplest viable per FR-1.5.)
- [x] Apply with `supabase db push`; commit migration.

**Acceptance:** migration applies cleanly; existing rows conform or are fixed.

### 2. Migration: enable RLS + policies `[opus]`
Design carefully — this is the security boundary. One migration:
- [x] Enable RLS on `perros`, `adoptantes`, `historial_matches`, `profiles_staff`.
- [x] Helper: `create function is_staff() returns boolean language sql stable security definer as $$ select exists(select 1 from profiles_staff where user_id = auth.uid()) $$;` (security definer so it can read the table regardless of its own RLS; revoke direct access to `profiles_staff` except its own select-own policy).
- [x] Policies:
  - `adoptantes`: SELECT/UPDATE own row (`user_id = auth.uid()`); INSERT own (`with check user_id = auth.uid()`); staff SELECT all (`is_staff()`).
  - `perros`: staff ALL; (adopter read of `disponible` dogs arrives in plan-02 — don't add yet).
  - `historial_matches`: staff ALL; adopter SELECT where `adoptante_id` belongs to their own `adoptantes` row.
  - `profiles_staff`: SELECT own row only; no INSERT/UPDATE/DELETE policies (managed via SQL editor with service role).
- [x] Writes to `perros`/`historial_matches` from the app now require either a staff JWT or the service-role client — verify which path the intake flow uses (task 5).

**Acceptance:** with plain anon key (no JWT): every select/insert on the 3 tables returns zero rows / permission error. With adopter JWT: sees only own `adoptantes` row. Supabase security advisors show no RLS errors.

### 3. Pydantic model + extraction for adopters `[sonnet]`
- [x] `src/models.py`: `PerfilAdoptante` — `tipo_vivienda ('casa'|'departamento')`, `tiene_patio bool`, `tiene_ninos bool`, `tiene_gatos bool`, `tiene_perros bool`, `horas_fuera int (0–24)`, `nivel_actividad ('alto'|'medio'|'bajo')`, `experiencia ('ninguna'|'algo'|'mucha')` — use `Literal` types so Gemini is constrained.
- [x] `src/extraction.py`: `extract_perfil_adoptante(texto)` mirroring the dog extractor (same model, schema, temperature, retry).
- [x] Add 3 adopter stories to the golden set.

**Acceptance:** live golden test passes; invalid enum output impossible by schema.

### 4. Auth pages & session handling `[sonnet]`
- [x] `src/auth.py`: `sign_up(email, pwd)`, `sign_in(email, pwd)`, `sign_out()`, `get_user_client()` (anon client with user JWT attached), `current_user()`, `require_login()`, `require_staff()` guards. Store session (access+refresh token) in `st.session_state`; refresh if expired.
- [x] `pages/1_Ingresar.py`: login/signup tabs; friendly errors (wrong password, email already registered, unconfirmed email).
- [x] Sidebar shows logged-in email + logout button (shared helper).
- [x] Decide + document in code: email confirmation ON in Supabase Auth settings (default) — signup flow tells the user to check their inbox.

**Acceptance:** full cycle works: sign up → confirm → log in → session survives page navigation → log out.

### 5. Wire key usage correctly `[opus]`
- [x] Add `SUPABASE_SERVICE_KEY` to secrets; `src/clients.py` exposes `service_client()` and `user_client(jwt)`. `service_client()` must only be reachable from code behind `require_staff()` — enforce by module structure and a runtime assert.
- [x] Dog intake flow (existing `app.py`) becomes staff-only: `require_staff()` gate; its DB writes go through the staff user's JWT client (policies allow) — service client reserved for true system actions.

**Acceptance:** logged-out visit to intake page → redirected to login. Adopter account visiting intake → "solo staff" message. Staff account → full flow works with RLS on.

### 6. Adopter registration & profile page `[sonnet]`
- [x] `pages/2_Mi_Perfil.py` (login required): first visit → free-text "Contanos sobre tu hogar y estilo de vida" → AI extraction → editable form pre-filled with extracted values (`st.form`) → save creates `adoptantes` row with `user_id`, `email`, `descripcion_original`.
- [x] Return visits → same form pre-filled from DB; save updates.
- [x] AI failure fallback: empty form, manual fill (NFR-A2); original text always saved.

**Acceptance:** new adopter completes signup→profile in one sitting; corrections persist; second adopter cannot see the first's data.

### 7. Staff bootstrap + docs `[haiku]`
- [x] Document in README + this plan: how to make a user staff (`insert into profiles_staff (user_id) values ('<uuid>');` via SQL editor).
- [ ] Create Camila's staff row. **Pending: Camila signs up in the app first, then run the README insert.**

**Acceptance:** Camila's account passes `require_staff()`.

## Verification

Two fresh accounts (one staff, one adopter) exercise: adopter signup → profile via AI → sees only own data; staff registers a dog → matching runs against real adopter rows; anon REST call with bare anon key returns nothing. Run `get_advisors` (security) — zero RLS findings.

## Risks / hard sections

- **Task 2 `[opus]`**: policy mistakes either lock the app out or leave data exposed. Test with three clients: bare anon, adopter JWT, staff JWT.
- **Task 5 `[opus]`**: the service-role key must never be importable from adopter-reachable paths.
- Session refresh in Streamlit is fiddly (reruns); keep tokens + expiry in `st.session_state` and refresh lazily in `get_user_client()`.
- Existing 3 `adoptantes` rows have no `user_id` — either delete them (test data) or leave orphaned; matching in plan-03 will only consider rows with profiles. Simplest: delete in task 1's migration.
