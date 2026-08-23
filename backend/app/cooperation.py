"""
cooperation.py
Cross-state cooperation dashboard for AgriSetu - the feature that demonstrates
states seeing each other's aggregated, anonymized agricultural data.

Owns: GET /api/cooperation-dashboard
    get_cooperation_summary() -> dict
    Returns: {"state_summaries": [{"state", "top_crops", "avg_soil_health", "active_farmers"}, ...]}

Reads two Firestore collections the backend owner populates:
    - `advisories`      (one doc per served /api/advisory call)
    - `diseaseReports`  (one doc per served /api/disease-diagnosis call)

ASSUMPTIONS ABOUT FIRESTORE DOC SHAPE - CONFIRM THESE WITH THE BACKEND OWNER,
this is the single biggest integration risk in this file:

    advisories doc (expected to mirror the /api/advisory contract):
        location: { state, district, lat, lng }
        recommended_crops: [ { name, confidence, reason }, ... ]  # sorted, highest confidence first
        soil_summary: { moisture, ph_estimate, ndvi }
        soil_health_score: float (0-1)                # OPTIONAL, preferred if present
        farmer_id / farmerId / user_id / userId: str   # OPTIONAL, needed for accurate unique-farmer counts
        timestamp: server timestamp

    diseaseReports doc:
        location: { state, district, lat, lng }
        farmer_id / farmerId / user_id / userId: str   # OPTIONAL
        timestamp: server timestamp

Degradation behavior if those optional fields are missing (so the demo never
just crashes on stage):
    - No soil_health_score on a doc -> derived from soil_summary (NDVI + pH +
      moisture) via a simple heuristic. This is a demo-quality estimate, not
      agronomic ground truth - say so if judges ask.
    - No farmer id field anywhere in a state's docs -> active_farmers falls
      back to a raw document count for that state (over-counts repeat
      submissions). A warning is logged so this is visible during dev, and
      it's called out again in the README as a known limitation to fix with
      the backend owner before relying on the number in the demo.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # so GCP_PROJECT_ID is available even when this file is imported standalone

import logging
from collections import defaultdict, Counter

from google.cloud import firestore

logger = logging.getLogger(__name__)

_db = firestore.Client(project=os.environ.get("GCP_PROJECT_ID"))

FARMER_ID_FIELDS = ("farmer_id", "farmerId", "user_id", "userId")

# Categorical moisture -> numeric score, used only as a fallback when a doc
# doesn't already carry a soil_health_score.
MOISTURE_SCORE_MAP = {
    "low": 0.3, "dry": 0.3,
    "moderate": 0.6, "medium": 0.6,
    "high": 0.9, "adequate": 0.9, "wet": 0.9,
}

TOP_CROPS_PER_STATE = 3


def _get_farmer_id(doc_dict: dict):
    for field in FARMER_ID_FIELDS:
        if doc_dict.get(field):
            return doc_dict[field]
    return None


def _derive_soil_health_score(soil_summary: dict) -> float:
    """
    Fallback scorer for docs without a precomputed soil_health_score.
    Averages three 0-1 signals: NDVI (as-is), pH distance from ~6.5
    (roughly optimal for most crops), and a mapped moisture category.
    """
    scores = []

    ndvi = soil_summary.get("ndvi")
    if isinstance(ndvi, (int, float)):
        scores.append(max(0.0, min(1.0, ndvi)))

    ph = soil_summary.get("ph_estimate")
    if isinstance(ph, (int, float)):
        scores.append(max(0.0, 1.0 - abs(ph - 6.5) / 6.5))

    moisture = soil_summary.get("moisture")
    if isinstance(moisture, str):
        moisture_score = MOISTURE_SCORE_MAP.get(moisture.lower())
        if moisture_score is not None:
            scores.append(moisture_score)

    return sum(scores) / len(scores) if scores else 0.0


def get_cooperation_summary() -> dict:
    """
    Aggregates `advisories` and `diseaseReports` by state.

    Returns:
        {"state_summaries": [
            {"state": str, "top_crops": [str, ...], "avg_soil_health": float, "active_farmers": int},
            ...
        ]}
    """
    crop_counters = defaultdict(Counter)
    soil_scores = defaultdict(list)
    farmer_ids_by_state = defaultdict(set)
    doc_counts_by_state = defaultdict(int)  # fallback if no farmer id ever seen
    any_farmer_id_seen = False

    # --- advisories: crops, soil health, farmer ids ---
    for doc in _db.collection("advisories").stream():
        data = doc.to_dict() or {}
        state = (data.get("location") or {}).get("state")
        if not state:
            continue  # skip malformed docs rather than fail the whole dashboard

        doc_counts_by_state[state] += 1

        recommended_crops = data.get("recommended_crops") or []
        if recommended_crops and isinstance(recommended_crops, list):
            top_crop = recommended_crops[0].get("name")
            if top_crop:
                crop_counters[state][top_crop] += 1

        if isinstance(data.get("soil_health_score"), (int, float)):
            soil_scores[state].append(data["soil_health_score"])
        elif data.get("soil_summary"):
            soil_scores[state].append(_derive_soil_health_score(data["soil_summary"]))

        farmer_id = _get_farmer_id(data)
        if farmer_id:
            any_farmer_id_seen = True
            farmer_ids_by_state[state].add(farmer_id)

    # --- diseaseReports: farmer ids + doc counts only ---
    for doc in _db.collection("diseaseReports").stream():
        data = doc.to_dict() or {}
        state = (data.get("location") or {}).get("state")
        if not state:
            continue

        doc_counts_by_state[state] += 1

        farmer_id = _get_farmer_id(data)
        if farmer_id:
            any_farmer_id_seen = True
            farmer_ids_by_state[state].add(farmer_id)

    if not any_farmer_id_seen:
        logger.warning(
            "cooperation.py: no farmer_id/farmerId/user_id/userId field found on any "
            "advisories/diseaseReports doc. active_farmers is falling back to raw "
            "document counts, which over-counts repeat submissions. Add a stable "
            "farmer identifier to both collections before demo day if possible."
        )

    state_summaries = []
    for state in sorted(doc_counts_by_state.keys()):
        top_crops = [name for name, _ in crop_counters[state].most_common(TOP_CROPS_PER_STATE)]
        scores = soil_scores.get(state, [])
        avg_soil_health = round(sum(scores) / len(scores), 2) if scores else 0.0

        farmer_ids = farmer_ids_by_state.get(state)
        active_farmers = len(farmer_ids) if farmer_ids else doc_counts_by_state[state]

        state_summaries.append({
            "state": state,
            "top_crops": top_crops,
            "avg_soil_health": avg_soil_health,
            "active_farmers": active_farmers,
        })

    return {"state_summaries": state_summaries}