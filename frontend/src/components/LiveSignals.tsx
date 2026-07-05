import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";
import { Globe, TrendingUp, TrendingDown, Newspaper, ExternalLink } from "lucide-react";

interface Interest { topic: string; points: { date: string; views: number }[]; total_views: number; trend_pct: number; source: string; }
interface NewsItem { title: string; url: string; date: string; source: string; }
interface Signals { interest: Interest | null; news: NewsItem[]; live: boolean; fetched_at: string; }

export default function LiveSignals() {
  const [sig, setSig] = useState<Signals | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/signals/live").then((r) => r.json()).then(setSig).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const it = sig?.interest;
  const up = (it?.trend_pct ?? 0) >= 0;

  return (
    <section className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Globe size={14} className="text-info" />
        <h2 className="text-sm font-mono uppercase tracking-widest text-muted">Live Market Signals</h2>
        <span className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest text-info">
          <span className="w-1.5 h-1.5 rounded-full bg-info pulse-ring" /> External · Live
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Category interest (Wikipedia) */}
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="text-[10px] uppercase tracking-widest text-muted font-mono mb-1">
            Category interest · 30d
          </div>
          {loading ? (
            <div className="text-muted text-sm">Fetching real data…</div>
          ) : it ? (
            <>
              <div className="flex items-baseline justify-between">
                <div className="text-lg font-bold">{it.topic}</div>
                <div className={`flex items-center gap-1 text-sm font-mono ${up ? "text-mint" : "text-danger"}`}>
                  {up ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {up ? "+" : ""}{it.trend_pct}%
                </div>
              </div>
              <div className="text-xs text-muted font-mono mt-0.5">
                {it.total_views.toLocaleString()} views
              </div>
              <div className="h-14 mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={it.points}>
                    <defs>
                      <linearGradient id="sig" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#5EA0FF" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="#5EA0FF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <YAxis hide domain={["dataMin", "dataMax"]} />
                    <Area type="monotone" dataKey="views" stroke="#5EA0FF" strokeWidth={1.5} fill="url(#sig)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="text-[10px] text-muted/70 font-mono mt-1">source: {it.source}</div>
            </>
          ) : (
            <div className="text-muted text-sm">No live interest data (offline?).</div>
          )}
        </div>

        {/* Industry news (Google News) */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-muted font-mono mb-2">
            <Newspaper size={11} /> Real industry news
          </div>
          {loading ? (
            <div className="text-muted text-sm">Fetching headlines…</div>
          ) : sig?.news?.length ? (
            <ul className="space-y-2">
              {sig.news.slice(0, 5).map((n, i) => (
                <li key={i}>
                  <a href={n.url} target="_blank" rel="noopener noreferrer"
                     className="group flex items-start gap-2 text-sm text-text/90 hover:text-info transition">
                    <ExternalLink size={13} className="mt-0.5 shrink-0 text-muted group-hover:text-info" />
                    <span className="flex-1">
                      {n.title}
                      <span className="text-[10px] text-muted font-mono ml-2">{n.source}</span>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-muted text-sm">No live news (offline?).</div>
          )}
        </div>
      </div>
    </section>
  );
}
