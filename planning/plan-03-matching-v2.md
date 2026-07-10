# Plan 03 — Matching Engine v2 (Hybrid)

| | |
|---|---|
| **Status** | ⚪ Drafted |
| **Depends on** | plan-01 (hard), plan-02 (recommended — uses `estado` and new dog fields) |
| **PRD sections** | §4.5 (FR-3.1…3.5), §7.2 |
| **Default model** | Sonnet; tasks 2 and 5 tagged `[opus]` |
| **Estimated effort** | ~3–4 sessions |

## Goal

Matching becomes a configurable weighted engine over the expanded profiles, with hard blocks intact, per-match AI explanations (score never from the LLM), event-driven re-matching when profiles change, and a staff review UI that turns a match into an adoption process.

## Out of scope

Notifications (plan-04), ML/learned weights, adopter-initiated applications.

## Context the implementer needs

- `src/matching.py` is a pure function from plan-00; extend, don't rewrite around it.
- Expanded fields exist after plans 01/02: dog `tamano`, `apto_perros`, `experiencia_requerida`, `energia`, `necesita_patio`, `apto_ninos`, `apto_gatos`; adopter `tiene_ninos/gatos/perros`, `tipo_vivienda`, `tiene_patio`, `horas_fuera`, `nivel_actividad`, `experiencia`.
- Cost rule (NFR-A4): explanations are ONE batched Gemini call per dog, not one per adopter.

## Scoring design (implement as specified)

**Hard blocks** (score 0, `apto=false`): `!apto_ninos × tiene_ninos`, `!apto_gatos × tiene_gatos`, `!apto_perros × tiene_perros`, `experiencia_requerida > experiencia` (orden: ninguna<algo<mucha).

**Weighted penalties** (from 100, floor 0), defaults in `matching_config`:

| regla | condición | peso |
|---|---|---|
| `patio` | necesita_patio ∧ ¬tiene_patio | 30 |
| `energia_vivienda` | energia=alto ∧ tipo_vivienda=departamento | 20 |
| `horas_solo` | horas_fuera ≥ 8 | 15 |
| `actividad` | energia=alto ∧ nivel_actividad=bajo (or inverse) | 15 |
| `tamano_depto` | tamano=grande ∧ tipo_vivienda=departamento | 10 |

## Tasks

### 1. Migration: config + match columns `[sonnet]`
- [ ] `matching_config`: `regla varchar pk`, `peso int not null`, `es_bloqueante bool default false`, `activa bool default true`. Seed hard blocks (`es_bloqueante`) + table above. RLS: staff ALL, authenticated SELECT.
- [ ] `historial_matches` add: `desglose_score jsonb`, `explicacion_ia text`, `vigente bool default true`.

**Acceptance:** migration applies; seeds present.

### 2. Engine rewrite `[opus]`
- [ ] `src/matching.py`: `score_match(perro, adoptante, config) -> MatchResult{afinidad, apto, desglose: dict[regla, int], motivo}`. Pure; config injected (list of rule rows). Unknown/None fields on either side → rule skipped and noted in desglose (`"sin_dato"`), never a crash.
- [ ] `match_perro_contra_adoptantes(perro, adoptantes, config)` and `match_adoptante_contra_perros(...)` — symmetric entry points.
- [ ] Rewrite/extend `tests/test_matching.py`: every hard block, every penalty, weight changes via config affect output, missing-field skip, floor at 0. Aim: this file is the engine's specification.

**Acceptance:** tests green; toggling `activa` on a rule in config changes scores with zero code change.

### 3. Batched AI explanations `[sonnet]`
- [ ] `src/explanations.py`: one Gemini call per dog taking the dog profile + list of scored adopters (id, score, desglose) → returns JSON array `{adoptante_id, explicacion}` (Pydantic schema, listed ids must match input). 2–3 sentence warm, honest Spanish explanations citing the desglose facts.
- [ ] On failure: fall back to the deterministic `motivo` string; never block the matching write.
- [ ] Store in `historial_matches.explicacion_ia`.

**Acceptance:** registering a dog with 5 adopters produces 5 explanations from a single API call; API-off fallback still persists matches.

### 4. Event-driven re-matching + staleness `[sonnet]`
- [ ] `src/rematch.py`: `on_perro_upsert(perro_id)` → mark this dog's `historial_matches` rows `vigente=false`, re-score against all adopters (with `user_id`), insert fresh rows. `on_adoptante_upsert(adoptante_id)` → same against all `disponible` dogs.
- [ ] Call sites: dog intake (exists), dog edit (plan-02 page), adopter profile create/save (plan-01 page).
- [ ] Only dogs in `disponible` get fresh matches; superseded rows are kept (`vigente=false`), never deleted.

**Acceptance:** editing an adopter's `tiene_gatos` flips their score against a cat-averse dog; old row remains with `vigente=false`.

### 5. Staff match review UI `[opus]`
- [ ] On dog detail page (plan-02): "Candidatos" section — current (`vigente`) matches ranked, score, badge, desglose expander, AI explanation.
- [ ] Action per candidate: "Iniciar proceso" → confirms → `transicionar(perro, 'en_proceso')` + record chosen `adoptante_id` (add `adoptante_elegido_id` FK to `perros` in task 1's migration) → other candidates greyed out.
- [ ] Guard rails: only offered when dog is `disponible`; cancelling the process (dog back to `disponible`) clears `adoptante_elegido_id`.

**Acceptance:** full happy path: dog disponible → review candidates → iniciar proceso → dog leaves adopter gallery (plan-02) and shows chosen adopter on detail page.

## Verification

Seed ~5 dogs × ~5 adopters with contrasting profiles; verify ranking sanity by hand on two dogs (desglose arithmetic checks out); explanation text references real facts; re-match on profile edit works; `pytest` green including new engine spec tests.

## Risks / hard sections

- **Task 2 `[opus]`**: the engine is the product's core logic — get the config-injection and missing-data semantics right; tests are the spec.
- **Task 5 `[opus]`**: touches state machine + FK + UI consistency; easy to leave dangling `adoptante_elegido_id`.
- Explanation batching: Gemini may hallucinate adopter ids — schema-constrain and validate the id set equals the input set; drop mismatches to fallback text.
