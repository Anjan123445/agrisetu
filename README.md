# AgriSetu

Hackathon project — AI-assisted crop advisory, disease diagnosis,
voice query, and a farmer-cooperation dashboard for smallholder
farmers.

## Repo structure

```
/frontend        Person 1
/backend         Person 2 (owns main.py/advisory.py; imports Person 3 & 4's modules)
  /app/main.py         FastAPI app, CORS, route wiring
  /app/advisory.py     POST /api/advisory — fully built
  /app/soil_weather.py Person 3 (stub today, real Earth Engine/weather Day 2)
  /app/disease.py      Person 3 (stub today, real model Day 2)
  /app/voice.py        Person 4 (stub today, real STT/TTS Day 2)
  /app/cooperation.py  Person 4 (stub today, real aggregation Day 2)
/docs            Shared: pitch deck, README, demo script (Person 4 owns final assembly)
/mock-data       Shared: JSON fixtures matching the API contract (§4)
```

## API contract

Frozen — see `backend/app/models.py` for the enforced Pydantic shapes
and `mock-data/` for example JSON payloads per endpoint:

- `POST /api/advisory`
- `POST /api/disease-diagnosis`
- `POST /api/voice-query`
- `GET /api/cooperation-dashboard`

If the contract needs to change, update `backend/app/models.py` and
the matching file in `mock-data/` in the same PR.

## Getting started

- Backend: see `backend/README.md` for local dev, Firebase setup, and
  Cloud Run deploy.
- Frontend: see `frontend/README.md`.
- Fixtures for building UI before the backend is deployed: `mock-data/`.
