
React + Vite + Tailwind. Mobile-first, built against mocked API responses so it runs standalone before the backend is live.

## Run

```bash
npm install
npm run dev
```

Optional — enables the Google Maps location picker (falls back to a state/district dropdown automatically if unset):

```bash
cp .env.example .env
# add VITE_GOOGLE_MAPS_API_KEY=...
```

## Structure

```
src/
  api/api.js            — single API client. USE_MOCKS flag switches between
                           local JSON fixtures and a real backend.
  context/AppContext.jsx — language + location, shared across screens
  i18n/strings.js        — en / hi / kn translation strings
  i18n/statesDistricts.js — fallback dropdown data for LocationPicker
  components/            — Layout, BottomNav, LanguageSwitcher, FurrowDivider
  pages/
    Landing.jsx
    LocationPicker.jsx
    AdvisoryDashboard.jsx
    DiseaseDiagnosis.jsx
    VoiceQuery.jsx
    CooperationDashboard.jsx
mock-data/*.json          — source fixtures (mirrored into public/mock-data
                             so they're fetchable at runtime like a real API)
```

## Switching to the real backend

Open `src/api/api.js` and change two lines:

```js
export const USE_MOCKS = false;
export const BASE_URL = "https://your-backend-url";
```

Every screen calls through this file, so no other code changes are needed. The mocked
responses in `mock-data/*.json` match the frozen API contract exactly, so once the
real endpoints return the same shape, the UI needs no further changes.

## Notes

- Voice recording uses `MediaRecorder` (Web Audio API) and sends a `webm` blob.
- Disease diagnosis accepts a photo via `<input type="file" capture="environment">`,
  which opens the camera directly on mobile.
- Deploy target: Firebase Hosting or Vercel — this is a static Vite build (`npm run build` → `dist/`).
