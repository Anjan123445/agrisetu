"""
OWNER: teammate B (voice / speech).
STATUS: stub — wires /api/voice-query end-to-end with fake data.
Replace handle_voice_query() with a real STT call (e.g. Google
Speech-to-Text) -> Gemini text response -> TTS call (e.g. Google
Cloud Text-to-Speech), uploading the resulting audio somewhere
public (Firebase Storage / GCS) and returning its URL.

Contract:
    async def handle_voice_query(audio_bytes: bytes, language: str) -> dict

Required output keys (must match models.VoiceQueryResponse):
    {
      "transcript": str,
      "response_text": str,
      "response_audio_url": str,
    }
"""


async def handle_voice_query(audio_bytes: bytes, language: str) -> dict:
    """
    STUB. Ignores audio content, returns a plausible fixed response.
    """
    return {
        "transcript": "(stub transcript — STT not yet wired up)",
        "response_text": "(stub response — Gemini text answer not yet wired up, "
        "language=%s)" % language,
        "response_audio_url": "https://storage.googleapis.com/agrisetu-audio/stub_reply.mp3",
    }
