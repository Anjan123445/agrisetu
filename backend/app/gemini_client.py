"""
Thin wrapper around the Gemini API so every module calls Gemini the
same way (model name, JSON-mode, error handling) instead of each
teammate wiring it up differently.
"""

import json
import logging

from google import genai
from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("agrisetu.gemini")

_configured = False

_client = None


def _ensure_configured():
    global _configured
    if not _configured:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env or Cloud Run "
                "env vars — see .env.example."
            )
        genai.configure(api_key=GEMINI_API_KEY)
        _configured = True

def generate_text(prompt: str) -> str:
    client = _client_instance()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return (response.text or "").strip()


def _client_instance():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

def generate_json(prompt: str, response_schema: dict | None = None) -> dict:
    client = _client_instance()
    config = {"response_mime_type": "application/json"}
    if response_schema:
        config["response_schema"] = response_schema
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=config)
    return json.loads(response.text)

def generate_json_with_image(prompt, image_bytes, mime_type, response_schema=None) -> dict:
    client = _client_instance()
    config = {"response_mime_type": "application/json"}
    if response_schema:
        config["response_schema"] = response_schema
    part = genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    response = client.models.generate_content(model=GEMINI_MODEL, contents=[prompt, part], config=config)
    return json.loads(response.text)
