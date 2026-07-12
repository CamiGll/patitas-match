# Plan 00 — Hardening & Restructure (no new features)

| | |
|---|---|
| **Status** | 🟢 Done (2026-07-12) |
| **Depends on** | — |
| **PRD sections** | §3.4 (L3–L7), §7.2, §7.3 |
| **Default model** | Sonnet (tasks tagged `[haiku]` are fine for Haiku) |
| **Estimated effort** | ~2 sessions |

## Goal

Same features as today, but the codebase is modular, validated, error-tolerant, dependency-pinned, under test and CI, and the DB schema is captured as a baseline migration. Every later plan builds on this structure.

## Out of scope

Auth, RLS, adopter UI, new matching rules, new pages. **Do not** enable RLS in this plan — the app still uses the anon key for everything and would break (PRD NFR-S1).

## Context the implementer needs

- The whole app is currently `app.py` (139 lines). Read it fully before starting.
- Secrets come from `st.secrets`; there is no local `secrets.toml` committed (keep it that way).
- Supabase schema (already live, do not change it in this plan): see PRD §3.3.
- The repo clone may be on a detached HEAD — ensure work happens on `main`.

## Target structure

```
patitas-match/
├── app.py                  # Streamlit entry: page config + intake UI only
├── src/
│   ├── __init__.py
│   ├── models.py           # PerfilPerro (moved), future Pydantic models
│   ├── clients.py          # cached Supabase + Gemini client factories (st.cache_resource)
│   ├── extraction.py       # extract_perfil_perro(texto) -> PerfilPerro | raises ExtractionError
│   ├── matching.py         # PURE functions: score_match(perro: dict, adoptante: dict) -> MatchResult
│   └── db.py               # insert_perro, get_adoptantes, insert_matches (batched)
├── tests/
│   ├── test_matching.py
│   └── golden/
│       ├── casos.json      # rescue stories + expected PerfilPerro fields
│       └── test_extraction_golden.py   # marked @pytest.mark.live (needs GEMINI_API_KEY)
├── .github/workflows/ci.yml
├── supabase/migrations/    # baseline migration (task 6)
├── requirements.txt        # pinned
├── .gitignore
└── README.md
```

## Tasks

### 1. Git & repo hygiene `[haiku]`
- [x] Confirm on branch `main` (`git switch main` if detached).
- [x] `.gitignore`: `.streamlit/secrets.toml`, `__pycache__/`, `.venv/`, `*.pyc`, `.pytest_cache/`.
- [x] README: what the app is, stack, how to run locally (`pip install -r requirements.txt`, create `.streamlit/secrets.toml` with the 3 keys, `streamlit run app.py`), link to `PRD.md` and `planning/`.

**Acceptance:** `git status` clean of junk; README covers setup end-to-end.

### 2. Pin dependencies `[haiku]`
- [x] Pin all 4 packages to their currently-installed versions (`pip show <pkg>`); add `pytest` to a new `requirements-dev.txt`.

**Acceptance:** fresh `pip install -r requirements.txt` succeeds; app still runs.

### 3. Restructure into modules `[sonnet]`
- [x] Create `src/` layout above; move code without changing behavior.
- [x] `clients.py`: wrap client creation in `@st.cache_resource` so clients aren't rebuilt every rerun.
- [x] `matching.py`: `score_match(perro, adoptante)` returns a small dataclass/dict `{afinidad, apto, motivo}` — no Streamlit, no Supabase imports (must be unit-testable).
- [x] `app.py` keeps only UI flow, calling the modules.

**Acceptance:** `streamlit run app.py` reproduces today's exact behavior (intake → JSON shown → insert → match table).

### 4. Validation & error handling `[sonnet]`
- [x] Replace `json.loads(response.text)` with `PerfilPerro.model_validate_json(response.text)`; use the model instance (`.model_dump()`) for the insert.
- [x] Wrap the flow in three user-visible steps (`st.status` or sequential spinners): ① AI extraction ② save dog ③ matching. Each step try/excepts and shows `st.error` with a readable message; a failure in ① or ② stops the flow (no partial writes after a failed step).
- [x] Gemini call: timeout + one retry on transient failure.
- [x] Duplicate guard: before insert, query `perros` for same `nombre` created in the last 10 minutes; if found, show `st.warning` with the existing ID and require a "Registrar de todos modos" confirmation (e.g., checkbox) to proceed.

