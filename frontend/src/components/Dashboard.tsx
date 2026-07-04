import { useAxiom } from "../store";
import KpiTile from "./KpiTile";
import RecommendationCard from "./RecommendationCard";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { useEffect, useMemo } from "react";
import { AlertTriangle, Sparkles } from "lucide-react";

export default function Dashboard() {
  const { kpis, history, recommendations, fetchAll, business } = useAxiom();

  useEffect(() => { fetchAll(); }, []);

  const briefing = useMemo(() => {
    return recommendations.find(
      (r) => r.agent === "ceo" && r.payload?.rank === 1
    );
  }, [recommendations]);

  const alerts = useMemo(() => {
    if (!kpis) return [];
    const out: { severity: "high" | "medium"; title: string; detail: string }[] = [];
    if (kpis.avg_bounce > 0.55) out.push({
      severity: "high",
      title: "Bounce rate anomaly",
      detail: `Site bounce rate at ${(kpis.avg_bounce * 100).toFixed(0)}% — well above baseline.`,
    });
    if (kpis.churn_delta > 2) out.push({
      severity: "high",
      title: "Churn accelerating",
      detail: `${kpis.churn_delta} more churn events than prior period.`,
    });
    if (kpis.runway_months < 12) out.push({
      severity: "medium",
      title: "Runway below 12 months",
      detail: `Current runway ${kpis.runway_months.toFixed(1)} months. Time to think about the raise.`,
    });
    if (kpis.competitor_signals >= 4) out.push({
      severity: "medium",
      title: "Competitive pressure",
      detail: `${kpis.competitor_signals} competitor moves in the last 14 days.`,
    });
    return out;
  }, [kpis]);

  if (!kpis) {
    return (
      <div className="p-6 text-muted">Loading KPIs…</div>
    );
  }

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <header className="mb-6 flex items-start justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Dashboard</div>
          <h1 className="text-2xl font-bold mt-1">{business?.name || "Business"}</h1>
          <div className="text-muted text-sm mt-1">{business?.industry} · {business?.stage}</div>
        </div>
        {briefing && (
          <div className="max-w-md bg-surface border-l-2 border-mint p-4 rounded">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-mint font-mono mb-1.5">
              <Sparkles size={12} /> Morning briefing — top decision
            </div>
            <div className="text-sm font-medium text-text">{briefing.title.replace(/^P\d+: /, "")}</div>
            <div className="text-xs text-muted mt-1">{briefing.body}</div>
          </div>
        )}
      </header>

      {/* Top KPI row — the 9 required metrics */}
      <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        <KpiTile
          label="Business Health"
          value={kpis.business_health}
          unit="/100"
          tone={kpis.business_health > 65 ? "positive" : kpis.business_health > 40 ? "warning" : "negative"}
          size="lg"
        />
        <KpiTile
          label="Growth Score"
          value={kpis.growth_score}
          unit="/100"
          delta={kpis.growth_pct}
          tone={kpis.growth_pct > 0 ? "positive" : "negative"}
        />
        <KpiTile
          label="Revenue Opportunity"
          value={`₹${(kpis.revenue_opportunity / 100000).toFixed(1)}L`}
          tone="positive"
        />
        <KpiTile
          label="Lead Score (avg)"
          value={kpis.lead_score_avg}
          unit="/100"
        />
        <KpiTile
          label="Customer Health"
          value={kpis.customer_health}
          unit="/100"
          tone={kpis.customer_health > 70 ? "positive" : "warning"}
        />
        <KpiTile
          label="Market Readiness"
          value={kpis.market_readiness}
          unit="/100"
          tone={kpis.market_readiness > 50 ? "neutral" : "warning"}
        />
        <KpiTile
          label="MRR"
          value={`₹${(kpis.mrr / 100000).toFixed(1)}L`}
          delta={kpis.growth_pct}
          tone={kpis.growth_pct > 0 ? "positive" : "negative"}
        />
        <KpiTile
          label="Runway"
          value={kpis.runway_months.toFixed(1)}
          unit="months"
          tone={kpis.runway_months > 18 ? "positive" : kpis.runway_months > 10 ? "warning" : "negative"}
        />
        <KpiTile
          label="Burn Multiple"
          value={kpis.burn_multiple.toFixed(2)}
          unit="x"
          tone={kpis.burn_multiple < 1.5 ? "positive" : kpis.burn_multiple < 2.5 ? "warning" : "negative"}
        />
        <KpiTile
          label="Active Pipeline"
          value={`₹${(kpis.active_pipeline / 100000).toFixed(1)}L`}
        />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* MRR trend */}
        <div className="lg:col-span-2 bg-surface border border-border rounded p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Business Health · 30d</div>
              <div className="text-lg font-bold mt-0.5">Trend</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-muted font-mono">latest</div>
              <div className="text-xl font-mono font-bold text-mint">{kpis.business_health}</div>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <XAxis
                  dataKey="ts"
                  tickFormatter={(v) => new Date(v).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                  stroke="#8B93A7"
                  fontSize={10}
                  fontFamily="JetBrains Mono"
                />
                <YAxis stroke="#8B93A7" fontSize={10} fontFamily="JetBrains Mono" />
                <Tooltip
                  contentStyle={{ background: "#0E1424", border: "1px solid #1F2942", fontFamily: "JetBrains Mono", fontSize: 12 }}
                />
                <Line type="monotone" dataKey="business_health" stroke="#00E5A0" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk alerts */}
        <div className="bg-surface border border-border rounded p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={14} className="text-warn" />
            <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Risk alerts</div>
          </div>
          {alerts.length === 0 && (
            <div className="text-muted text-sm">No active alerts. Nice.</div>
          )}
          <div className="space-y-2">
            {alerts.map((a, i) => (
              <div key={i} className={`p-3 rounded border-l-2 ${a.severity === "high" ? "border-danger bg-danger/5" : "border-warn bg-warn/5"}`}>
                <div className="text-sm font-medium">{a.title}</div>
                <div className="text-xs text-muted mt-0.5">{a.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Recommendations feed */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={14} className="text-mint" />
          <h2 className="text-sm font-mono uppercase tracking-widest text-muted">
            AI Recommendations
          </h2>
          <div className="text-xs text-muted font-mono ml-2">{recommendations.filter((r) => r.status === "pending").length} pending</div>
        </div>
        <div className="space-y-2">
          {recommendations.length === 0 && (
            <div className="bg-surface border border-border rounded p-6 text-center text-muted">
              No recommendations yet. Click "Start day" to run your boardroom.
            </div>
          )}
          {recommendations.slice(0, 10).map((r) => (
            <RecommendationCard key={r.id} rec={r} />
          ))}
        </div>
      </section>
    </div>
  );
}
