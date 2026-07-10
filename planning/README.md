# Planning — Patitas Match

This folder is the project's operating system: every piece of work starts as a plan here, gets implemented against its acceptance criteria, and is marked done. The source of truth for *what* we're building is [`../PRD.md`](../PRD.md); this folder is *how* and *in what order*.

## Index

| Plan | Theme | Status | Depends on |
|---|---|---|---|
| [00-assessment.md](00-assessment.md) | Current-state snapshot (strengths/weaknesses) | 📸 Snapshot | — |
| [plan-00-hardening.md](plan-00-hardening.md) | Restructure + fragility fixes, no new features | 🟡 Ready | — |
| [plan-01-adopters-auth-security.md](plan-01-adopters-auth-security.md) | Supabase Auth, adopter self-registration, RLS | ⚪ Drafted | plan-00 |
| [plan-02-dog-lifecycle.md](plan-02-dog-lifecycle.md) | Dog listing, detail, photos, state machine | ⚪ Drafted | plan-01 |
| [plan-03-matching-v2.md](plan-03-matching-v2.md) | Hybrid matching: weighted rules + AI explanations | ⚪ Drafted | plan-01 (plan-02 recommended) |
| [plan-04-notifications-dashboard.md](plan-04-notifications-dashboard.md) | Email notifications + staff dashboard | ⚪ Drafted | plan-02, plan-03 |

**Status legend:** ⚪ Drafted → 🟡 Ready (decisions resolved, next up) → 🔵 In progress → 🟢 Done → 🔴 Blocked

## Workflow rules

1. **One plan in progress at a time.** Finish or explicitly pause before starting another.
2. **Plans are contracts.** The implementing session follows the plan's tasks and acceptance criteria; if reality contradicts the plan, update the plan file first, then the code.
3. **Every schema change is a migration file** in `supabase/migrations/` (decision: single Supabase project, versioned migrations — see PRD §9). Never ad-hoc SQL in the dashboard.
4. **Update the status column here** when a plan changes state, and check off tasks inside the plan as they land.
5. **New features get a new plan file** (`plan-NN-slug.md`) following [TEMPLATE.md](TEMPLATE.md), added to the index. Feature PRDs, if written, live next to their plan as `prd-NN-slug.md`.

## Model routing & token economy

Plans in this folder are written by a high-reasoning model (**Fable/Opus**) with enough concrete detail (file paths, SQL, acceptance criteria) that a cheaper model (**Sonnet/Haiku**) can implement without re-deriving context. Rules of thumb:

- **Plan creation & revision:** Fable or Opus. Thinking is the expensive part; buy it once, encode it in the plan.
- **Implementation:** Sonnet by default; Haiku for mechanical tasks (renames, boilerplate, config files, straightforward CRUD pages).
- **Hard sections:** tasks tagged `[opus]` inside a plan involve security, concurrency, or subtle design — escalate to Opus/Fable for those tasks only, then drop back down.
- **Token-saving practices for implementing sessions:**
  - Read the plan file and ONLY the files it names — don't re-explore the repo.
  - Don't re-read `PRD.md` unless the plan links a specific section.
  - Don't re-verify decisions recorded in `00-assessment.md` § "Decisions locked" — they are settled.
  - Batch related edits; run the test suite once per task, not per edit.
  - When a task is done, tick its checkbox in the plan — that's the handoff state for the next session.

## Environment facts (so sessions don't rediscover them)

- Supabase project: `Patitas Match`, id `lizyjyqvnhmnjkpqfmlf`, region `sa-east-1`, Postgres 17.
- GitHub: `CamiGll/patitas-match`, default branch `main`.
- Secrets live in `.streamlit/secrets.toml` (git-ignored): `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`.
- Windows 11 dev machine; PowerShell; no Docker assumed.
