import { useState, useRef, useEffect } from "react";
import { Send, Sparkles } from "lucide-react";

interface Msg { role: "user" | "assistant"; content: string; }

const SUGGESTIONS = [
  "What's my biggest risk this week?",
  "Should I match the competitor's price cut?",
  "Where should I put my next ₹5L of ad spend?",
  "Explain my burn multiple.",
];

export default function Copilot() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || streaming) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: q }, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const res = await fetch("/api/copilot/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: q }),
      });
      if (!res.body) throw new Error("no body");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") continue;
          try {
            const { token } = JSON.parse(data);
            if (token) {
              setMsgs((m) => {
                const copy = [...m];
                copy[copy.length - 1] = {
                  role: "assistant",
                  content: copy[copy.length - 1].content + token,
                };
                return copy;
              });
            }
          } catch {}
        }
      }
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto h-full flex flex-col">
      <header className="mb-4">
        <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Copilot</div>
        <h1 className="text-2xl font-bold mt-1 flex items-center gap-2">
          <Sparkles className="text-mint" size={22} /> Ask your AI team
        </h1>
        <p className="text-muted text-sm mt-1">
          Grounded in your live KPIs and the recommendations your agents just produced.
        </p>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pb-4">
        {msgs.length === 0 && (
          <div className="grid grid-cols-2 gap-2 mt-4">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="text-left text-sm p-3 bg-surface border border-border rounded hover:border-mint/40 hover:bg-surface2 transition"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] p-3 rounded text-sm whitespace-pre-wrap
              ${m.role === "user"
                ? "bg-mint/10 border-l-2 border-mint text-text"
                : "bg-surface border border-border text-text/90"}`}>
              {m.content}
              {m.role === "assistant" && streaming && i === msgs.length - 1 && <span className="cursor" />}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-border pt-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask your executive team…"
            className="flex-1 bg-surface border border-border rounded px-3 py-2.5 text-sm focus:outline-none focus:border-mint/50"
            disabled={streaming}
          />
          <button
            onClick={() => send()}
            disabled={streaming || !input.trim()}
            className="bg-mint text-bg font-medium text-sm py-2.5 px-4 rounded hover:bg-mint/90 transition disabled:opacity-50"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
