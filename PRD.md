# Patitas Match — Product Requirements Document (PRD)

| | |
|---|---|
| **Product** | Patitas Match 🐾 |
| **Author** | Camila Galli |
| **Status** | Living document |
| **Last updated** | 2026-07-08 |
| **Repo** | https://github.com/CamiGll/patitas-match |
| **App version covered** | v0.1 (current) → v1.0 (target) |

---

## 1. Overview

### 1.1 Problem

Animal shelters and rescue volunteers describe rescued dogs in informal, unstructured text ("We found Ramiro wandering, he's a calm 9-year-old, no patience for kids but great with cats, ideal for an apartment"). Turning those stories into structured, comparable profiles — and then manually cross-checking each dog against every potential adopter's household — is slow, inconsistent, and error-prone. Bad matches lead to returned animals, which is traumatic for the animal and costly for the shelter.

### 1.2 Vision

**Streamline the pet adoption process for shelters by using AI to structure rescue stories and automatically match animals with the most compatible families.**

A volunteer pastes a rescue story; the system extracts a structured profile, stores it, and instantly ranks every registered adopter by compatibility — with transparent, explainable reasons for every score.

### 1.3 Context

This is a solo-built learning/portfolio project with no hard deadline, designed to demonstrate an end-to-end AI product: LLM structured extraction, relational persistence, a deterministic-plus-AI matching engine, and a real deployment. The PRD is written to production standards even where the implementation is intentionally MVP-scoped.

---

## 2. Users & Roles

| Role | Today (v0.1) | Target (v1.0) |
|---|---|---|
| **Shelter staff / volunteer** | Sole user. Registers dogs via free-text intake; views match results. | Authenticated role. Manages dog lifecycle, reviews matches, triggers notifications. |
| **Adopter** | Does not touch the app — rows exist only via manual DB inserts. | Self-registers with an account (Supabase Auth), fills a profile (free text parsed by AI + structured fields), receives match notifications. |

---

## 3. Current State (v0.1) — Implemented Features

### 3.1 Tech stack

| Layer | Technology | Notes |
|---|---|---|
| UI + app server | **Streamlit** (single-file `app.py`) | Secrets via `st.secrets` |
| AI extraction | **Google Gemini 2.5 Flash** via `google-genai` SDK | JSON structured output, Pydantic schema, `temperature=0.1` |
| Schema validation | **Pydantic** (`PerfilPerro`) | Defines the extraction contract |
| Database | **Supabase** (Postgres 17, `sa-east-1`) | `supabase-py` client, anon key |
| Language | Python | `requirements.txt`: `supabase`, `google-genai`, `pydantic`, `streamlit` |

### 3.2 Implemented functionality

**F1 — AI intake of rescued dogs.** Staff pastes an informal description; Gemini extracts a structured profile enforced by a Pydantic response schema:

| Field | Type | Values |
|---|---|---|
| `nombre` | str | lowercase name |
| `edad` | str | `cachorro` / `adulto` / `senior` |
| `energia` | str | `alto` / `medio` / `bajo` |
| `necesita_patio` | bool | needs a yard |
| `apto_ninos` | bool | OK with children |
| `apto_gatos` | bool | OK with cats |

**F2 — Persistence.** The extracted profile plus the original free text is inserted into `perros`; the new record ID is surfaced in the UI.

**F3 — Rule-based matching engine.** On every dog registration, all rows in `adoptantes` are scored (base 100):

- **Hard blocks** (score → 0, marked not apt): dog not OK with kids × adopter has kids; dog not OK with cats × adopter has cats.
- **Soft penalties**: dog needs yard × adopter in apartment (−30); high-energy dog × apartment (−20).
- Every evaluation produces a human-readable `motivo` (reason).

**F4 — Match history.** Every dog×adopter evaluation is persisted to `historial_matches` (score, apt flag, reason, timestamp) and rendered as a ranked table in the UI.

### 3.3 Current data model

```
perros                         adoptantes                  historial_matches
├─ id (PK, bigint)             ├─ id (PK, bigint)          ├─ id (PK, bigint)
├─ nombre (varchar)            ├─ nombre (varchar)         ├─ perro_id (FK → perros)
├─ descripcion_original (text) ├─ tiene_ninos (bool)       ├─ adoptante_id (FK → adoptantes)
├─ edad (varchar)              ├─ tiene_gatos (bool)       ├─ porcentaje_afinidad (int)
├─ energia (varchar)           ├─ tipo_vivienda (varchar)  ├─ apto (bool)
├─ necesita_patio (bool)       └─ creado_en (timestamptz)  ├─ motivo (text)
├─ apto_ninos (bool)                                       └─ evaluado_en (timestamptz)
├─ apto_gatos (bool)
└─ creado_en (timestamptz)
```

