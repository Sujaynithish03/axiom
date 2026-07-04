import { useEffect, useState } from "react";
import EngineView from "./EngineView";
import { Magnet, UserPlus, Loader2, MessageSquare, ChevronDown } from "lucide-react";

const ACCENT = "#5EA0FF";

interface Lead {
  id: number; company: string; contact: string; stage: string;
  deal_size_inr: number; score: number; owner?: string;
}
interface Conversion { channel: string; message: string; next_step: string; }

const scoreColor = (s: number) => (s >= 75 ? "#00E5A0" : s >= 55 ? "#FFB454" : "#8B93A7");
const inr = (n: number) => `₹${(n / 1000).toFixed(0)}k`;

export default function LeadGenView() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [capturing, setCapturing] = useState(false);
  const [conversions, setConversions] = useState<Record<number, Conversion>>({});
  const [convertingId, setConvertingId] = useState<number | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);

  const fetchLeads = async () => {
    try {
      const r = await fetch("/api/leadgen/leads?limit=12").then((x) => x.json());
      setLeads(r || []);
    } catch {}
  };

  useEffect(() => { fetchLeads(); }, []);

  const capture = async () => {
    setCapturing(true);
    try {
      const fresh: Lead[] = await fetch("/api/leadgen/capture", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ count: 4 }),
      }).then((x) => x.json());
      setLeads((prev) => [...fresh, ...prev].slice(0, 12));
    } catch {} finally {
      setCapturing(false);
    }
  };

  const convert = async (id: number) => {
    setOpenId(id);
    if (conversions[id]) return;
    setConvertingId(id);
    try {
      const c: Conversion = await fetch(`/api/leadgen/convert/${id}`, { method: "POST" }).then((x) => x.json());
      setConversions((prev) => ({ ...prev, [id]: c }));
    } catch {} finally {
      setConvertingId(null);
    }
  };

  return (
    <div>
      {/* The AI playbook (segments, digital campaigns, WhatsApp broadcast) */}
      <EngineView engineKey="leadgen" />

      {/* The live acquisition + conversion workspace */}
      <div className="p-4 sm:p-6 max-w-[1100px] mx-auto -mt-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <Magnet size={16} style={{ color: ACCENT }} />
            <h2 className="text-lg font-bold">Live lead capture &amp; conversion</h2>
          </div>
          <button
            onClick={capture}
            disabled={capturing}
            className="flex items-center justify-center gap-2 text-sm font-medium py-2.5 px-4 rounded transition disabled:opacity-60"
            style={{ background: ACCENT, color: "#070A14" }}
          >
            {capturing ? <Loader2 size={15} className="animate-spin" /> : <UserPlus size={15} />}
            {capturing ? "Capturing…" : "Run campaign · capture leads"}
          </button>
        </div>

        <p className="text-muted text-sm mb-4 max-w-2xl">
          Simulates a campaign bringing in leads. Each lands in your CRM with an AI lead score — then the engine drafts a personalized play to convert it.
        </p>

        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          {leads.length === 0 && (
            <div className="p-8 text-center text-muted text-sm">
              No leads yet. Click <b className="text-text">Run campaign</b> to capture your first batch.
            </div>
          )}
          {leads.map((l) => {
            const conv = conversions[l.id];
            const isOpen = openId === l.id;
            return (
              <div key={l.id} className="border-b border-border last:border-0">
                <div className="flex items-center gap-3 px-4 py-3">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{l.contact}</div>
                    <div className="text-xs text-muted truncate">{l.company} · {l.owner || l.stage}</div>
                  </div>
                  <div className="text-xs font-mono text-muted hidden sm:block">{inr(l.deal_size_inr)}</div>
                  <div className="flex items-center gap-1.5 w-16 justify-end">
                    <span className="text-sm font-mono font-bold" style={{ color: scoreColor(l.score) }}>{l.score}</span>
                    <span className="text-[10px] text-muted">/100</span>
                  </div>
                  <button
                    onClick={() => (isOpen ? setOpenId(null) : convert(l.id))}
                    className="flex items-center gap-1.5 text-xs font-medium py-1.5 px-3 rounded border transition"
                    style={{ borderColor: `${ACCENT}55`, color: ACCENT }}
                  >
                    {convertingId === l.id ? <Loader2 size={13} className="animate-spin" /> : <MessageSquare size={13} />}
                    Convert
                    <ChevronDown size={13} className={`transition ${isOpen ? "rotate-180" : ""}`} />
                  </button>
                </div>

                {isOpen && (
                  <div className="px-4 pb-4 pt-1">
                    {convertingId === l.id && !conv && (
                      <div className="text-xs text-muted flex items-center gap-2 py-2">
                        <Loader2 size={13} className="animate-spin" /> The engine is drafting a conversion play…
                      </div>
                    )}
                    {conv && (
                      <div className="bg-surface2 border border-border rounded-lg p-3.5 flex flex-col gap-3">
                        <div>
                          <div className="text-[10px] uppercase tracking-widest font-mono mb-1" style={{ color: ACCENT }}>Channel</div>
                          <div className="text-sm">{conv.channel}</div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase tracking-widest font-mono mb-1" style={{ color: ACCENT }}>Ready-to-send message</div>
                          <div className="text-sm text-text/90 leading-relaxed bg-bg/50 border border-border rounded p-2.5">{conv.message}</div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase tracking-widest font-mono mb-1" style={{ color: ACCENT }}>Next step</div>
                          <div className="text-sm text-muted">{conv.next_step}</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
