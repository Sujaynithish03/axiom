import { useAxiom } from "../store";
import { motion, AnimatePresence } from "framer-motion";
import { useMemo } from "react";
import { Rocket, Terminal } from "lucide-react";

const AGENT_META: Record<string, { display: string; role: string; color: string }> = {
  ceo:       { display: "CEO",       role: "Chief of Staff",         color: "ceo" },
  marketing: { display: "Marketing", role: "Growth & campaigns",     color: "marketing" },
  sales:     { display: "Sales",     role: "Pipeline & leads",       color: "sales" },
  finance:   { display: "Finance",   role: "Cashflow & runway",      color: "finance" },
  strategy:  { display: "Strategy",  role: "Market & competitors",   color: "strategy" },
  learning:  { display: "Learning",  role: "Feedback loop",          color: "learning" },
};

export default function Boardroom() {
  const { events, agentStreams, agentPhase, currentPhase, runBoardroom } = useAxiom();

  const recentEvents = useMemo(() => events.slice(-40).reverse(), [events]);

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <header className="flex items-start justify-between mb-6">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted font-mono">
            The boardroom
          </div>
          <h1 className="text-2xl font-bold mt-1">Your AI executives, thinking now</h1>
          <p className="text-muted text-sm mt-1">
            Six agents run in parallel. Every token they generate streams here live.
          </p>
        </div>
        <button
          onClick={runBoardroom}
          className="flex items-center gap-2 bg-mint text-bg font-medium text-sm py-2 px-4 rounded hover:bg-mint/90 transition"
        >
          <Rocket size={14} /> Run boardroom
        </button>
      </header>

      {currentPhase && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          key={currentPhase}
          className="mb-4 px-4 py-2.5 bg-surface border-l-2 border-mint rounded text-sm font-mono text-text/90"
        >
          {currentPhase}
        </motion.div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(AGENT_META).map(([key, meta]) => {
          const stream = agentStreams[key] || "";
          const phase = agentPhase[key];
          const isActive = phase && phase !== "done";
          return (
            <motion.div
              key={key}
              layout
              className={`bg-surface border border-border rounded p-4 h-64 flex flex-col ${
                isActive ? "border-mint/40" : ""
              }`}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${isActive ? "pulse-ring" : ""}`}
                  style={{ background: `var(--tw-color-${meta.color}, #00E5A0)` }}
                />
                <div className="font-mono text-sm font-bold" style={{ color: `var(--tw-color-${meta.color})` }}>
                  {meta.display}
                </div>
                <div className="text-xs text-muted ml-1">— {meta.role}</div>
                {phase && (
                  <div className="ml-auto text-[10px] uppercase tracking-widest text-muted font-mono">
                    {phase}
                  </div>
                )}
              </div>
              <div className="flex-1 overflow-y-auto text-xs font-mono text-text/80 leading-relaxed whitespace-pre-wrap">
                {stream || <span className="text-muted italic">Idle. Waiting for boardroom trigger…</span>}
                {isActive && <span className="cursor" />}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-8">
        <div className="flex items-center gap-2 mb-3">
          <Terminal size={14} className="text-mint" />
          <h2 className="text-sm font-mono uppercase tracking-widest text-muted">Event log</h2>
        </div>
        <div className="bg-surface border border-border rounded h-64 overflow-y-auto p-3 font-mono text-xs">
          <AnimatePresence initial={false}>
            {recentEvents.map((e, i) => (
              <motion.div
                key={e.id || `${e.ts}-${i}`}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-2 py-0.5"
              >
                <span className="text-muted shrink-0">
                  {e.ts ? new Date(e.ts).toLocaleTimeString() : "--:--"}
                </span>
                <span className="text-mint shrink-0 w-16 truncate">{e.agent}</span>
                <span className="text-muted shrink-0 w-20">{e.kind}</span>
                <span className="text-text/80 flex-1 truncate">{e.content}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
