"""
OWNER: you (backend owner).
STATUS: fully implemented against the frozen contract.

Flow for POST /api/advisory:
  1. Validate request (models.AdvisoryRequest).
  2. soil_weather.get_signals(location) -> raw signals (stubbed for now,
     real Earth Engine/weather call comes from teammate A on Day 2).
  3. Build a Gemini prompt from signals + location + crop_history, ask
     for recommended_crops + a localized advisory_text as strict JSON.
  4. Assemble the final response in the exact contract shape.
  5. Write the advisory to Firestore `advisories` (feeds the
     cooperation dashboard).
  6. Return the response.

soil_summary / weather_summary are built directly from
soil_weather.get_signals() (not from Gemini) so those numbers stay
deterministic and don't drift due to model hallucination. Gemini is
only used for the parts that need reasoning + language localization:
recommended_crops and advisory_text.
"""

import datetime
import logging

from fastapi import APIRouter, HTTPException

from app import soil_weather
from app.gemini_client import generate_json
from app.firebase import get_db, ADVISORIES_COLLECTION
from app.models import (
    AdvisoryRequest,
    AdvisoryResponse,
    RecommendedCrop,
    SoilSummary,
    WeatherSummary,
)

logger = logging.getLogger("agrisetu.advisory")

router = APIRouter()


# JSON schema Gemini must fill in. Kept intentionally narrow — only the
# fields that require reasoning/localization, not the raw sensor numbers.
_GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_crops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "confidence": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["name", "confidence", "reason"],
            },
        },
        "advisory_text": {"type": "string"},
    },
    "required": ["recommended_crops", "advisory_text"],
}


def _build_prompt(request: AdvisoryRequest, signals: dict) -> str:
    crop_history_str = ", ".join(request.crop_history) if request.crop_history else "none reported"

    return f"""You are an agricultural advisor helping smallholder farmers in India.

Farm location: {request.location.district}, {request.location.state} \
(lat {request.location.lat}, lng {request.location.lng})
Farmer's recent crop history: {crop_history_str}

Current field signals:
- Soil moisture: {signals['soil_moisture']}
- Estimated soil pH: {signals['soil_ph_estimate']}
- NDVI (vegetation health index, 0-1): {signals['ndvi']}
- 7-day weather forecast: {signals['forecast_7day']}
- Average temperature (7-day): {signals['temp_avg_c']} C
- Expected rainfall (7-day): {signals['rainfall_mm_7day']} mm

Task:
1. Recommend 2-3 suitable crops for this field for the upcoming season,
   considering the soil/weather signals and crop history (e.g. avoid
   recommending the same crop repeatedly if that risks soil exhaustion,
   favor rotation where sensible). For each crop give a confidence score
   between 0 and 1 and a short reason grounded in the specific signals above.
2. Write a short, practical, farmer-friendly advisory (4-6 sentences)
   in the language with code "{request.language}" (use natural, native
   phrasing for that language, not a literal translation of English
   agricultural jargon). Cover: what the current conditions mean for
   the farmer, and one or two concrete actions to take this week.

Respond ONLY with JSON matching the required schema. No extra commentary.
"""


def _stub_audio_url(language: str) -> str:
    """
    TODO(voice/audio owner): replace with a real TTS call (e.g. Google
    Cloud Text-to-Speech) on `advisory_text`, upload the resulting file
    to Firebase Storage / GCS, and return its public URL. For now this
    returns a deterministic placeholder so the frontend can build
    against a real-looking URL shape.
    """
    return f"https://storage.googleapis.com/agrisetu-audio/advisory_{language}.mp3"


def _write_advisory_to_firestore(request: AdvisoryRequest, response: AdvisoryResponse) -> None:
    db = get_db()
    if db is None:
        logger.warning("Firestore not configured — skipping advisory write.")
        return

    try:
        db.collection(ADVISORIES_COLLECTION).add(
            {
                "location": request.location.model_dump(),
                "language": request.language,
                "crop_history": request.crop_history,
                "recommended_crops": [c.model_dump() for c in response.recommended_crops],
                "soil_summary": response.soil_summary.model_dump(),
                "weather_summary": response.weather_summary.model_dump(),
                "advisory_text": response.advisory_text,
                "audio_url": response.audio_url,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
        )
    except Exception:
        # Never let a Firestore hiccup break the advisory response itself —
        # log and move on. The farmer still gets their advisory.
        logger.exception("Failed to write advisory to Firestore")


async def build_advisory(request: AdvisoryRequest) -> AdvisoryResponse:
    # 1. Signals (stubbed today, real Earth Engine/weather Day 2)
    signals = soil_weather.get_signals(request.location.model_dump())

    # 2. Gemini: crop recommendations + localized advisory text
    prompt = _build_prompt(request, signals)
    try:
        gemini_out = generate_json(prompt, _GEMINI_RESPONSE_SCHEMA)
    except Exception as e:
        logger.exception("Gemini call failed")
        raise HTTPException(status_code=502, detail=f"Advisory generation failed: {e}")

    try:
        recommended_crops = [RecommendedCrop(**c) for c in gemini_out["recommended_crops"]]
        advisory_text = gemini_out["advisory_text"]
    except (KeyError, TypeError) as e:
        logger.error("Gemini output missing expected fields: %s", gemini_out)
        raise HTTPException(status_code=502, detail=f"Advisory generation returned an unexpected shape: {e}")

    # 3. Deterministic fields straight from signals (no Gemini involved)
    soil_summary = SoilSummary(
        moisture=signals["soil_moisture"],
        ph_estimate=signals["soil_ph_estimate"],
        ndvi=signals["ndvi"],
    )
    weather_summary = WeatherSummary(
        forecast_7day=signals["forecast_7day"],
        temp_avg_c=signals["temp_avg_c"],
    )

    response = AdvisoryResponse(
        recommended_crops=recommended_crops,
        soil_summary=soil_summary,
        weather_summary=weather_summary,
        advisory_text=advisory_text,
        audio_url=_stub_audio_url(request.language),
    )

    # 4. Firestore write (feeds cooperation dashboard) — best-effort
    _write_advisory_to_firestore(request, response)

    return response


@router.post("/api/advisory", response_model=AdvisoryResponse)
async def post_advisory(request: AdvisoryRequest):
    return await build_advisory(request)
