"""
Central config. All env vars read here, nowhere else, so the whole
team can see what's required in one place.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# --- Firebase ---
# Auth is via Application Default Credentials everywhere — no key file
# config needed. See app/firebase.py for details.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")

# --- CORS ---
# Comma-separated list of allowed origins, e.g.
# "http://localhost:5173,https://agrisetu-frontend.web.app"
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

# --- Misc ---
ENV = os.getenv("ENV", "development")
