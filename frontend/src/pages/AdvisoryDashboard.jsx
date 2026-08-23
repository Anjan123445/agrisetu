import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import PageShell from "../components/Layout";
import FurrowDivider from "../components/FurrowDivider";
import { useApp } from "../context/AppContext";
import { getAdvisory } from "../api/api";

export default function AdvisoryDashboard() {
  const { t, language, location } = useApp();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    if (!location) {
      navigate("/location");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getAdvisory({ location, language, crop_history: [] })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {
        if (!cancelled) setError(t.errorGeneric);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [location, language]);

  function togglePlay() {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(() => {});
    }
    setPlaying(!playing);
  }

  return (
    <PageShell showBack>
      <section className="mx-auto max-w-xl px-5 py-6 sm:px-8">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-semibold text-leaf-deep sm:text-3xl">
              {t.advisoryTitle}
            </h1>
            {location && (
              <p className="mt-1 text-sm text-ink/60">
                {location.district}, {location.state}
              </p>
            )}
          </div>
          <Link
            to="/location"
            className="flex-none whitespace-nowrap rounded-full border border-ink/15 px-3 py-1.5 text-xs font-semibold text-ink/70 hover:bg-white"
          >
            {t.changeLocation}
          </Link>
        </div>

        {loading && <LoadingState message={t.advisoryLoading} />}
        {error && <ErrorState message={error} />}

        {data && !loading && (
          <div className="mt-6 space-y-6">
            {/* Advisory text + audio */}
            <div className="rounded-2xl bg-leaf-deep p-5 text-white shadow-md">
              <p className="text-base leading-relaxed">{data.advisory_text}</p>
              <button
                type="button"
                onClick={togglePlay}
                className="mt-4 flex items-center gap-2 rounded-full bg-marigold px-5 py-2.5 text-sm font-bold text-leaf-deep active:scale-95"
              >
                <span aria-hidden="true">{playing ? "❚❚" : "▶"}</span>
                {playing ? t.pauseAdvisory : t.playAdvisory}
              </button>
              <audio
                ref={audioRef}
                src={data.audio_url}
                onEnded={() => setPlaying(false)}
                className="hidden"
              />
            </div>

            <FurrowDivider tone="earth" />

            {/* Recommended crops */}
            <div>
              <h2 className="font-display text-xl font-semibold text-leaf-deep">
                {t.recommendedCrops}
              </h2>
              <div className="mt-3 space-y-3">
                {data.recommended_crops.map((crop) => (
                  <CropCard key={crop.name} crop={crop} />
                ))}
              </div>
            </div>

            {/* Soil + weather */}
            <div className="grid gap-4 sm:grid-cols-2">
              <SummaryCard title={t.soilSummary} tone="earth">
                <Stat label={t.moisture} value={capitalize(data.soil_summary.moisture)} />
                <Stat label={t.phEstimate} value={data.soil_summary.ph_estimate} />
                <Stat label={t.ndvi} value={data.soil_summary.ndvi} />
              </SummaryCard>
              <SummaryCard title={t.weatherSummary} tone="sky">
                <Stat label={t.avgTemp} value={`${data.weather_summary.temp_avg_c}°C`} />
                <p className="mt-2 text-sm leading-relaxed text-ink/70">
                  {data.weather_summary.forecast_7day}
                </p>
              </SummaryCard>
            </div>
          </div>
        )}
      </section>
    </PageShell>
  );
}

function CropCard({ crop }) {
  const pct = Math.round(crop.confidence * 100);
  return (
    <div className="rounded-2xl border border-ink/10 bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-ink">{crop.name}</h3>
        <span className="font-mono text-xs font-semibold text-marigold">{pct}%</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-husk-deep">
        <div className="h-full rounded-full bg-marigold" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-sm leading-relaxed text-ink/70">{crop.reason}</p>
    </div>
  );
}

function SummaryCard({ title, tone, children }) {
  const border = tone === "earth" ? "border-earth/30" : "border-sky/30";
  return (
    <div className={`rounded-2xl border ${border} bg-white p-4`}>
      <h3 className="text-sm font-bold uppercase tracking-wide text-ink/60">{title}</h3>
      <div className="mt-2 space-y-1.5">{children}</div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="flex items-baseline justify-between text-sm">
      <span className="text-ink/60">{label}</span>
      <span className="font-mono font-semibold text-ink">{value}</span>
    </div>
  );
}

export function LoadingState({ message }) {
  return (
    <div className="mt-8 flex flex-col items-center gap-3 py-10 text-center">
      <div className="h-8 w-8 animate-spin rounded-full border-[3px] border-leaf/20 border-t-leaf" />
      <p className="text-sm text-ink/60">{message}</p>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div className="mt-6 rounded-xl border border-alert/30 bg-alert/5 p-4 text-sm text-alert">
      {message}
    </div>
  );
}

function capitalize(s) {
  return typeof s === "string" ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}