**Acceptance:** with a wrong `GEMINI_API_KEY`, the app shows a friendly error and inserts nothing. Submitting the same story twice within 10 min triggers the warning.

### 5. Batch match inserts `[haiku]`
- [x] Collect all match rows and insert with a single `supabase.table("historial_matches").insert(list_of_rows).execute()`.

**Acceptance:** one network call regardless of adopter count; table output unchanged.

### 6. Baseline migration `[sonnet]`
- [x] Install Supabase CLI (`scoop install supabase` or the Windows installer); `supabase init`; `supabase login`; `supabase link --project-ref lizyjyqvnhmnjkpqfmlf`.
- [x] `supabase db pull` to capture the current schema as the baseline migration; commit `supabase/` (the CLI's generated `.gitignore` handles temp files).

**Acceptance:** `supabase/migrations/<timestamp>_remote_schema.sql` exists in git and recreates the 3 tables.

### 7. Tests + CI `[sonnet]`
- [x] `tests/test_matching.py`: cover hard block kids, hard block cats, both blocks, yard penalty (−30), energy penalty (−20), stacked penalties (50), clean 100% match. Pure-function tests, no mocks needed.
- [x] Golden set: 5 rescue stories in `tests/golden/casos.json` with expected field values; `test_extraction_golden.py` calls Gemini for real, marked `@pytest.mark.live`, skipped when `GEMINI_API_KEY` is absent.
- [x] `.github/workflows/ci.yml`: on push/PR → Python 3.12, install deps, `pytest -m "not live"`.

**Acceptance:** `pytest -m "not live"` green locally; Actions run green on GitHub after push.

## Verification

Run the app, register a test dog, confirm identical behavior to pre-refactor (plus the new step indicators). `pytest -m "not live"` green. CI green.

## Implementation notes (2026-07-12)

Deviations from the plan as written, per workflow rule 2:

- **Task 2:** no packages were installed locally — the app had only ever run on Streamlit Cloud. Created `.venv` (Python 3.12, matching CI) and pinned fresh-install versions: `supabase==2.31.0`, `google-genai==2.11.0`, `pydantic==2.13.4`, `streamlit==1.59.1`, `pytest==9.1.1`.
- **Task 4:** duplicate-guard flow uses `st.session_state` to keep the extracted profile across the checkbox rerun, so confirming a duplicate does not re-call Gemini.
- **Task 6:** Supabase CLI not installed and `supabase login` is interactive — used the plan's sanctioned fallback: baseline migration hand-written from the live schema (queried via `information_schema`/`pg_constraint`), committed as `supabase/migrations/20260712120000_baseline_schema.sql`. **Update (same day):** CLI v2.109.1 installed at `%LOCALAPPDATA%\Programs\supabase` (on user PATH) and `supabase init` run (config.toml committed). **Pending for plan-01:** Camila runs `supabase login`, then `supabase link --project-ref lizyjyqvnhmnjkpqfmlf`.
- Added `pytest.ini` (marker registration + `pythonpath`), not in the original target structure.
- `.streamlit/secrets.toml` created locally (git-ignored) with Supabase URL + anon key; Camila filled in `GEMINI_API_KEY`.
- **Verified E2E 2026-07-12** (Playwright driving the real UI): happy path matches the pre-refactor oracle exactly (Sofía 100 / Carlos 0 / Laura 100), duplicate guard stops the flow and proceeds on confirmation, empty input is a no-op, invalid Gemini key shows the step-① error with zero DB writes. Verification caught one regression, fixed same day: `@st.cache_resource` clients were pinned to the secrets at first use — factories now take credentials as cache-key arguments. Test rows cleaned up. Recipe persisted in `.claude/skills/verify/SKILL.md`.

## Risks / hard sections

- Task 3 is the only one with regression risk — behavior must be byte-for-byte equivalent; the match table is the oracle.
- Task 6 first-time CLI setup on Windows can be fiddly (PATH, access token). If `db pull` fights the linked project, an acceptable fallback is copying the schema DDL from the dashboard into a hand-written baseline migration — but prefer the CLI.
