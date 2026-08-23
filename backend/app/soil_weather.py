"""
OWNER: teammate A (Earth Engine + weather).
STATUS: stub — returns realistic fake data so advisory.py can be built
and tested end-to-end today. Replace get_signals() with a real Earth
Engine NDVI/soil-moisture pull + weather API call. Keep the return
shape exactly as-is; advisory.py and the Gemini prompt depend on it.

Contract:
    get_signals(location: dict) -> dict

Input `location` shape (matches models.Location):
    {"lat": float, "lng": float, "state": str, "district": str}

Required output keys (advisory.py reads all of these):
    {
      "soil_moisture": str,        # e.g. "low" | "moderate" | "high"
      "soil_ph_estimate": float,
      "ndvi": float,                # 0.0 - 1.0
      "forecast_7day": str,         # short human-readable forecast
      "temp_avg_c": float,
      "rainfall_mm_7day": float,    # extra signal, useful for the Gemini prompt
    }
"""

import hashlib
import random


def get_signals(location: dict) -> dict:
    """
    STUB. Deterministic-per-location fake data (seeded off lat/lng so the
    same location always returns the same fake signals during testing,
    instead of random noise on every call).

    Real implementation should call:
      - Google Earth Engine (NDVI, soil moisture) for `location`
      - A weather API (e.g. Open-Meteo / IMD) for 7-day forecast at lat/lng
    """
    lat = location.get("lat", 0.0)
    lng = location.get("lng", 0.0)
    seed = int(hashlib.sha256(f"{lat:.3f},{lng:.3f}".encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)

    moisture_options = ["low", "moderate", "high"]
    forecast_options = [
        "light rain expected",
        "clear skies, low rainfall expected",
        "heavy rain expected mid-week",
        "hot and dry, no rain expected",
    ]

    return {
        "soil_moisture": rng.choice(moisture_options),
        "soil_ph_estimate": round(rng.uniform(5.5, 7.5), 1),
        "ndvi": round(rng.uniform(0.2, 0.7), 2),
        "forecast_7day": rng.choice(forecast_options),
        "temp_avg_c": round(rng.uniform(22.0, 34.0), 1),
        "rainfall_mm_7day": round(rng.uniform(0.0, 60.0), 1),
    }
