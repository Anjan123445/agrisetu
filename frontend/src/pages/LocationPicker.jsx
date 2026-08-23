import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageShell from "../components/Layout";
import { useApp } from "../context/AppContext";
import { STATES } from "../i18n/statesDistricts";

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

export default function LocationPicker() {
  const { t, setLocation } = useApp();
  const navigate = useNavigate();
  const [mode, setMode] = useState(GOOGLE_MAPS_API_KEY ? "map" : "dropdown");

  return (
    <PageShell showBack>
      <section className="mx-auto max-w-xl px-5 py-8 sm:px-8">
        <h1 className="font-display text-2xl font-semibold text-leaf-deep sm:text-3xl">
          {t.locationTitle}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-ink/70">{t.locationBody}</p>

        <div className="mt-6">
          {mode === "map" ? (
            <MapPicker onFallback={() => setMode("dropdown")} onPicked={handlePicked} />
          ) : (
            <DropdownPicker onPicked={handlePicked} />
          )}
        </div>

        {GOOGLE_MAPS_API_KEY && (
          <button
            type="button"
            onClick={() => setMode(mode === "map" ? "dropdown" : "map")}
            className="mt-5 text-sm font-semibold text-leaf underline underline-offset-2"
          >
            {mode === "map" ? t.locationUseDropdown : t.locationUseMap}
          </button>
        )}
      </section>
    </PageShell>
  );

  function handlePicked(loc) {
    setLocation(loc);
    navigate("/advisory");
  }
}

// ---------------------------------------------------------------------------
// Google Maps picker — loads the JS SDK only if VITE_GOOGLE_MAPS_API_KEY is set.
// Falls back automatically if the script fails to load (e.g. no key/quota).
// ---------------------------------------------------------------------------
function MapPicker({ onPicked, onFallback }) {
  const { t } = useApp();
  const mapRef = useRef(null);
  const [marker, setMarker] = useState(null); // {lat, lng, state, district}
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const mapInstance = useRef(null);
  const markerInstance = useRef(null);
  const geocoder = useRef(null);

  useEffect(() => {
    if (window.google?.maps) {
      setReady(true);
      return;
    }
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places`;
    script.async = true;
    script.onload = () => setReady(true);
    script.onerror = () => setFailed(true);
    document.head.appendChild(script);
  }, []);

  useEffect(() => {
    if (!ready || !mapRef.current || mapInstance.current) return;
    const center = { lat: 20.5937, lng: 78.9629 }; // India centroid
    mapInstance.current = new window.google.maps.Map(mapRef.current, {
      center,
      zoom: 5,
      streetViewControl: false,
      mapTypeControl: false,
      fullscreenControl: false,
    });
    geocoder.current = new window.google.maps.Geocoder();

    mapInstance.current.addListener("click", (e) => {
      placeMarker(e.latLng.lat(), e.latLng.lng());
    });
  }, [ready]);

  useEffect(() => {
    if (failed) onFallback();
  }, [failed]);

  function placeMarker(lat, lng) {
    if (!markerInstance.current) {
      markerInstance.current = new window.google.maps.Marker({
        position: { lat, lng },
        map: mapInstance.current,
      });
    } else {
      markerInstance.current.setPosition({ lat, lng });
    }
    geocoder.current.geocode({ location: { lat, lng } }, (results, status) => {
      let state = "";
      let district = "";
      if (status === "OK" && results?.[0]) {
        for (const comp of results[0].address_components) {
          if (comp.types.includes("administrative_area_level_1")) state = comp.long_name;
          if (comp.types.includes("administrative_area_level_2")) district = comp.long_name;
        }
      }
      setMarker({ lat, lng, state, district });
    });
  }

  return (
    <div>
      <div
        ref={mapRef}
        className="h-64 w-full overflow-hidden rounded-2xl border border-ink/10 bg-husk-deep sm:h-80"
      >
        {!ready && !failed && (
          <div className="flex h-full items-center justify-center text-sm text-ink/50">
            {t.locationDetecting}
          </div>
        )}
      </div>
      {marker && (
        <div className="mt-4 rounded-xl bg-white p-4 text-sm">
          <p className="font-semibold text-ink">
            {marker.district || "—"}, {marker.state || "—"}
          </p>
          <p className="mt-0.5 font-mono text-xs text-ink/50">
            {marker.lat.toFixed(4)}, {marker.lng.toFixed(4)}
          </p>
        </div>
      )}
      <button
        type="button"
        disabled={!marker}
        onClick={() => onPicked(marker)}
        className="mt-5 w-full rounded-full bg-leaf px-6 py-3.5 text-base font-bold text-white transition-colors disabled:cursor-not-allowed disabled:bg-ink/20 sm:hover:bg-leaf-deep"
      >
        {t.locationContinue}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// State / district dropdown fallback — no external dependency, works offline.
// ---------------------------------------------------------------------------
function DropdownPicker({ onPicked }) {
  const { t } = useApp();
  const [stateName, setStateName] = useState("");
  const [district, setDistrict] = useState("");

  const stateObj = STATES.find((s) => s.state === stateName);

  return (
    <div className="space-y-4">
      <Field label={t.locationStateLabel}>
        <select
          value={stateName}
          onChange={(e) => {
            setStateName(e.target.value);
            setDistrict("");
          }}
          className="w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-base"
        >
          <option value="">—</option>
          {STATES.map((s) => (
            <option key={s.state} value={s.state}>
              {s.state}
            </option>
          ))}
        </select>
      </Field>

      <Field label={t.locationDistrictLabel}>
        <select
          value={district}
          disabled={!stateObj}
          onChange={(e) => setDistrict(e.target.value)}
          className="w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-base disabled:bg-husk-deep disabled:text-ink/40"
        >
          <option value="">—</option>
          {stateObj?.districts.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </Field>

      <button
        type="button"
        disabled={!stateObj || !district}
        onClick={() =>
          onPicked({
            lat: stateObj.lat,
            lng: stateObj.lng,
            state: stateObj.state,
            district,
          })
        }
        className="w-full rounded-full bg-leaf px-6 py-3.5 text-base font-bold text-white transition-colors disabled:cursor-not-allowed disabled:bg-ink/20 sm:hover:bg-leaf-deep"
      >
        {t.locationContinue}
      </button>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold text-ink/80">{label}</span>
      {children}
    </label>
  );
}
