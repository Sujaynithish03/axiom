import { useEffect, useState } from "react";
import { engineByKey } from "../engines";
import { Sparkles, Loader2, ImageIcon, AlertTriangle, Download } from "lucide-react";

interface Poster {
  id: number; ts: string; prompt: string; image_url: string | null;
  caption: string | null; status: "ok" | "error"; error: string | null;
}

const SUGGESTIONS = [
  "Festive Diwali sale poster, warm gold tones",
  "Instagram square post announcing a new product launch",
  "Minimal before/after skincare results poster",
  "Influencer-style testimonial ad poster",
];

export default function AdPosterView() {
  const def = engineByKey("adposter")!;
  const [brief, setBrief] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [posters, setPosters] = useState<Poster[]>([]);
  const Icon = def.icon;

  const loadHistory = () =>
    fetch("/api/adposter/history?limit=12").then((r) => r.json()).then(setPosters).catch(() => {});

  useEffect(() => { loadHistory(); }, []);

  const generate = async () => {
    const text = brief.trim();
    if (!text || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/adposter/generate", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ brief: text }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Generation failed.");
      } else {
        setPosters((p) => [data, ...p]);
        setBrief("");
      }
    } catch (e) {
      setError("Could not reach the backend.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 max-w-[1100px] mx-auto">
      <header className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div className="flex items-start gap-3">
          <div
            className="w-11 h-11 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `${def.color}1A`, border: `1px solid ${def.color}55` }}
          >
            <Icon size={22} style={{ color: def.color }} />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-muted font-mono">
              Engine · Gemini-powered
            </div>
            <h1 className="text-xl sm:text-2xl font-bold mt-0.5">{def.title}</h1>
            <p className="text-muted text-sm mt-1 max-w-xl">{def.subtitle}</p>
          </div>
        </div>
      </header>

      {/* Brief input */}
      <div className="bg-surface border border-border rounded-xl p-4 sm:p-5 mb-6">
        <div className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: def.color }}>
          Creative brief
        </div>
        <textarea
          value={brief}
          onChange={(e) => setBrief(e.target.value)}
          placeholder="Describe the poster you want — occasion, mood, offer…"
          rows={2}
          disabled={busy}
          className="w-full bg-surface2 border border-border rounded-lg px-3 py-2.5 text-sm resize-none focus:outline-none focus:border-current"
          style={{ caretColor: def.color }}
        />
        {!brief && (
          <div className="flex flex-wrap gap-2 mt-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setBrief(s)}
                className="text-xs text-left px-3 py-1.5 rounded-lg border border-border bg-surface2 hover:border-current transition"
                style={{ color: def.color }}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-3">
          <div className="text-[11px] text-muted">
            Real-time image generation via Gemini — every other engine in AXIOM stays fully local.
          </div>
          <button
            onClick={generate}
            disabled={busy || !brief.trim()}
            className="flex items-center gap-2 font-medium text-sm py-2.5 px-4 rounded-lg transition disabled:opacity-50 shrink-0"
            style={{ background: def.color, color: "#070A14" }}
          >
            {busy ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={14} />}
            {busy ? "Generating…" : def.cta}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-surface border border-danger/40 rounded-lg p-4 mb-6 flex gap-3">
          <AlertTriangle size={18} className="text-danger shrink-0 mt-0.5" />
          <div>
            <div className="text-danger font-medium text-sm mb-1">Generation failed</div>
            <div className="text-xs text-muted leading-relaxed">{error}</div>
          </div>
        </div>
      )}

      {/* Gallery */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {posters.length === 0 && !busy && (
          <div className="col-span-full bg-surface border border-border rounded-xl p-10 text-center">
            <ImageIcon size={30} style={{ color: def.color }} className="mx-auto mb-3 opacity-70" />
            <div className="text-sm text-muted max-w-md mx-auto">
              No posters yet. Write a brief above and click <b className="text-text">{def.cta}</b>.
            </div>
          </div>
        )}
        {posters.filter((p) => p.status === "ok" && p.image_url).map((p) => (
          <div key={p.id} className="bg-surface border border-border rounded-xl overflow-hidden hover-lift">
            <img src={p.image_url!} alt={p.prompt} className="w-full aspect-square object-cover" />
            <div className="p-3">
              <div className="text-xs text-text/80 line-clamp-2">{p.prompt}</div>
              <div className="flex items-center justify-between mt-2">
                <div className="text-[10px] text-muted font-mono">
                  {new Date(p.ts + "Z").toLocaleString()}
                </div>
                <a
                  href={p.image_url!}
                  download
                  className="flex items-center gap-1 text-[11px] font-mono hover:underline"
                  style={{ color: def.color }}
                >
                  <Download size={12} /> Save
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
