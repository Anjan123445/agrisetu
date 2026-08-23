# mock-data

Shared JSON fixtures matching the frozen API contract (§4). Use these
to build/demo the frontend against realistic shapes before the real
backend endpoint is deployed, or as a fallback if the live backend is
flaky during the demo.

| File | Matches |
|---|---|
| `advisory.json` | `POST /api/advisory` |
| `disease_diagnosis.json` | `POST /api/disease-diagnosis` |
| `voice_query.json` | `POST /api/voice-query` |
| `cooperation_dashboard.json` | `GET /api/cooperation-dashboard` |

Each file has a `response` key with the exact shape the real endpoint
returns. The two multipart endpoints (`disease_diagnosis.json`,
`voice_query.json`) also include a `request_example_fields` key
showing the non-file form fields, since the file part (image/audio)
can't be represented in JSON.

If the contract shape changes, update both this folder and
`backend/app/models.py` in the same PR — they must never drift apart.
