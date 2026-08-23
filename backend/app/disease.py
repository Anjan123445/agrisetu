"""
OWNER: teammate A (disease diagnosis / image model).
STATUS: stub — wires the /api/disease-diagnosis endpoint end-to-end
with a fake-but-valid response so the frontend can integrate today.
Replace diagnose() with a real call (e.g. Gemini vision, or a
fine-tuned classifier) that inspects the image bytes.

Contract:
    async def diagnose(image_bytes: bytes, location: dict, language: str) -> dict

Required output keys (must match models.DiseaseDiagnosisResponse):
    {
      "disease_name": str,
      "confidence": float,       # 0.0 - 1.0
      "description": str,
      "remedy": str,             # in the requested `language`
      "prevention_tips": list[str],
    }
"""


async def diagnose(image_bytes: bytes, location: dict, language: str) -> dict:
    """
    STUB. Ignores image content, returns a plausible fixed response.
    Real implementation should send `image_bytes` to a vision model
    (Gemini multimodal is a reasonable first pass) with a prompt asking
    for the same structured shape, then translate/localize to `language`.
    """
    return {
        "disease_name": "Leaf Blight",
        "confidence": 0.77,
        "description": "Fungal infection causing brown lesions on leaves, "
        "spreading in humid conditions.",
        "remedy": "Apply a copper-based fungicide and remove affected leaves. "
        "(stub response — not yet localized to '%s')" % language,
        "prevention_tips": [
            "Avoid overhead irrigation late in the day",
            "Ensure adequate spacing between plants for airflow",
        ],
    }
