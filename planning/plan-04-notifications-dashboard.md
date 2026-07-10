# Plan 04 — Email Notifications & Staff Dashboard

| | |
|---|---|
| **Status** | ⚪ Drafted |
| **Depends on** | plan-02, plan-03 |
| **PRD sections** | §4.6 (FR-4.1…4.3), §6 |
| **Default model** | Sonnet; task 2 tagged `[opus]` |
| **Estimated effort** | ~2–3 sessions |

## Goal

When matching produces strong candidates (≥80%), staff and opted-in adopters get an email. Staff get a dashboard showing the shelter's funnel: dogs per state, time-in-state, and match→adoption conversion.

## Out of scope

WhatsApp (PRD §9 trigger), per-user notification preferences beyond the existing opt-in flag, real-time/websocket updates.

## Context the implementer needs

- Matching writes happen in app code (`src/rematch.py`), so the simplest reliable trigger is app-side after a re-match completes — no DB webhooks needed for v1.
- Email provider decision: **Resend** free tier (3k emails/month), sent from a Supabase **Edge Function** so the API key lives in Supabase secrets, not Streamlit. Sender: `onboarding@resend.dev` until a domain exists (portfolio-acceptable).
- Adopters have `acepta_notificaciones` and `email` from plan-01.

## Tasks

### 1. Notification outbox `[sonnet]`
- [ ] Migration: `notificaciones` table — `id`, `tipo ('match_staff'|'match_adoptante'|'digest')`, `destinatario_email`, `payload jsonb`, `estado ('pendiente'|'enviada'|'fallida')`, `creado_en`, `enviado_en`. RLS: staff SELECT; no client writes (service/staff paths only).
- [ ] `src/notifications.py`: after a re-match, enqueue rows: one `match_staff` per dog with any vigente match ≥80 (payload: dog, top candidates); one `match_adoptante` per opted-in adopter newly matched ≥80 with a `disponible` dog. Dedupe: don't re-enqueue the same (tipo, dog, adopter) pair while a previous one is < 7 days old.

**Acceptance:** re-match run creates expected outbox rows exactly once; opt-out adopters excluded.

### 2. Edge Function sender `[opus]`
- [ ] `supabase/functions/enviar-notificaciones/index.ts`: reads `pendiente` rows (service role), renders simple Spanish HTML templates per tipo, sends via Resend API, marks `enviada`/`fallida` (with error in payload). Batch limit 20 per invocation.
- [ ] Secrets: `RESEND_API_KEY` via `supabase secrets set`.
- [ ] Invocation: called from the app right after enqueueing — protect it: require the service JWT or a shared secret header. Plus `supabase functions deploy` documented in README.
- [ ] Digest (FR-4.2): schedule the same function daily via Supabase cron (`pg_cron` + `net.http_post` or dashboard scheduled function) to sweep anything still `pendiente` and send a staff digest if >N items. Keep minimal.

**Acceptance:** end-to-end: register a matching dog → staff inbox receives the email within a minute; outbox row `enviada`. Failed send marks `fallida` without crashing the app flow.

### 3. Staff dashboard `[sonnet]`
> Before writing any chart code, load the `dataviz` skill.
- [ ] `pages/6_Panel.py` (staff): stat tiles (dogs per estado, adopters registered, adoptions total, return rate); funnel matches≥80 → en_proceso → adoptado; median days-in-state per estado (from `actualizado_en` history — add a lightweight `historial_estados` table in task 1's migration: `perro_id, estado, desde timestamptz`, written by `lifecycle.transicionar`).
- [ ] Metrics tie back to PRD §6 definitions (match coverage %, extraction-accuracy from `correcciones`).

**Acceptance:** dashboard renders with real data; numbers hand-verify against SQL on seeded dataset.

## Verification

Seeded run-through: adopter opts in → new compatible dog registered → adopter + staff emails arrive → dog adopted via lifecycle → dashboard funnel and return-rate update. Advisors (security + performance) clean.

## Risks / hard sections

- **Task 2 `[opus]`**: auth between app→Edge Function and idempotency (double-invoke must not double-send — mark rows `enviando` first or use `update ... where estado='pendiente' returning`).
- Resend free tier + `resend.dev` sender may land in spam — fine for portfolio; note real-domain setup as future work.
- Don't block the user-facing matching flow on email: enqueue is synchronous, sending is not.
