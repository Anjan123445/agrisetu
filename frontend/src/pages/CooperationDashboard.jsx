import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageShell from "../components/Layout";
import { useApp } from "../context/AppContext";
import { getCooperationDashboard } from "../api/api";
import { LoadingState, ErrorState } from "./AdvisoryDashboard";

export default function CooperationDashboard() {
  const { t } = useApp();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCooperationDashboard()
      .then(setData)
      .catch(() => setError(t.errorGeneric))
      .finally(() => setLoading(false));
  }, []);

  const chartData =
    data?.state_summaries.map((s) => ({
      state: s.state,
      farmers: s.active_farmers,
      soilHealth: Math.round(s.avg_soil_health * 100),
    })) ?? [];

  return (
    <PageShell showBack>
      <section className="mx-auto max-w-2xl px-5 py-6 sm:px-8">
        <h1 className="font-display text-2xl font-semibold text-leaf-deep sm:text-3xl">
          {t.coopTitle}
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-ink/70">{t.coopBody}</p>

        {loading && <LoadingState message={t.loading} />}
        {error && <ErrorState message={error} />}

        {data && !loading && (
          <div className="mt-6 space-y-8">
            {/* Chart */}
            <div className="rounded-2xl border border-ink/10 bg-white p-4">
              <h2 className="text-sm font-bold uppercase tracking-wide text-ink/60">
                {t.coopTableFarmers}
              </h2>
              <div className="mt-3 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E6DCC0" vertical={false} />
                    <XAxis
                      dataKey="state"
                      tick={{ fontSize: 10, fill: "#232920" }}
                      interval={0}
                      angle={-30}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 11, fill: "#232920" }} />
                    <Tooltip
                      contentStyle={{
                        borderRadius: 12,
                        border: "1px solid #E6DCC0",
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="farmers" fill="#3F6B2D" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-hidden rounded-2xl border border-ink/10 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="bg-husk-deep text-xs font-bold uppercase tracking-wide text-ink/60">
                  <tr>
                    <th className="px-4 py-3">{t.coopTableState}</th>
                    <th className="px-4 py-3">{t.coopTableCrops}</th>
                    <th className="px-4 py-3 text-right">{t.coopTableSoil}</th>
                    <th className="px-4 py-3 text-right">{t.coopTableFarmers}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink/5">
                  {data.state_summaries.map((row) => (
                    <tr key={row.state}>
                      <td className="px-4 py-3 font-semibold text-ink">{row.state}</td>
                      <td className="px-4 py-3 text-ink/70">{row.top_crops.join(", ")}</td>
                      <td className="px-4 py-3 text-right font-mono text-ink/70">
                        {Math.round(row.avg_soil_health * 100)}%
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-ink/70">
                        {row.active_farmers}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </PageShell>
  );
}
