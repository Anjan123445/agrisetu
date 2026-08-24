"""
voice.py
Voice / Multilingual query handler for AgriSetu.

Owns: POST /api/voice-query
    handle_voice_query(audio_bytes: bytes, language: str) -> dict
    Returns: {"transcript": str, "response_text": str, "response_audio_url": str}
"""

from datetime import timedelta
import logging
import os
import uuid
from urllib.parse import quote

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, storage
from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate

from app.gemini_client import generate_text

load_dotenv()

logger = logging.getLogger(__name__)

FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET")

if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})

_speech_client = None
_tts_client = None
_translate_client = None

_SPEECH_ENCODING = speech.RecognitionConfig.AudioEncoding.WEBM_OPUS

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

STT_SUPPORTED = {"en", "hi", "kn", "mr", "ta", "te", "gu", "bn", "pa", "ml", "ur"}
PIVOT_LANGUAGE = "hi"


def _bcp47(language: str) -> str:
    return LANGUAGE_BCP47.get(language, "en-IN")


def _ensure_clients():
    global _speech_client, _tts_client, _translate_client
    if _speech_client is not None:
        return

    from app.firebase import init_firebase
    init_firebase()

    _speech_client = speech.SpeechClient()
    _tts_client = texttospeech.TextToSpeechClient()
    _translate_client = translate.Client()


def _transcribe(audio_bytes: bytes, language: str) -> str:
    _ensure_clients()
    stt_lang = language if language in STT_SUPPORTED else PIVOT_LANGUAGE
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=_SPEECH_ENCODING,
        language_code=_bcp47(stt_lang),
        sample_rate_hertz=48000,
        model="latest_long",
        enable_automatic_punctuation=True,
    )
    response = _speech_client.recognize(config=config, audio=audio)
    transcript = " ".join(
        r.alternatives[0].transcript for r in response.results if r.alternatives
    ).strip()
    if transcript and stt_lang != language:
        transcript = _translate_text(transcript, target_lang=language, source_lang=stt_lang)
    return transcript


def _translate_text(text: str, target_lang: str, source_lang: str = None) -> str:
    if source_lang == target_lang:
        return text
    _ensure_clients()
    result = _translate_client.translate(text, target_language=target_lang, source_language=source_lang)
    return result["translatedText"]


def _ask_gemini(transcript: str, language: str) -> str:
    prompt = (
        "You are AgriSetu, a helpful assistant for Indian farmers. "
        f"Answer this farmer's question helpfully and concisely, in {language} language. "
        "Keep it practical and easy to act on, and avoid jargon.\n\n"
        f"Farmer's question: {transcript}"
    )
    return generate_text(prompt)


def _synthesize_speech(text: str, language: str) -> bytes:
    _ensure_clients()
    input_text = texttospeech.SynthesisInput(text=text)
    voice_params = texttospeech.VoiceSelectionParams(
        language_code=_bcp47(language), ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = _tts_client.synthesize_speech(input=input_text, voice=voice_params, audio_config=audio_config)
    return response.audio_content


def _upload_audio(audio_content: bytes, language: str) -> str:
    _ensure_clients()
    if not FIREBASE_STORAGE_BUCKET:
        logger.warning("FIREBASE_STORAGE_BUCKET is not configured; skipping audio upload.")
        return ""

    bucket = storage.bucket()
    filename = f"voice-replies/{language}/{uuid.uuid4().hex}.mp3"
    blob = bucket.blob(filename)
    blob.upload_from_string(audio_content, content_type="audio/mpeg")

    try:
        # Service-account credentials can sign an expiring URL.
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET",
        )
    except AttributeError:
        # Local ADC user credentials cannot sign URLs. Firebase download tokens
        # provide a browser-readable URL without requiring a private key.
        download_token = uuid.uuid4().hex
        blob.metadata = {"firebaseStorageDownloadTokens": download_token}
        blob.patch()
        encoded_name = quote(filename, safe="")
        return (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
            f"{encoded_name}?alt=media&token={download_token}"
        )


def handle_voice_query(audio_bytes: bytes, language: str) -> dict:
    transcript = _transcribe(audio_bytes, language)

    if not transcript:
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