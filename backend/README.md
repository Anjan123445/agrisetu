# AgriSetu Backend

FastAPI backend for AgriSetu. Lives at `/backend` in the monorepo
(see repo root README for the full layout). Built against the frozen
API contract so the frontend and teammate modules can integrate
without waiting on each other.

## Structure

```
backend/
app/
  main.py          FastAPI app, CORS, route wiring, startup (Firebase init)
  advisory.py       POST /api/advisory — fully implemented (Gemini + Firestore)
  models.py         Pydantic request/response models = the frozen contract
  config.py         All env vars read here
  firebase.py       Firebase Admin SDK init + Firestore collection handles
  gemini_client.py  Shared Gemini API wrapper (JSON-mode)
  soil_weather.py   STUB — teammate A: Earth Engine + weather -> get_signals()
  disease.py        STUB — teammate A: disease diagnosis -> diagnose()
  voice.py          STUB — teammate B: STT/TTS -> handle_voice_query()
  cooperation.py    STUB — teammate B: dashboard aggregation -> get_state_summaries()
requirements.txt
Dockerfile
deploy.sh           Cloud Run deploy script
.env.example
```

## Local setup

Run these from inside `backend/`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GEMINI_API_KEY at minimum
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080/docs for interactive API docs.

Without `FIREBASE_CREDENTIALS_PATH` set, Firestore writes are skipped
(logged as a warning) rather than crashing the app — so you can test
`/api/advisory` with just a `GEMINI_API_KEY` before Firebase is fully
set up.

## Firebase setup

1. In the Firebase console, create/select the project, enable
   Firestore (production mode is fine).
2. Local dev: Project Settings -> Service Accounts -> Generate new
   private key. Save it as `firebase-service-account.json` in the repo
   root (already gitignored) and point `FIREBASE_CREDENTIALS_PATH` at it.
3. Cloud Run: skip the key file. Instead grant the Cloud Run runtime
   service account `roles/datastore.user` (the `deploy.sh` output
   prints the exact command) — it'll use Application Default
   Credentials automatically.

Collections used: `farmers`, `advisories`, `diseaseReports`,
`stateAggregates` (see `app/firebase.py` for details on who writes
what).

## Deploying to Cloud Run

From inside `backend/` (the script also `cd`s here itself if you run
it from elsewhere):

```bash
GEMINI_API_KEY=xxxx ./deploy.sh
```

Override `PROJECT_ID`, `REGION`, or `SERVICE_NAME` as env vars if the
defaults (`agrisetu-hackathon`, `asia-south1`, `agrisetu-backend`)
don't match your setup.

## Day 2 handoff

Each stub file has a docstring at the top spelling out the exact
function signature and required return shape. When a teammate hands
off their real module, drop it in place of the stub with the same
filename and function name — nothing in `main.py` or `advisory.py`
needs to change.

| File | Function | Owner |
|---|---|---|
| `soil_weather.py` | `get_signals(location: dict) -> dict` | Teammate A |
| `disease.py` | `async diagnose(image_bytes, location, language) -> dict` | Teammate A |
| `voice.py` | `async handle_voice_query(audio_bytes, language) -> dict` | Teammate B |
| `cooperation.py` | `get_state_summaries() -> list[dict]` | Teammate B |

## Endpoints

- `POST /api/advisory` — fully implemented (soil/weather signals ->
  Gemini reasoning -> Firestore write -> response).
- `POST /api/disease-diagnosis` — wired to a stub, ready for the real
  model to drop in.
- `POST /api/voice-query` — wired to a stub.
- `GET /api/cooperation-dashboard` — wired to a stub (tries real
  Firestore data first, falls back to fixed sample data).