### 3.4 Known limitations & technical debt (v0.1)

| # | Issue | Severity | Notes |
|---|---|---|---|
| L1 | **RLS disabled on all 3 tables** — anyone holding the anon key can read/write every row via the Supabase REST API | 🔴 Critical | Fix in Phase 1 alongside Auth (see §7.1) |
| L2 | No adopter registration UI — matching runs against manually inserted rows | 🔴 High | Phase 1 |
| L3 | No error handling: Gemini failures, malformed JSON, or Supabase errors crash the Streamlit run mid-flow (dog may be inserted but matches not, or vice versa) | 🟠 High | Wrap in try/except, validate with `PerfilPerro.model_validate_json`, make insert+match resilient |
| L4 | No duplicate protection — resubmitting the same text creates duplicate dogs and duplicate match history | 🟠 Medium | |
| L5 | Matching runs client-side per adopter with one INSERT each (N round-trips); fine at 3 adopters, not at 300 | 🟡 Medium | Batch insert; later move matching server-side |
| L6 | Enum-like fields (`edad`, `energia`, `tipo_vivienda`) are free varchar — no DB constraint keeps values consistent with what the code compares against | 🟡 Medium | Postgres enums or CHECK constraints |
| L7 | Single-file app, no tests, no CI, no dependency pinning (`requirements.txt` has no versions) | 🟡 Medium | See §8 |
| L8 | Old match history is never invalidated when a dog or adopter would be re-evaluated | 🟡 Low | Re-match strategy defined in Phase 3 |

---

## 4. Future Condition (v1.0) — Product Requirements

### 4.1 Guiding decisions (agreed)

- **Platform:** stay on **Streamlit** (multipage app). Migration to a dedicated web frontend (e.g., Next.js + Supabase Auth) is explicitly *out of scope* for v1.0; §9 records the trigger criteria.
- **Matching:** **hybrid** — deterministic rules for safety-critical hard blocks and weighted scoring; Gemini generates the human-readable explanation per match. AI never overrides a hard block.
- **Auth:** **Supabase Auth for both roles** (adopters and staff), with a role claim and RLS policies.
- **Notifications:** **email first** (Supabase Edge Function + a transactional provider such as Resend). WhatsApp is a future consideration for the LatAm context.
- **Dog lifecycle:** full rescue flow (6-state machine, §4.4).

### 4.2 Phase 1 — Adopter self-registration & security foundation

*The core loop is incomplete until real adopters exist; exposing a public form makes the RLS fix non-negotiable, so they ship together.*

- **FR-1.1** Adopters sign up with email (Supabase Auth — email/password or magic link) and get a profile row linked by `user_id`.
- **FR-1.2** Adopter intake mirrors the dog intake UX: a free-text "tell us about your home and lifestyle" field parsed by Gemini into a structured `PerfilAdoptante` (housing type, yard, kids, cats, other dogs, hours away from home, activity level, experience with dogs), plus editable structured fields so the adopter can correct the AI.
- **FR-1.3** Adopters can view and edit their own profile only.
- **FR-1.4** RLS enabled on all tables with policies: adopters read/write their own row; only staff read all adopters and write dogs/matches; match history visible to staff and to the affected adopter.
- **FR-1.5** Staff role assignment (simplest viable: an `is_staff` flag or a `roles` table managed manually in v1.0).
- **FR-1.6** All privileged writes (dog insert, match insert) go through the service-role path server-side, never the anon key.

### 4.3 Phase 2 — Dog listing & lifecycle

- **FR-2.1** Dog list page: searchable/filterable table of all dogs (by status, energy, age, compatibility flags).
- **FR-2.2** Dog detail page: full profile, original rescue story, photos, status, and its match history.
- **FR-2.3** Photo upload to **Supabase Storage** (1–5 images per dog).
- **FR-2.4** Staff can edit any AI-extracted field (human-in-the-loop correction) and change status with an audit timestamp.
- **FR-2.5** Lifecycle state machine enforced in app logic and by a DB CHECK constraint (§4.4).
- **FR-2.6** Adopter-facing view lists only dogs in `disponible` status.

