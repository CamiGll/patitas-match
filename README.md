# 🐾 Patitas Match

AI-assisted adoption matching for rescue dogs. Staff paste a dog's rescue story in plain Spanish; Gemini extracts a structured profile, the dog is saved to Supabase, and a deterministic rule engine scores compatibility against registered adopters.

## Stack

- **UI:** [Streamlit](https://streamlit.io/)
- **AI extraction:** Google Gemini (`gemini-2.5-flash`) via `google-genai`, constrained by Pydantic schemas
- **Database:** [Supabase](https://supabase.com/) (Postgres), schema versioned in `supabase/migrations/`
- **Matching:** deterministic, explainable rules (`src/matching.py`)

## Run locally

1. Install dependencies (Python 3.12):

   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

2. Create `.streamlit/secrets.toml` (git-ignored) with the three keys:

   ```toml
   SUPABASE_URL = "https://<project>.supabase.co"
   SUPABASE_KEY = "<anon key>"
   GEMINI_API_KEY = "<gemini key>"
   ```

3. Start the app:

   ```powershell
   .venv\Scripts\streamlit run app.py
   ```

## Tests

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\pytest -m "not live"
```

The golden extraction tests (`-m live`) call Gemini for real and are skipped unless `GEMINI_API_KEY` is set in the environment.

## Docs

- [`PRD.md`](PRD.md) — product requirements and decision log (the *what* and *why*)
- [`planning/`](planning/) — implementation plans and status (the *how* and *in what order*)
