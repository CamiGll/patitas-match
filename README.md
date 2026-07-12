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

## Roles & staff bootstrap

Anyone can create an adopter account in the app (email + password, confirmation email required). **Staff** is granted by inserting the user's UUID into `profiles_staff` via the Supabase SQL editor (there is no UI for this on purpose):

```sql
insert into profiles_staff (user_id)
select id from auth.users where email = 'person@example.com';
```

Row Level Security is enabled on all tables: adopters see and edit only their own profile; the dog-intake page and all dog/match data require a staff account; the bare anon key can read nothing.

## Docs

- [`PRD.md`](PRD.md) — product requirements and decision log (the *what* and *why*)
- [`planning/`](planning/) — implementation plans and status (the *how* and *in what order*)
