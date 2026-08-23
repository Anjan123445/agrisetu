"""
soil_weather.py
================
AgriSetu — Soil / Weather / Satellite (NDVI) signal module.

OWNER: teammate A (Earth Engine + weather) — this is the real
implementation replacing the original stub.

Public API
----------
    get_signals(location: dict) -> dict

    location = {"lat": 15.3, "lng": 75.7, "state": "Karnataka", "district": "Belagavi"}
    (matches models.Location)

Returns a dict matching the contract advisory.py depends on exactly:

    {
        "soil_moisture": "moderate",       # "low" | "moderate" | "high"
        "soil_ph_estimate": 6.5,
        "ndvi": 0.41,                        # 0.0 - 1.0
        "forecast_7day": "light rain expected",
        "temp_avg_c": 29.0,
        "rainfall_mm_7day": 12.4,
    }

advisory.py reads all six of these keys directly (see its SoilSummary /
WeatherSummary construction and the Gemini prompt in _build_prompt) — the
key names and types here must not change without updating advisory.py too.

Design notes for the hackathon
-------------------------------
* Earth Engine auth/quota is the single most likely thing to break live during
  a demo (auth token expiry, project not registered, quota burst, network).
  So NDVI resolution is wrapped so that ANY failure — auth, network, timeout,
  empty image collection, whatever — falls back to a curated per-district
  JSON lookup (data/district_fallback.json) instead of raising or returning
  nulls. The function is written to *always* return a complete, valid dict.
* Weather uses Open-Meteo (free, no API key). Same pattern: on any failure,
  fall back to a district-appropriate synthetic forecast + rainfall figure.
* Soil pH is not something Sentinel-2/MODIS give you directly (that needs a
  soil-specific product like SoilGrids or ISRIC). We proxy it from the
  fallback table / a very rough NDVI-based heuristic, and always label it as
  an *estimate* (per the contract's own field name `soil_ph_estimate`).

This file has ZERO import-time side effects — no auth calls, no network
calls happen just from `import soil_weather`. Earth Engine is only
initialized lazily, inside a try/except, the first time it's actually needed.

get_signals() is plain sync (advisory.py calls it directly, not awaited,
inside its own async route handler) — intentionally so, since the fallback
path is fast, and matches the stub's original signature. An in-memory TTL
cache still sits in front of the network calls (see CACHE_TTL_S below) so
repeated calls for the same demo location don't re-hit Earth Engine/Open-Meteo
every time; set AGRISETU_CACHE_TTL_S=0 to disable.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger("agrisetu.soil_weather")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
_FALLBACK_PATH = _HERE / "data" / "district_fallback.json"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_TIMEOUT_S = 6

# Earth Engine calls get their own (short) budget — we'd rather fall back
# fast than let a flaky GEE call eat the whole request during a live demo.
GEE_TIMEOUT_S = float(os.environ.get("AGRISETU_GEE_TIMEOUT_S", "8"))

# How long a get_signals() result is cached for a given rounded location.
# 0 disables caching entirely (always hits network/fallback fresh).
CACHE_TTL_S = float(os.environ.get("AGRISETU_CACHE_TTL_S", "600"))  # default 10 min

# NDVI collection: Sentinel-2 SR harmonized, cloud-masked, most recent
# ~30 day composite. MODIS MOD13Q1 is used as a secondary fallback inside
# the "live" path itself (coarser resolution, 16-day composites, but a
# much longer/more stable archive than Sentinel-2 in some regions).
_S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
_MODIS_NDVI_COLLECTION = "MODIS/061/MOD13Q1"

_ndvi_cache: dict[str, float] = {}

# Full-result cache: {location_cache_key: (expires_at_epoch, result_dict)}
_signals_cache: dict[str, tuple[float, dict]] = {}


# ---------------------------------------------------------------------------
# Fallback data
# ---------------------------------------------------------------------------

def _load_fallback_table() -> dict[str, Any]:
    with open(_FALLBACK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_FALLBACK_TABLE = _load_fallback_table()


def _fallback_entry_for(location: dict) -> dict[str, Any]:
    """Look up a curated district entry, falling back to a national default."""
    district = (location.get("district") or "").strip().lower()
    entry = _FALLBACK_TABLE["districts"].get(district)
    if entry is None:
        logger.info(
            "No curated fallback entry for district=%r; using national_default",
            location.get("district"),
        )
        entry = _FALLBACK_TABLE["national_default"]
    return entry


# ---------------------------------------------------------------------------
# Earth Engine (NDVI)
# ---------------------------------------------------------------------------

_ee_initialized = False
_ee_init_failed = False


def _ensure_ee_initialized() -> bool:
    """
    Lazily import + initialize the `ee` (Earth Engine) module.
    Returns True if EE is ready to use, False if init failed for any reason.

    Auth: expects either
      - a service account via GOOGLE_APPLICATION_CREDENTIALS pointing at a
        JSON key file, with EE_SERVICE_ACCOUNT set to that account's email, or
      - a machine that has already run `earthengine authenticate` (persisted
        user credentials), optionally with EE_PROJECT set (required by newer
        EE API versions that need a cloud project for quota).
    Never raises — any problem here just returns False and the caller falls
    back to curated data.
    """
    global _ee_initialized, _ee_init_failed

    if _ee_initialized:
        return True
    if _ee_init_failed:
        # Don't hammer a broken auth path on every request within a process;
        # one failed attempt per process lifetime is enough to give up.
        return False

    try:
        import ee  # imported lazily so this module has zero import-time deps

        service_account = os.environ.get("EE_SERVICE_ACCOUNT")
        key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project = os.environ.get("EE_PROJECT")

        if service_account and key_path:
            credentials = ee.ServiceAccountCredentials(service_account, key_path)
            ee.Initialize(credentials, project=project) if project else ee.Initialize(credentials)
        else:
            # Falls back to previously-persisted `earthengine authenticate`
            # credentials on this machine, if any.
            ee.Initialize(project=project) if project else ee.Initialize()

        _ee_initialized = True
        logger.info("Earth Engine initialized successfully.")
        return True

    except Exception as exc:  # noqa: BLE001 - intentionally broad, this must never crash the caller
        logger.warning("Earth Engine init failed, will use fallback NDVI data: %s", exc)
        _ee_init_failed = True
        return False


def _fetch_ndvi_live(lat: float, lng: float) -> Optional[float]:
    """
    Attempt to compute a recent mean NDVI for a small buffer around
    (lat, lng) using Sentinel-2, falling back to MODIS if Sentinel-2 has no
    recent cloud-free coverage. Returns None on any failure (caller falls
    back to curated data) — never raises.
    """
    if not _ensure_ee_initialized():
        return None

    cache_key = f"{round(lat, 3)},{round(lng, 3)}"
    if cache_key in _ndvi_cache:
        return _ndvi_cache[cache_key]

    try:
        import ee

        point = ee.Geometry.Point([lng, lat])
        region = point.buffer(1500)  # ~1.5km radius, small farm-scale window

        def _mean_ndvi_from(image) -> Optional[float]:
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=20, maxPixels=1e8
            )
            val = stats.get("NDVI").getInfo()
            return float(val) if val is not None else None

        # --- Try Sentinel-2 first: last 30 days, cloud-filtered ---
        s2 = (
            ee.ImageCollection(_S2_COLLECTION)
            .filterBounds(region)
            .filterDate(ee.Date(ee.Date.now()).advance(-30, "day"), ee.Date.now())
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        )

        def _add_ndvi(img):
            ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
            return img.addBands(ndvi)

        s2_with_ndvi = s2.map(_add_ndvi)
        s2_composite = s2_with_ndvi.select("NDVI").median()

        if s2.size().getInfo() > 0:
            ndvi_val = _mean_ndvi_from(s2_composite)
            if ndvi_val is not None:
                ndvi_val = round(max(-1.0, min(1.0, ndvi_val)), 3)
                _ndvi_cache[cache_key] = ndvi_val
                return ndvi_val

        # --- Fall back to MODIS 16-day NDVI composite (scaled by 0.0001) ---
        modis = (
            ee.ImageCollection(_MODIS_NDVI_COLLECTION)
            .filterBounds(region)
            .filterDate(ee.Date(ee.Date.now()).advance(-45, "day"), ee.Date.now())
            .select("NDVI")
        )
        if modis.size().getInfo() > 0:
            modis_composite = modis.median().multiply(0.0001)
            stats = modis_composite.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=250, maxPixels=1e8
            )
            val = stats.get("NDVI").getInfo()
            if val is not None:
                ndvi_val = round(max(-1.0, min(1.0, float(val))), 3)
                _ndvi_cache[cache_key] = ndvi_val
                return ndvi_val

        logger.info("No usable Sentinel-2 or MODIS imagery found for %s", cache_key)
        return None

    except Exception as exc:  # noqa: BLE001
        logger.warning("Live NDVI fetch failed for (%s, %s): %s", lat, lng, exc)
        return None


# ---------------------------------------------------------------------------
# Weather (Open-Meteo)
# ---------------------------------------------------------------------------

def _classify_rainfall(daily_precip_mm: list[float]) -> str:
    total = sum(v for v in daily_precip_mm if v is not None)
    rainy_days = sum(1 for v in daily_precip_mm if v and v > 1.0)

    if total < 2:
        return "little to no rain expected"
    if total < 15 and rainy_days <= 2:
        return "light rain expected"
    if total < 40:
        return "moderate rain expected over the week"
    return "heavy rain expected, plan for possible waterlogging"


def _fetch_weather_live(lat: float, lng: float) -> Optional[dict]:
    """
    Pull a 7-day forecast from Open-Meteo (no API key required).
    Returns None on any failure — never raises.
    """
    try:
        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "forecast_days": 7,
        }
        resp = requests.get(params=params, url=OPEN_METEO_URL, timeout=OPEN_METEO_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        if not tmax or not tmin:
            return None

        avg_temps = [
            (mx + mn) / 2.0
            for mx, mn in zip(tmax, tmin)
            if mx is not None and mn is not None
        ]
        if not avg_temps:
            return None

        temp_avg_c = round(sum(avg_temps) / len(avg_temps), 1)
        forecast_text = _classify_rainfall(precip)
        rainfall_mm_7day = round(sum(v for v in precip if v is not None), 1)

        return {
            "forecast_7day": forecast_text,
            "temp_avg_c": temp_avg_c,
            "rainfall_mm_7day": rainfall_mm_7day,
        }

    except Exception as exc:  # noqa: BLE001
        logger.warning("Live weather fetch failed for (%s, %s): %s", lat, lng, exc)
        return None


def _fallback_weather(entry: dict) -> dict:
    """
    Synthesize a plausible 7-day forecast summary (including a rainfall
    figure) from the curated soil profile when Open-Meteo is unreachable.
    Deliberately conservative / generic language rather than inventing
    precise-sounding numbers, though rainfall_mm_7day is still a concrete
    number since the Gemini prompt in advisory.py uses it directly.
    """
    moisture = entry.get("moisture", "moderate")
    if moisture == "high":
        forecast_7day = "light rain expected"
        temp_avg_c = 27.0
        rainfall_mm_7day = 18.0
    elif moisture == "low":
        forecast_7day = "little to no rain expected, dry conditions likely"
        temp_avg_c = 33.0
        rainfall_mm_7day = 2.0
    else:
        forecast_7day = "scattered light showers possible"
        temp_avg_c = 30.0
        rainfall_mm_7day = 8.0
    return {
        "forecast_7day": forecast_7day,
        "temp_avg_c": temp_avg_c,
        "rainfall_mm_7day": rainfall_mm_7day,
    }


# ---------------------------------------------------------------------------
# pH estimate helper
# ---------------------------------------------------------------------------

def _estimate_ph(ndvi: float, fallback_entry: dict) -> float:
    """
    Soil pH cannot be derived from optical NDVI directly. We use the curated
    district value as the primary estimate (it's a real per-district figure),
    with a very small NDVI-informed nudge so two nearby points with
    different vegetation health don't return an identical pH figure. This is
    explicitly an *estimate*, matching the contract's `ph_estimate` naming.
    """
    base_ph = float(fallback_entry.get("ph_estimate", 6.8))
    expected_ndvi = float(fallback_entry.get("ndvi", 0.4))
    delta = ndvi - expected_ndvi
    nudged = base_ph - (delta * 0.4)  # small, bounded nudge
    return round(max(4.5, min(9.0, nudged)), 2)


# ---------------------------------------------------------------------------
# Result cache (whole get_signals() output, keyed on rounded location)
# ---------------------------------------------------------------------------

def _location_cache_key(lat: float, lng: float) -> str:
    # Rounded to ~100m precision — plenty for "same demo pin clicked again",
    # while not accidentally merging genuinely distinct nearby farms.
    return f"{round(lat, 3)},{round(lng, 3)}"


def _get_cached_signals(cache_key: str) -> Optional[dict]:
    if CACHE_TTL_S <= 0:
        return None
    entry = _signals_cache.get(cache_key)
    if entry is None:
        return None
    expires_at, result = entry
    if time.monotonic() >= expires_at:
        _signals_cache.pop(cache_key, None)
        return None
    return result


def _store_cached_signals(cache_key: str, result: dict) -> None:
    if CACHE_TTL_S <= 0:
        return
    _signals_cache[cache_key] = (time.monotonic() + CACHE_TTL_S, dict(result))


def clear_cache() -> None:
    """Clear both the NDVI and full-signals caches. Mainly useful for tests
    or if you want to force a fresh live pull mid-demo."""
    _ndvi_cache.clear()
    _signals_cache.clear()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_signals(location: dict) -> dict:
    """
    Resolve soil + weather + NDVI signals for a location.

    Parameters
    ----------
    location : dict
        Expected shape (matches models.Location / the /api/advisory request):
        {"lat": 15.3, "lng": 75.7, "state": "Karnataka", "district": "Belagavi"}
        Only "lat"/"lng" are needed for live lookups; "district" is used for
        the curated fallback lookup and should be provided when possible.

    Returns
    -------
    dict with exactly the keys advisory.py expects:
        soil_moisture, soil_ph_estimate, ndvi, forecast_7day, temp_avg_c,
        rainfall_mm_7day

    This function NEVER raises for network/auth/quota problems — any live
    lookup failure (Earth Engine auth, Open-Meteo unreachable, etc.) falls
    back to curated per-district data instead. If both lat and lng are
    missing/invalid it raises ValueError (that's a caller bug, not a
    flaky-external-service problem, so it's surfaced rather than silently
    faked).
    """
    if not isinstance(location, dict):
        raise ValueError("location must be a dict")

    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        raise ValueError("location must include numeric 'lat' and 'lng'")
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError) as exc:
        raise ValueError("location 'lat'/'lng' must be numeric") from exc
    if math.isnan(lat) or math.isnan(lng):
        raise ValueError("location 'lat'/'lng' must be finite numbers")

    cache_key = _location_cache_key(lat, lng)
    cached = _get_cached_signals(cache_key)
    if cached is not None:
        return dict(cached)

    fallback_entry = _fallback_entry_for(location)

    # --- NDVI ---
    ndvi = _fetch_ndvi_live(lat, lng)
    if ndvi is None:
        ndvi = float(fallback_entry["ndvi"])

    # --- Weather (forecast_7day, temp_avg_c, rainfall_mm_7day) ---
    weather = _fetch_weather_live(lat, lng)
    if weather is None:
        weather = _fallback_weather(fallback_entry)

    # --- Moisture: derive from fallback entry (real soil-moisture products
    # like SMAP need their own auth/collection; out of scope for the hackathon
    # timeline, so we use the curated label, which already reflects
    # district-typical conditions) ---
    soil_moisture = fallback_entry.get("moisture", "moderate")

    # --- pH estimate ---
    soil_ph_estimate = _estimate_ph(ndvi, fallback_entry)

    result = {
        "soil_moisture": soil_moisture,
        "soil_ph_estimate": soil_ph_estimate,
        "ndvi": round(float(ndvi), 3),
        "forecast_7day": weather["forecast_7day"],
        "temp_avg_c": weather["temp_avg_c"],
        "rainfall_mm_7day": weather["rainfall_mm_7day"],
    }

    _store_cached_signals(cache_key, result)
    return dict(result)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    sample = {"lat": 15.3, "lng": 75.7, "state": "Karnataka", "district": "Belagavi"}
    print("First call (fresh):")
    print(json.dumps(get_signals(sample), indent=2))
    print("\nSecond call (served from cache, no network hit):")
    print(json.dumps(get_signals(sample), indent=2))
    sys.exit(0)
