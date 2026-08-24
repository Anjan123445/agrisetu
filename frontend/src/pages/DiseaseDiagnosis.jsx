import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageShell from "../components/Layout";
import FurrowDivider from "../components/FurrowDivider";
import { useApp } from "../context/AppContext";
import { getDiseaseDiagnosis } from "../api/api";
import { LoadingState, ErrorState } from "./AdvisoryDashboard";

export default function DiseaseDiagnosis() {
  const { t, language, location } = useApp();
  const navigate = useNavigate(); // Initialize navigate
  
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  // Guard: redirect to location picker if location context is missing
  useEffect(() => {
    if (!location) navigate("/location");
  }, [location, navigate]);

  function handleFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    setPreviewUrl(URL.createObjectURL(f));
  }

  async function handleSubmit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    
    // Retrieve deviceId safely if you added it to AppContext earlier, 
    // or leave as is based on how you implemented the API params!
    try {
      const res = await getDiseaseDiagnosis({ image: file, location, language });
      setResult(res);
    } catch {
      setError(t.errorGeneric);
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell showBack>
      <section className="mx-auto max-w-xl px-5 py-6 sm:px-8">
        <h1 className="font-display text-2xl font-semibold text-leaf-deep sm:text-3xl">
          {t.diseaseTitle}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-ink/70">{t.diseaseBody}</p>

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFile}
          className="hidden"
        />

        {!previewUrl ? (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="mt-6 flex w-full flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-leaf/40 bg-white px-6 py-12 text-center transition-colors hover:bg-husk-deep"
          >
            <span className="text-4xl" aria-hidden="true">📷</span>
            <span className="font-semibold text-leaf-deep">{t.diseaseUpload}</span>
          </button>
        ) : (
          <div className="mt-6">
            <img
              src={previewUrl}
              alt="Uploaded crop leaf"
              className="h-64 w-full rounded-2xl border border-ink/10 object-cover"
            />
            <div className="mt-3 flex gap-3">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="flex-1 rounded-full border border-ink/15 px-4 py-3 text-sm font-semibold text-ink hover:bg-white"
              >
                {t.diseaseRetake}
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="flex-1 rounded-full bg-leaf px-4 py-3 text-sm font-bold text-white disabled:bg-ink/20 sm:hover:bg-leaf-deep"
              >
                {t.diseaseSubmit}
              </button>
            </div>
          </div>
        )}

        {loading && <LoadingState message={t.diseaseLoading} />}
        {error && <ErrorState message={error} />}

        {result && !loading && (
          <div className="mt-6 space-y-5">
            <FurrowDivider tone="marigold" />
            <div className="rounded-2xl border border-alert/25 bg-white p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-xl font-semibold text-alert">
                  {result.disease_name}
                </h2>
                <span className="font-mono text-xs font-semibold text-ink/60">
                  {t.diseaseConfidence} {Math.round(result.confidence * 100)}%
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink/70">{result.description}</p>
            </div>

            <div className="rounded-2xl bg-white p-5">
              <h3 className="text-sm font-bold uppercase tracking-wide text-ink/60">
                {t.diseaseRemedy}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-ink">{result.remedy}</p>
            </div>

            <div className="rounded-2xl bg-white p-5">
              <h3 className="text-sm font-bold uppercase tracking-wide text-ink/60">
                {t.diseasePrevention}
              </h3>
              <ul className="mt-2 space-y-2">
                {result.prevention_tips.map((tip, i) => (
                  <li key={i} className="flex gap-2 text-sm leading-relaxed text-ink">
                    <span className="mt-0.5 flex-none text-leaf" aria-hidden="true">
                      ✓
                    </span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </section>
    </PageShell>
  );
}