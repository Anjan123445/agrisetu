"""
Pydantic models for AgriSetu API contract.
This file is the single source of truth for request/response shapes.
DO NOT change field names/types without updating the frozen contract doc
and telling the whole team — the frontend is built against this shape.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared / location
# ---------------------------------------------------------------------------

class Location(BaseModel):
    lat: float
    lng: float
    state: str
    district: str


# ---------------------------------------------------------------------------
# POST /api/advisory
# ---------------------------------------------------------------------------

class AdvisoryRequest(BaseModel):
    location: Location
    language: str = Field(..., description="ISO-ish language code, e.g. 'kn', 'hi', 'en'")
    crop_history: List[str] = Field(default_factory=list)
    device_id: Optional[str] = None


class RecommendedCrop(BaseModel):
    name: str
    confidence: float
    reason: str


class SoilSummary(BaseModel):
    moisture: str
    ph_estimate: float
    ndvi: float


class WeatherSummary(BaseModel):
    forecast_7day: str
    temp_avg_c: float


class AdvisoryResponse(BaseModel):
    recommended_crops: List[RecommendedCrop]
    soil_summary: SoilSummary
    weather_summary: WeatherSummary
    advisory_text: str
    audio_url: str


# ---------------------------------------------------------------------------
# POST /api/disease-diagnosis  (multipart: image, location, language)
# ---------------------------------------------------------------------------

class DiseaseDiagnosisResponse(BaseModel):
    disease_name: str
    confidence: float
    description: str
    remedy: str
    prevention_tips: List[str]


# ---------------------------------------------------------------------------
# POST /api/voice-query  (multipart: audio, language)
# ---------------------------------------------------------------------------

class VoiceQueryResponse(BaseModel):
    transcript: str
    response_text: str
    response_audio_url: str


# ---------------------------------------------------------------------------
# GET /api/cooperation-dashboard
# ---------------------------------------------------------------------------

class StateSummary(BaseModel):
    state: str
    top_crops: List[str]
    avg_soil_health: float
    active_farmers: int


class CooperationDashboardResponse(BaseModel):
    state_summaries: List[StateSummary]
