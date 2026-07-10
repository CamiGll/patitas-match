# Current-State Assessment — 2026-07-09

Snapshot of where the project stands when this planning system was created. Implementing sessions: treat "Decisions locked" as settled — do not re-litigate.

## Strengths

1. **Complete working vertical slice**: real Gemini extraction → Supabase persistence → rule-based matching → persisted match history. The core loop exists and runs.
2. **AI best practices already in place**: Pydantic response schema, JSON mime type, `temperature=0.1`.
3. **Sound data model**: proper FKs, timestamps, audit table (`historial_matches`) from day one.
4. **Deterministic, explainable matching** — right call for a safety-relevant domain.
5. **Minimal sustainable stack** (Streamlit + Gemini Flash + Supabase free tier) for a solo developer.
6. **PRD with decision log exists** (`../PRD.md`).

## Weaknesses (priority order)

1. **Security**: RLS disabled on all 3 tables; anon key fully privileged; no auth/roles. → plan-01
2. **Half the core loop missing**: no adopter registration UI; matching runs against 3 hand-inserted rows. → plan-01
3. **Fragility**: no error handling (mid-flow failure leaves half-written state), `json.loads` without Pydantic validation, no duplicate protection, N+1 match inserts. → plan-00
4. **No engineering scaffolding**: single-file app, unpinned deps, no tests/CI/migrations, one-line README. → plan-00
5. **Data-quality debt**: enum-like fields are free varchar (an AI output of `"media"` vs `"medio"` silently breaks matching); no `estado` field. → plan-00/01/02

## Decisions locked (2026-07-09, with Camila)

| Decision | Choice |
|---|---|
| Hardening phase before features | **Yes — plan-00 runs first** |
| Dev/prod database | **Single Supabase project + versioned migrations** in `supabase/migrations/` |
| Auth method | **Email + password** via Supabase Auth (no magic link / OAuth — Streamlit redirect friction) |
| Testing bar | **Pragmatic**: pytest for matching engine + AI golden set, GitHub Actions on every push. No UI tests, no coverage gates. |
| Platform | Streamlit stays (PRD §9 has migration triggers) |
| Matching | Hybrid: deterministic scores, Gemini writes explanations only (PRD §4.5) |
| Notifications | Email first (PRD §4.6) |
| Docs language | English; app domain language Spanish |
