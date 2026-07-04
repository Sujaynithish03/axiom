import { TrendingUp, TrendingDown } from "lucide-react";

export default function KpiTile({
  label,
  value,
  unit = "",
  delta,
  tone = "neutral",
  size = "md",
}: {
  label: string;
  value: string | number;
  unit?: string;
  delta?: number | null;
  tone?: "positive" | "negative" | "warning" | "neutral";
  size?: "md" | "lg";
}) {
  const borderTone =
    tone === "positive" ? "border-l-mint" :
    tone === "negative" ? "border-l-danger" :
    tone === "warning" ? "border-l-warn" :
    "border-l-border";

  return (
    <div className={`bg-surface border border-border ${borderTone} border-l-2 p-4 rounded`}>
      <div className="text-[10px] uppercase tracking-widest text-muted font-mono">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <div className={`font-mono font-bold text-text ${size === "lg" ? "text-3xl" : "text-2xl"}`}>
          {value}
        </div>
        {unit && <div className="text-xs text-muted font-mono">{unit}</div>}
      </div>
      {delta !== undefined && delta !== null && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-mono
          ${delta > 0 ? "text-mint" : delta < 0 ? "text-danger" : "text-muted"}`}>
          {delta > 0 ? <TrendingUp size={12} /> : delta < 0 ? <TrendingDown size={12} /> : null}
          {delta > 0 ? "+" : ""}{delta.toFixed(1)}%
        </div>
      )}
    </div>
  );
}
