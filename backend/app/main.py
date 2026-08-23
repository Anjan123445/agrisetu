"""
AgriSetu backend entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8080

Route ownership:
    POST /api/advisory              -> app/advisory.py            (fully built)
    POST /api/disease-diagnosis     -> app/disease.py stub          (Day 2: teammate A)
    POST /api/voice-query           -> app/voice.py stub            (Day 2: teammate B)
    GET  /api/cooperation-dashboard -> app/cooperation.py stub      (Day 2: teammate B)

When teammates hand off their modules on Day 2, drop the real
soil_weather.py / disease.py / voice.py / cooperation.py in place —
the function signatures are already the contract, so nothing else in
this file needs to change.
"""

import logging

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, ENV
from app.firebase import init_firebase, get_db, DISEASE_REPORTS_COLLECTION
from app.advisory import router as advisory_router
#from app.test_connection import router as test_connection_router
from app import disease, voice, cooperation
from app.models import (
    DiseaseDiagnosisResponse,
    VoiceQueryResponse,
    CooperationDashboardResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agrisetu.main")

app = FastAPI(title="AgriSetu API", version="0.1.0")

# --- CORS: frontend is a different origin ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Advisory router (fully implemented) ---
app.include_router(advisory_router)

# --- Temporary ADC/Firestore connectivity check — safe to leave in ---
#app.include_router(test_connection_router)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting AgriSetu API (env=%s)", ENV)
    init_firebase()


@app.get("/")
async def root():
    return {"service": "agrisetu-api", "status": "ok", "env": ENV}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /api/disease-diagnosis  (multipart: image, location, language)
# STUB until teammate A's real model lands — wired end-to-end so the
# frontend can integrate today.
# ---------------------------------------------------------------------------

@app.post("/api/disease-diagnosis", response_model=DiseaseDiagnosisResponse)
async def post_disease_diagnosis(
    image: UploadFile = File(...),
    location: str = Form(...),
    language: str = Form(...),
):
    image_bytes = await image.read()
    result = await disease.diagnose(image_bytes, {"raw": location}, language)

    db = get_db()
    if db is not None:
        try:
            db.collection(DISEASE_REPORTS_COLLECTION).add(
                {
                    "location": location,
                    "language": language,
                    **result,
                }
            )
        except Exception:
            logger.exception("Failed to write disease report to Firestore")

    return DiseaseDiagnosisResponse(**result)


# ---------------------------------------------------------------------------
# POST /api/voice-query  (multipart: audio, language)
# STUB until teammate B's real STT/TTS lands.
# ---------------------------------------------------------------------------

@app.post("/api/voice-query", response_model=VoiceQueryResponse)
async def post_voice_query(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    audio_bytes = await audio.read()
    result = await voice.handle_voice_query(audio_bytes, language)
    return VoiceQueryResponse(**result)


# ---------------------------------------------------------------------------
# GET /api/cooperation-dashboard
# STUB until teammate B wires real aggregation.
# ---------------------------------------------------------------------------

@app.get("/api/cooperation-dashboard", response_model=CooperationDashboardResponse)
async def get_cooperation_dashboard():
    summaries = cooperation.get_state_summaries()
    return CooperationDashboardResponse(state_summaries=summaries)
