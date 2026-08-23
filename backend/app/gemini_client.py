"""
Thin wrapper around the Gemini API so every module calls Gemini the
same way (model name, JSON-mode, error handling) instead of each
teammate wiring it up differently.
"""

import json
import logging

import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("agrisetu.gemini")

_configured = False


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


def generate_json(prompt: str, response_schema: dict | None = None) -> dict:
    """
    Call Gemini asking for strict JSON output matching response_schema
    (a JSON-schema-like dict, Gemini's structured output format), parse
    and return it as a dict. Raises on malformed output rather than
    silently returning something that doesn't match the contract.
    """
    _ensure_configured()

    model = genai.GenerativeModel(GEMINI_MODEL)

    generation_config = {"response_mime_type": "application/json"}
    if response_schema is not None:
        generation_config["response_schema"] = response_schema

    response = model.generate_content(prompt, generation_config=generation_config)

    text = response.text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error("Gemini returned non-JSON output: %s", text[:500])
        raise RuntimeError("Gemini response was not valid JSON")
