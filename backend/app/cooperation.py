"""
OWNER: teammate B (cooperation dashboard).
STATUS: stub — returns fake-but-valid state summaries so the frontend
dashboard can integrate today. Real implementation should read the
`stateAggregates` Firestore collection (or compute live from
`advisories`) and roll it up per state.

Contract:
    def get_state_summaries() -> list[dict]

Required shape per item (must match models.StateSummary):
    {
      "state": str,
      "top_crops": list[str],
      "avg_soil_health": float,   # 0.0 - 1.0
      "active_farmers": int,
    }

Suggested real implementation:
    - On each /api/advisory call, advisory.py already writes a doc to
      `advisories` with state + recommended_crops + soil_summary.
    - Either (a) query + aggregate `advisories` live here, or
      (b) run a scheduled job that rolls those up into
      `stateAggregates` (one doc per state) and just read that here
      for a fast dashboard load. (b) is better once farmer counts grow.
"""

from app.firebase import get_db, STATE_AGGREGATES_COLLECTION


def get_state_summaries() -> list[dict]:
    """
    STUB. Tries to read real data from `stateAggregates` if Firestore is
    configured and has data; otherwise falls back to fixed fake data so
    the endpoint always returns something valid during the hackathon.
    """
    db = get_db()
    if db is not None:
        try:
            docs = db.collection(STATE_AGGREGATES_COLLECTION).stream()
            summaries = [d.to_dict() for d in docs]
            if summaries:
                return summaries
        except Exception:
            pass  # fall through to stub data below

    return [
        {
            "state": "Karnataka",
            "top_crops": ["Groundnut", "Ragi"],
            "avg_soil_health": 0.6,
            "active_farmers": 128,
        },
        {
            "state": "Maharashtra",
            "top_crops": ["Cotton", "Soybean"],
            "avg_soil_health": 0.55,
            "active_farmers": 94,
        },
    ]
