import { useState, useRef, useEffect } from "react";
import { useAxiom } from "../store";
import { Send, Loader2, MessageSquare, CheckCircle2 } from "lucide-react";

interface Msg { role: "user" | "assistant"; content: string; updated?: boolean; }

const SUGGESTIONS: Record<string, string[]> = {
  strategy: ["Explain this positioning", "Make the pricing 20% cheaper", "Target a younger segment"],
  marketing: ["Shift more budget to WhatsApp", "Make the big idea bolder", "Add an influencer channel"],
  leadgen: ["Focus on physical events", "Rewrite the WhatsApp hook", "Target tier-2 cities"],
  sales: ["Make outreach more urgent", "Add a discovery-call stage", "Tighten the funnel targets"],
  analytics: ["Forecast a slower month", "Focus the roadmap on retention", "What's my biggest risk?"],
  success: ["Prioritize the at-risk segment", "Make the playbook proactive", "Rewrite the chatbot greeting"],
};

export default function EngineChat({ engineKey, accent, label }: { engineKey: string; accent: string; label: string; }) {
  const { chatEngine } = useAxiom();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, busy]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const { reply, updated } = await chatEngine(engineKey, q);
      setMsgs((m) => [...m, { role: "assistant", content: reply, updated }]);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", content: "Something went wrong — try again." }]);
    } finally {
      setBusy(false);
    }
  };

  const suggestions = SUGGESTIONS[engineKey] || ["Explain this plan", "Make it more aggressive"];

  return (
    <div className="mt-4 bg-surface border border-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <MessageSquare size={15} style={{ color: accent }} />
        <div className="text-sm font-semibold">Ask the {label} Engine</div>
        <div className="text-[10px] uppercase tracking-widest text-muted font-mono ml-auto">
          chat can rewrite the plan
        </div>
      </div>

      <div ref={scrollRef} className="max-h-72 overflow-y-auto p-4 space-y-3">
        {msgs.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="text-xs text-left px-3 py-2 rounded-lg border border-border bg-surface2 hover:border-current transition"
                style={{ color: accent }}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] p-3 rounded-lg text-sm whitespace-pre-wrap ${
                m.role === "user" ? "text-bg" : "bg-surface2 border border-border text-text/90"
              }`}
              style={m.role === "user" ? { background: accent } : undefined}
            >
              {m.content}
              {m.updated && (
                <div className="flex items-center gap-1.5 mt-2 text-[11px] font-mono" style={{ color: accent }}>
                  <CheckCircle2 size={13} /> Plan updated above ↑
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-xs text-muted">
            <Loader2 size={13} className="animate-spin" /> The {label} Engine is thinking…
          </div>
        )}
      </div>

      <div className="border-t border-border p-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={`Ask or tell the ${label} Engine to change something…`}
          disabled={busy}
          className="flex-1 bg-surface2 border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-current"
          style={{ caretColor: accent }}
        />
        <button
          onClick={() => send()}
          disabled={busy || !input.trim()}
          className="font-medium text-sm py-2.5 px-4 rounded-lg transition disabled:opacity-50"
          style={{ background: accent, color: "#070A14" }}
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
