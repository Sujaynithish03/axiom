import { useAxiom } from "../store";
import type { Recommendation } from "../types";
import { Check, X, Zap } from "lucide-react";

const AGENT_COLOR: Record<string, string> = {
  ceo: "text-mint",
  marketing: "text-marketing",
  sales: "text-sales",
  finance: "text-finance",
  strategy: "text-strategy",
  learning: "text-learning",
};

export default function RecommendationCard({ rec }: { rec: Recommendation }) {
  const { decide, execute } = useAxiom();
  const isPending = rec.status === "pending";
  const isDone = rec.status !== "pending";

  return (
    <div className={`bg-surface border border-border rounded p-4 ${isDone ? "opacity-60" : ""}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] uppercase tracking-widest font-mono ${AGENT_COLOR[rec.agent] || "text-muted"}`}>
              {rec.agent}
            </span>
            <span className="text-[10px] text-muted font-mono">
              conf {(rec.confidence * 100).toFixed(0)}%
            </span>
            {rec.predicted_impact_inr > 0 && (
              <span className="text-[10px] text-mint font-mono">
                +₹{(rec.predicted_impact_inr / 100000).toFixed(1)}L predicted
              </span>
            )}
            {rec.status !== "pending" && (
              <span className={`text-[10px] font-mono ml-auto uppercase tracking-widest
                ${rec.status === "approved" ? "text-mint" :
                  rec.status === "executed" ? "text-mint" : "text-muted"}`}>
                {rec.status}
              </span>
            )}
          </div>
          <div className="font-medium text-text">{rec.title}</div>
          <div className="text-sm text-muted mt-1">{rec.body}</div>
        </div>

        {isPending && (
          <div className="flex gap-1 shrink-0">
            <button
              onClick={() => decide(rec.id, "approved")}
              className="flex items-center gap-1 bg-mint/10 hover:bg-mint/20 text-mint text-xs font-mono py-1.5 px-2.5 rounded transition"
            >
              <Check size={12} /> Approve
            </button>
            <button
              onClick={() => execute(rec.id)}
              className="flex items-center gap-1 bg-mint text-bg text-xs font-mono py-1.5 px-2.5 rounded hover:bg-mint/90 transition"
            >
              <Zap size={12} /> Execute
            </button>
            <button
              onClick={() => decide(rec.id, "dismissed")}
              className="flex items-center gap-1 bg-surface2 hover:bg-border text-muted text-xs font-mono py-1.5 px-2.5 rounded transition"
            >
              <X size={12} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
