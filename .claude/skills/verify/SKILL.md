---
name: verify
description: How to launch and drive Patitas Match end-to-end for verification (Streamlit + Playwright)
---

# Verifying Patitas Match

## Launch

```bash
.venv/Scripts/streamlit run app.py --server.headless true --server.port 8599
```

Secrets come from `.streamlit/secrets.toml` (SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY — all three must be real; extraction needs a valid Gemini key).

## Drive (Playwright, already in .venv)

- **Streamlit gotcha:** `textarea.fill()` alone is not enough — Streamlit commits the value on blur. After `fill()`, do `page.keyboard.press("Tab")` and wait ~1s before clicking the button, or the click submits the old value.
- Button: `page.get_by_role("button", name="Analizar y Buscar Adoptantes")`.
- Success oracle: wait for text "Panel de Decisiones Automatizado", then read `table tr` rows.
- Errors surface as `[data-testid="stAlert"]` — poll those in parallel with the success marker; waiting on success alone hangs 90s on failure.
- Duplicate guard: submitting the same dog name within 10 min shows "Ya existe un perro llamado" + a "Registrar de todos modos" checkbox.

## Oracle with seed adopters (ids 1–3)

Sofía (cats, depto), Carlos (kids, casa_con_patio), Laura (depto). A senior/low-energy/kid-incompatible/cat-friendly dog scores: Sofía 100%, Carlos 0% (hard block niños), Laura 100%.

## Cleanup

Delete test dogs afterward: `delete from perros where id in (...)` — `historial_matches` rows cascade.

## Gotchas

- `@st.cache_resource` clients: cache keys include the secret values, so secrets edits invalidate them (fixed 2026-07-12); still, restart the app if anything looks stale.
- Supabase free tier pauses the project when idle — if queries time out, restore it first (status INACTIVE).
