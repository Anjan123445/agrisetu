"""
OWNER: teammate A (disease diagnosis / image model).
STATUS: real implementation, replacing the fake-but-valid stub.

Contract (unchanged from the stub):
    async def diagnose(image_bytes: bytes, location: dict, language: str) -> dict

Required output keys (must match models.DiseaseDiagnosisResponse):
    {
      "disease_name": str,
      "confidence": float,       # 0.0 - 1.0
      "description": str,
      "remedy": str,             # in the requested `language`
      "prevention_tips": list[str],
    }

Uses gemini_client.generate_json_with_image() so this module calls Gemini
the same way every other module does (same model config, same JSON-mode
handling) rather than wiring up its own separate Gemini client.

NOTE on `location`: main.py currently calls this as
    disease.diagnose(image_bytes, {"raw": location}, language)
where `location` is the RAW JSON STRING from the multipart form field,
not a parsed dict — so `{"raw": location}` is `{"raw": "<json string>"}`,
not real lat/lng/district/state. This function defensively tries to
parse `location["raw"]` as JSON if present (falls back to no location
context if that fails), so it still works today, but the real fix is in
main.py: parse the location JSON string BEFORE calling diagnose(), so
this function gets an actual dict matching models.Location. Flagged
separately — not something this file can fully fix on its own since the bug
is in how main.py builds the argument.

Unlike a "fill in something plausible" fallback, this module does NOT
invent a disease diagnosis if Gemini fails — a wrong diagnosis could
cost a farmer their crop. On any failure it raises RuntimeError with a
clear message; main.py should let that propagate as a 502 (FastAPI's
default behavior for an unhandled exception in an async route is a 500,
which is also fine — see the integration note in the handoff message
for the one-line change to get a 502 instead, if preferred).
"""

from __future__ import annotations

import json
import logging
import re

from app.gemini_client import generate_json_with_image

logger = logging.getLogger("agrisetu.disease")

_LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ml": "Malayalam",
    "or": "Odia",
}

_SUPPORTED_MIME_TYPES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
}

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "disease_name": {"type": "string"},
        "confidence": {"type": "number"},
        "description": {"type": "string"},
        "remedy": {"type": "string"},
        "prevention_tips": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["disease_name", "confidence", "description", "remedy", "prevention_tips"],
}


def _guess_mime_type(image_bytes: bytes) -> str:
    for magic, mime in _SUPPORTED_MIME_TYPES.items():
        if image_bytes.startswith(magic):
            return mime
            
    # Guard: Flag unsupported formats (like HEIC) instead of silently failing
    # or blindly assuming JPEG. Browsers usually re-encode camera captures, 
    # but direct file uploads might not.
    logger.warning("Unsupported or unknown image magic bytes detected. Defaulting to image/jpeg, but this may fail.")
    return "image/jpeg"


def _language_name(language_code: str) -> str:
    return _LANGUAGE_NAMES.get((language_code or "en").lower(), language_code or "English")


def _location_context(location: dict) -> str:
    """
    Defensive parsing — see the module docstring note on the current
    main.py bug that passes {"raw": "<json string>"} instead of a real
    dict. Handles both the buggy shape and the correct
    {"lat":..., "lng":..., "state":..., "district":...} shape so this
    keeps working either way, and works even better once main.py is fixed.
    """
    if not location:
        return ""

    parsed = location
    if "raw" in location and isinstance(location["raw"], str):
        try:
            parsed = json.loads(location["raw"])
        except (json.JSONDecodeError, TypeError):
            return ""

    if not isinstance(parsed, dict):
        return ""

    bits = [str(parsed[k]) for k in ("district", "state") if parsed.get(k)]
    if not bits:
        return ""
    return f" The photo was taken in {', '.join(bits)}, India — consider diseases common to that region/season."


