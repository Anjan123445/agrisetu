"""
Firebase Admin SDK setup + Firestore collection handles.

Collections (per team agreement):
  farmers           - one doc per farmer/device, profile + history
  advisories        - one doc per /api/advisory call (feeds dashboard)
  diseaseReports    - one doc per /api/disease-diagnosis call
  stateAggregates   - precomputed/rolling per-state summaries, read by
                       /api/cooperation-dashboard (cooperation.py owns writes)

Import `db` from this module anywhere you need Firestore. Don't call
firebase_admin.initialize_app() anywhere else — it can only run once
per process.
"""

"""
Firebase Admin SDK setup + Firestore collection handles.

Auth: Application Default Credentials (ADC) only — this org has
iam.disableServiceAccountKeyCreation enforced, so a downloadable
service account JSON key is never an option here, locally or in prod.

  Local dev:  run `gcloud auth application-default login` once
              (see README) — ADC picks up your user credentials from
              ~/.config/gcloud/application_default_credentials.json.
  Cloud Run:  ADC is provided automatically via the metadata server
              using the service's runtime service account. Grant that
              service account roles/datastore.user (deploy.sh prints
              the exact command).

Collections (per team agreement):
  farmers           - one doc per farmer/device, profile + history
  advisories        - one doc per /api/advisory call (feeds dashboard)
  diseaseReports    - one doc per /api/disease-diagnosis call
  stateAggregates   - precomputed/rolling per-state summaries, read by
                       /api/cooperation-dashboard (cooperation.py owns writes)

Import `db` from this module anywhere you need Firestore. Don't call
firebase_admin.initialize_app() anywhere else — it can only run once
per process.
"""

import logging

import firebase_admin
from firebase_admin import credentials, firestore

from app.config import FIREBASE_PROJECT_ID

logger = logging.getLogger("agrisetu.firebase")

_app = None
db = None


def init_firebase():
    """Idempotent Firebase init using ambient ADC. Call once at app startup."""
    global _app, db

    if firebase_admin._apps:
        _app = firebase_admin.get_app()
        db = firestore.client()
        return db

    try:
        # ApplicationDefault() resolves ADC from (in order): the
        # metadata server (Cloud Run), or the local gcloud ADC file
        # created by `gcloud auth application-default login`. No
        # certificate file is read in either case.
        cred = credentials.ApplicationDefault()
        _app = firebase_admin.initialize_app(
            cred, {"projectId": FIREBASE_PROJECT_ID} if FIREBASE_PROJECT_ID else None
        )
        db = firestore.client()
        logger.info("Firebase initialized via ADC (project=%s)", FIREBASE_PROJECT_ID or "default")
    except Exception:
        # Don't crash the whole API if ADC isn't set up yet — log loudly
        # so /api/advisory can still be tested without Firestore.
        # Writes will raise when actually attempted.
        logger.exception(
            "Firebase failed to initialize via ADC. Locally, run "
            "`gcloud auth application-default login`. On Cloud Run, "
            "check the runtime service account has roles/datastore.user."
        )
        db = None

    return db


# --- Collection name constants (use these, not raw strings, everywhere) ---
FARMERS_COLLECTION = "farmers"
ADVISORIES_COLLECTION = "advisories"
DISEASE_REPORTS_COLLECTION = "diseaseReports"
STATE_AGGREGATES_COLLECTION = "stateAggregates"


def get_db():
    """Fetch the Firestore client, initializing on first use if needed."""
    global db
    if db is None:
        init_firebase()
    return db
