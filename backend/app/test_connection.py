"""
Standalone Firestore connectivity check. Not part of the API contract —
this exists purely so you can confirm ADC + Firestore access works
before relying on it inside advisory.py etc.
"""

import datetime
import logging

from fastapi import APIRouter, HTTPException

from app.firebase import get_db

logger = logging.getLogger("agrisetu.test_connection")

router = APIRouter()


@router.post("/api/test-connection")
async def test_connection():
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="Firestore client is None — ADC likely isn't set up. "
            "Run `gcloud auth application-default login` and restart the server.",
        )

    try:
        doc_ref = db.collection("test_connections").document()
        doc_ref.set(
            {
                "message": "hello from local machine via ADC",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
        )
        return {"status": "ok", "doc_id": doc_ref.id}
    except Exception as e:
        logger.exception("Firestore write failed")
        raise HTTPException(status_code=500, detail=f"Firestore write failed: {e}")