def _build_prompt(language: str, location: dict) -> str:
    lang_name = _language_name(language)
    loc_context = _location_context(location)

    return f"""You are an agricultural plant pathologist helping a farmer in India diagnose a possible crop disease from a photo of a leaf.{loc_context}

Look carefully at the leaf image and identify the most likely disease (or state clearly if the leaf appears healthy). Consider common fungal, bacterial, viral, and nutrient-deficiency issues found in Indian cropping systems.

Respond with ONLY a JSON object matching the required schema. Rules:
- "disease_name" and "description" must be in English.
- "remedy" and every item in "prevention_tips" MUST be written in {lang_name}, in plain language a farmer without formal agricultural training can understand.
- Prefer remedies that are low-cost and locally available in rural India (neem oil, common fungicides, cultural practices) over expensive/rare inputs, where appropriate.
- If the image is not a plant leaf at all, or is too unclear to assess, set "disease_name" to "Unable to determine" and explain why in "description", with confidence at or below 0.3.
- No markdown fences, no extra commentary — raw JSON only."""


def _extract_json(raw: dict | str) -> dict:
    """generate_json_with_image() already returns a parsed dict in the
    normal case (gemini_client.py parses response.text as JSON). This is
    a defensive extra layer only for the case where a raw string somehow
    reaches here — kept minimal since gemini_client.py owns JSON parsing."""
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    return json.loads(text)


def _validate_and_normalize(parsed: dict) -> dict:
    required_keys = {"disease_name", "confidence", "description", "remedy", "prevention_tips"}
    missing = required_keys - parsed.keys()
    if missing:
        raise RuntimeError(f"Gemini response missing required keys: {missing}. Got: {parsed}")

    disease_name = str(parsed["disease_name"]).strip()
    description = str(parsed["description"]).strip()
    remedy = str(parsed["remedy"]).strip()

    try:
        confidence = round(max(0.0, min(1.0, float(parsed["confidence"]))), 2)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"'confidence' is not numeric: {parsed['confidence']!r}") from exc

    prevention_tips = parsed["prevention_tips"]
    if isinstance(prevention_tips, str):
        prevention_tips = [prevention_tips]
    if not isinstance(prevention_tips, list) or not all(isinstance(t, str) for t in prevention_tips):
        raise RuntimeError(f"'prevention_tips' must be a list of strings, got: {prevention_tips!r}")
    prevention_tips = [t.strip() for t in prevention_tips if t.strip()]
    if not prevention_tips:
        raise RuntimeError("'prevention_tips' was empty after normalization")

    if not disease_name:
        raise RuntimeError("'disease_name' was empty")
    if not remedy:
        raise RuntimeError("'remedy' was empty")

    return {
        "disease_name": disease_name,
        "confidence": confidence,
        "description": description,
        "remedy": remedy,
        "prevention_tips": prevention_tips,
    }


async def diagnose(image_bytes: bytes, location: dict, language: str) -> dict:
    """
    Diagnose a likely crop disease from a leaf photo using Gemini.

    async def to match the contract main.py calls (`await disease.diagnose(...)`)
    — the actual Gemini call is synchronous under the hood (gemini_client.py
    doesn't offer an async path), which is fine for a hackathon's request
    volume; if this becomes a bottleneck under concurrent load, wrap the
    gemini_client call in `asyncio.to_thread(...)`.
    """
    if not image_bytes:
        raise ValueError("image_bytes must be non-empty")
    if len(image_bytes) < 100:
        raise ValueError("image_bytes is too small to be a real image")

    mime_type = _guess_mime_type(image_bytes)
    prompt = _build_prompt(language, location)

    try:
        raw = generate_json_with_image(prompt, image_bytes, mime_type, _RESPONSE_SCHEMA)
    except Exception as exc:  # noqa: BLE001 - surfaced as a clear RuntimeError, never faked
        logger.exception("Gemini disease diagnosis call failed")
        raise RuntimeError(f"Disease diagnosis failed: {exc}") from exc

    parsed = _extract_json(raw)
    result = _validate_and_normalize(parsed)

    logger.info(
        "Diagnosed disease=%r confidence=%.2f language=%s",
        result["disease_name"], result["confidence"], language,
    )
    return result