import { Link } from "react-router-dom";
import PageShell from "../components/Layout";
import FurrowDivider from "../components/FurrowDivider";
import { useApp } from "../context/AppContext";

export default function Landing() {
  const { t } = useApp();

  return (
    <PageShell dark>
      {/* Hero */}
      <section className="bg-leaf-deep px-5 pb-14 pt-6 text-white sm:px-8 sm:pb-20 sm:pt-10">
        <div className="mx-auto max-w-xl">
          <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-husk/70">
            {t.tagline}
          </p>
          <h1 className="font-display text-4xl font-semibold leading-[1.1] sm:text-5xl">
            {t.heroHeadline}
          </h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-husk/85 sm:text-lg">
            {t.heroBody}
          </p>
          <Link
            to="/location"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-marigold px-6 py-3.5 text-base font-bold text-leaf-deep shadow-lg shadow-black/20 transition-transform active:scale-95 sm:hover:-translate-y-0.5"
          >
            {t.ctaAdvisory}
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </section>

      <FurrowDivider tone="marigold" className="bg-leaf-deep" />

      {/* Secondary actions */}
      <section className="px-5 py-10 sm:px-8">
        <div className="mx-auto grid max-w-xl gap-3 sm:grid-cols-3">
          <QuickCard to="/diagnose" emoji="🍃" label={t.ctaDiagnose} />
          <QuickCard to="/ask" emoji="🎙" label={t.ctaVoice} />
          <QuickCard to="/network" emoji="📊" label={t.ctaCoop} />
        </div>
      </section>

      <FurrowDivider className="px-5 sm:px-8" />

      {/* How it works */}
      <section className="px-5 py-10 sm:px-8">
        <div className="mx-auto max-w-xl">
          <h2 className="font-display text-2xl font-semibold text-leaf-deep">
            Three signals, one field
          </h2>
          <div className="mt-6 space-y-5">
            <Signal
              tone="earth"
              title="Soil"
              body="Moisture, estimated pH and vegetation health for the plot you point to."
            />
            <Signal
              tone="sky"
              title="Weather"
              body="A 7-day forecast tuned to your exact coordinates, not just the district."
            />
            <Signal
              tone="marigold"
              title="Season"
              body="What you've grown before, factored into every recommendation."
            />
          </div>
        </div>
      </section>
    </PageShell>
  );
}

function QuickCard({ to, emoji, label }) {
  return (
    <Link
      to={to}
      className="flex flex-col items-center gap-2 rounded-2xl border border-ink/10 bg-white px-4 py-5 text-center shadow-sm transition-colors hover:bg-husk-deep"
    >
      <span className="text-2xl" aria-hidden="true">
        {emoji}
      </span>
      <span className="text-sm font-semibold text-ink">{label}</span>
    </Link>
  );
}

function Signal({ tone, title, body }) {
  const bg = tone === "earth" ? "bg-earth" : tone === "sky" ? "bg-sky" : "bg-marigold";
  return (
    <div className="flex gap-4">
      <span className={`mt-1 h-2.5 w-2.5 flex-none rounded-full ${bg}`} aria-hidden="true" />
      <div>
        <h3 className="font-semibold text-ink">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-ink/70">{body}</p>
      </div>
    </div>
  );
}
