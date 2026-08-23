"""
voice.py
Voice / Multilingual query handler for AgriSetu.

Owns: POST /api/voice-query
    handle_voice_query(audio_bytes: bytes, language: str) -> dict
    Returns: {"transcript": str, "response_text": str, "response_audio_url": str}

Pipeline:
    1. Cloud Speech-to-Text  : audio_bytes -> transcript (in `language`, or bridged - see below)
    2. Gemini API            : transcript -> farming-advice answer (in `language`)
    3. Cloud Text-to-Speech  : answer -> speech audio (in `language`)
    4. Firebase Storage      : upload audio -> public URL

KNOWN LIMITATION (also documented in README):
    Cloud Speech-to-Text's accuracy/coverage varies a lot by Indian language.
    For languages outside STT_SUPPORTED below, we transcribe in a pivot
    language (Hindi) instead and use the Cloud Translation API to translate
    the transcript into the farmer's requested language, and the Gemini
    answer is generated directly in the target language regardless. This
    keeps every response in the language the farmer expects, at the cost of
    an extra translation hop (and its error) for unsupported languages.
    This is a deliberate "note, don't block" tradeoff for hackathon scope.

ASSUMPTION FLAGGED FOR TEAMMATE INTEGRATION:
    Audio encoding is assumed to be WebM/Opus, the default output of the
    browser MediaRecorder API on Chrome/most mobile browsers. If the
    frontend records audio differently (e.g. WAV/LINEAR16), update
    `_SPEECH_ENCODING` / `sample_rate_hertz` below to match - confirm with
    whoever owns the recording UI.
"""



import os
from dotenv import load_dotenv
load_dotenv()  # so GCP_PROJECT_ID is available even when this file is imported standalone
from urllib import response
import uuid
import logging

from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
import firebase_admin
from firebase_admin import credentials, storage
from google import genai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config / client init
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")  # e.g. "agrisetu-xxxx.appspot.com"

_genai_client = genai.Client(api_key=GEMINI_API_KEY)
# Confirm the exact model id available in your Google AI Studio / Vertex AI
# console at build time - model names/versions change frequently.
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Idempotent guard so importing this module twice (e.g. hot reload) doesn't
# crash on "app already exists".
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()  # swap for credentials.Certificate(path) if using a service account json
    firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})

_speech_client = speech.SpeechClient()
_tts_client = texttospeech.TextToSpeechClient()
_translate_client = translate.Client()

# Assumed input audio container - see module docstring.
_SPEECH_ENCODING = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS

# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

# App's short language codes -> BCP-47 codes Cloud Speech/TTS expect.
# Extend as more Indian languages are added to the frontend language picker.
LANGUAGE_BCP47 = {
    "en": "en-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "gu": "gu-IN",
    "bn": "bn-IN",
    "pa": "pa-IN",
    "ml": "ml-IN",
    "or": "or-IN",
    "as": "as-IN",
    "ur": "ur-IN",
}

# Languages we've confirmed have solid Cloud STT coverage for `latest_long`.
# Anything outside this set is bridged through PIVOT_LANGUAGE - see docstring.
STT_SUPPORTED = {"en", "hi", "kn", "mr", "ta", "te", "gu", "bn", "pa", "ml", "ur"}

PIVOT_LANGUAGE = "hi"  # broad national reach, reliably well-supported by STT


def _bcp47(language: str) -> str:
    return LANGUAGE_BCP47.get(language, "en-IN")


# ---------------------------------------------------------------------------
# Step 1: Speech-to-Text (+ translation bridge for uncovered languages)
# ---------------------------------------------------------------------------

def _transcribe(audio_bytes: bytes, language: str) -> str:
    stt_lang = language if language in STT_SUPPORTED else PIVOT_LANGUAGE

    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=_SPEECH_ENCODING,
        language_code=_bcp47(stt_lang),
        model="latest_long",
        enable_automatic_punctuation=True,
    )

    response = _speech_client.recognize(config=config, audio=audio)
    transcript = " ".join(
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    ).strip()

    if transcript and stt_lang != language:
        transcript = _translate_text(transcript, target_lang=language, source_lang=stt_lang)

    return transcript


def _translate_text(text: str, target_lang: str, source_lang: str = None) -> str:
    result = _translate_client.translate(text, target_language=target_lang, source_language=source_lang)
    return result["translatedText"]


# ---------------------------------------------------------------------------
# Step 2: Gemini - general farming Q&A
# ---------------------------------------------------------------------------

def _ask_gemini(transcript: str, language: str) -> str:
    """
    Deliberately broad prompt: this is the catch-all voice assistant, not the
    structured /api/advisory or /api/disease-diagnosis flows. Keep it general.
    """
    prompt = (
        "You are AgriSetu, a helpful assistant for Indian farmers. "
        f"Answer this farmer's question helpfully and concisely, in {language} language. "
        "Keep it practical and easy to act on, and avoid jargon.\n\n"
        f"Farmer's question: {transcript}"
    )
    response = _genai_client.models.generate_content(
    model=GEMINI_MODEL_NAME,
    contents=prompt,
    )
    return (response.text or "").strip()


# ---------------------------------------------------------------------------
# Step 3: Text-to-Speech
# ---------------------------------------------------------------------------

def _synthesize_speech(text: str, language: str) -> bytes:
    input_text = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=_bcp47(language),
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = _tts_client.synthesize_speech(input=input_text, voice=voice_params, audio_config=audio_config)
    return response.audio_content


# ---------------------------------------------------------------------------
# Step 4: Upload to Firebase Storage
# ---------------------------------------------------------------------------

def _upload_audio(audio_content: bytes, language: str) -> str:
    bucket = storage.bucket()
    filename = f"voice-replies/{language}/{uuid.uuid4().hex}.mp3"
    blob = bucket.blob(filename)
    blob.upload_from_string(audio_content, content_type="audio/mpeg")
    blob.make_public()  # hackathon-simple; swap for signed URLs before any real deployment
    return blob.public_url


# ---------------------------------------------------------------------------
# Public entry point - matches POST /api/voice-query contract
# ---------------------------------------------------------------------------

def handle_voice_query(audio_bytes: bytes, language: str) -> dict:
    """
    Args:
        audio_bytes: raw bytes from the multipart `audio` field.
        language: short language code, e.g. "kn", "hi", "en".

    Returns:
        {"transcript": str, "response_text": str, "response_audio_url": str}

    Raises:
        Exceptions from the underlying Google Cloud / Gemini / Firebase
        clients are allowed to propagate - the FastAPI layer (backend
        owner's app.py) should catch and map these to a 502/500 response.
        Not swallowing errors here so failures are visible during demo prep.
    """
    transcript = _transcribe(audio_bytes, language)

    if not transcript:
        # Contract still needs a valid shape even if STT heard nothing.
        fallback_text = _translate_text(
            "Sorry, I couldn't hear that clearly. Could you try again?",
            target_lang=language, source_lang="en",
        )
        audio_content = _synthesize_speech(fallback_text, language)
        return {
            "transcript": "",
            "response_text": fallback_text,
            "response_audio_url": _upload_audio(audio_content, language),
        }

    response_text = _ask_gemini(transcript, language)
    audio_content = _synthesize_speech(response_text, language)

    return {
        "transcript": transcript,
        "response_text": response_text,
        "response_audio_url": _upload_audio(audio_content, language),
    }