### 4.4 Dog lifecycle state machine

```
rescatado ──► en_recuperacion ──► disponible ──► en_proceso ──► en_transito ──► adoptado
                                      ▲               │              │             │
                                      └───────────────┴──────────────┴── devuelto ─┘
```

| State | Meaning |
|---|---|
| `rescatado` | Just rescued; intake done, not yet ready |
| `en_recuperacion` | Medical/behavioral recovery |
| `disponible` | Ready for adoption; visible to adopters; matching active |
| `en_proceso` | Matched with an adopter; interviews/visits ongoing |
| `en_transito` | Trial period in the adopter's home |
| `adoptado` | Final adoption confirmed (terminal, but reversible to `devuelto`) |
| `devuelto` | Returned; re-enters at `en_recuperacion` or `disponible` |

### 4.5 Phase 3 — Matching engine v2 (hybrid)

- **FR-3.1** Expanded variables on both sides: dog size, gets along with other dogs, minimum experience needed; adopter's other dogs, hours alone tolerance, activity level, dog-owning experience.
- **FR-3.2** Scoring = deterministic weighted model. Hard blocks (kids, cats, other dogs) remain absolute → score 0. Weights stored in a `matching_config` table so they are tunable without redeploying.
- **FR-3.3** Per-match explanation generated by Gemini from the score breakdown ("Ana's house has a yard and no kids, which suits Ramiro's profile; note she is away 9h/day and he dislikes being alone"). The numeric score is never produced by the LLM.
- **FR-3.4** Event-driven re-matching: registering a new adopter scores them against all `disponible` dogs; editing a profile re-scores affected pairs; superseded rows in `historial_matches` are marked stale rather than deleted (auditability).
- **FR-3.5** Match review UI for staff: ranked candidates per dog, explanation, and an action to move the dog to `en_proceso` with a chosen adopter.

### 4.6 Phase 4 — Notifications & operational polish

- **FR-4.1** Email notification (Edge Function + Resend or similar) to staff when a new dog gets any match ≥ 80%, and to an adopter when a newly available dog matches them ≥ 80% (opt-in flag on the adopter profile).
- **FR-4.2** Digest option (daily summary) to avoid spam as volume grows.
- **FR-4.3** Basic staff dashboard: dogs per status, average time in each state, match funnel (matches → processes → adoptions → returns).

---

## 5. Target data model additions (v1.0)

- `perros`: + `estado` (enum, §4.4), `tamano`, `apto_perros`, `experiencia_requerida`, `actualizado_en`.
- `fotos_perros`: `id`, `perro_id` FK, `storage_path`, `orden`.
- `adoptantes`: + `user_id` (FK → `auth.users`, unique), `descripcion_original`, `tiene_perros`, `horas_fuera`, `nivel_actividad`, `experiencia`, `acepta_notificaciones`, `email`.
- `historial_matches`: + `desglose_score` (jsonb: per-rule contribution), `explicacion_ia` (text), `vigente` (bool — stale flag).
- `matching_config`: `regla`, `peso`, `es_bloqueante`, `activa`.
- Enum types (or CHECK constraints) for `edad`, `energia`, `tipo_vivienda`, `estado`, `tamano`, `nivel_actividad`.

---

## 6. Success metrics

Portfolio-scoped: defined to demonstrate product thinking; the starred ones are actually measurable with the app's own data from day one.

| Metric | Target | How measured |
|---|---|---|
| ★ Intake time: rescue story → structured, stored profile | < 30 s | App timestamps |
| ★ AI extraction accuracy (fields needing no human correction) | ≥ 90% | Phase 2 edit-tracking (FR-2.4) as ground truth |
| ★ Match coverage: % of `disponible` dogs with ≥1 apt match ≥ 70% | ≥ 60% | `historial_matches` |
| Staff effort: manual cross-checking eliminated | 100% of pairs auto-scored | By construction; audit via history |
| Adoption funnel conversion (match → `en_proceso` → `adoptado`) | Baseline in Phase 4, then improve | Dashboard (FR-4.3) |
| Return rate (`devuelto` / `adoptado`) | < 10% | Lifecycle data — the ultimate quality signal for matching |

---

## 7. Non-functional requirements & best practices

### 7.1 Security

- **NFR-S1 (Critical, pre-Phase-1):** enable RLS on `perros`, `adoptantes`, `historial_matches` **together with** the policies in FR-1.4 — enabling RLS alone would break the current app. Until then, treat the anon key as fully privileged and never commit it.
- **NFR-S2:** secrets only in `st.secrets` / environment — never in git. Add `.gitignore` for `.streamlit/secrets.toml`.
- **NFR-S3:** service-role key used only server-side; anon key only for reads permitted by policy.
- **NFR-S4:** treat all free text as untrusted LLM input — extraction schema constrains output; never execute or interpolate model output.
- **NFR-S5:** re-run Supabase security advisors after every schema change.

### 7.2 AI quality & cost

- **NFR-A1:** all Gemini calls use response schemas (Pydantic) and low temperature; responses validated with `model_validate_json` before any DB write.
- **NFR-A2:** graceful degradation — if extraction fails, show the error and let staff fill the form manually; never lose the original text.
- **NFR-A3:** keep a small golden set of rescue stories with hand-labeled expected profiles; run it as a regression test when changing model or prompt.
- **NFR-A4:** model choice (`gemini-2.5-flash`) and prompt versions recorded; explanations (FR-3.3) generated in one batched call per dog, not per adopter, to control cost.

### 7.3 Engineering quality

- **NFR-E1:** restructure `app.py` into modules as Phase 1 lands: `pages/` (Streamlit multipage), `services/` (extraction, matching, notifications), `db/` (queries), `models/` (Pydantic).
- **NFR-E2:** pin dependencies (`requirements.txt` with versions or `uv`/`pip-tools` lockfile).
- **NFR-E3:** unit tests for the matching engine (pure function: profiles in → scores out) and the golden-set extraction test; run on GitHub Actions on every push.
- **NFR-E4:** schema changes applied as versioned Supabase migrations, not ad-hoc SQL, from Phase 1 onward.
- **NFR-E5:** matching writes batched (single multi-row insert) — removes L5.
- **NFR-E6:** wrap the intake flow in explicit steps with user-visible status so a mid-flow failure is recoverable (removes L3).

### 7.4 Reliability & performance

- **NFR-R1:** intake end-to-end (extraction + insert + matching) completes < 10 s at 100 adopters.
- **NFR-R2:** Gemini calls have a timeout and one retry; DB errors surface a readable message, never a stack trace.

---

## 8. Roadmap summary

| Phase | Theme | Key deliverables | Effort (solo) |
|---|---|---|---|
| **0 (done)** | AI intake + rule matching MVP | F1–F4 | — |
| **1** | Adopters + security | Supabase Auth, adopter AI intake, RLS + policies, code restructure | ~2–3 wks |
| **2** | Dog listing & lifecycle | List/detail pages, photos (Storage), state machine, human-in-the-loop edits | ~2–3 wks |
| **3** | Matching v2 | Expanded variables, weighted config, AI explanations, event-driven re-match, review UI | ~2–3 wks |
| **4** | Notifications & dashboard | Email (Edge Function), digests, funnel dashboard | ~1–2 wks |

Phases are sequenced by dependency and learning value, not dates (solo, no deadline).

---

## 9. Decision log & migration triggers

| Decision | Rationale | Revisit when |
|---|---|---|
| Stay on Streamlit | Solo Python developer, fastest iteration, free hosting, adequate for staff tool + adopter forms | Adopters need a polished public browsing/mobile experience, or auth UX in Streamlit becomes the bottleneck → evaluate Next.js + Supabase Auth for the public side only, keeping Streamlit for staff |
| Hybrid matching (rules score, AI explains) | Safety-critical decisions must be deterministic and auditable; LLM adds empathy and clarity, not risk | If weighted rules plateau in quality → explore LLM-assisted *ranking* with the rule score as a floor |
| Email before WhatsApp | Zero-cost, simple; WhatsApp Business API is heavy for a portfolio project | Real shelter adoption in LatAm → WhatsApp becomes Phase 5 |
| Spanish domain language in schema/UI, English docs | App serves Spanish speakers; docs target an international portfolio audience | — |

## 10. Out of scope (v1.0)

Multi-tenancy (multiple shelters), payments/donations, other species (schema says `perros`; a rename to `mascotas` + `especie` field is the cheap future-proofing if this ever changes), mobile app, WhatsApp, admin analytics beyond FR-4.3.
