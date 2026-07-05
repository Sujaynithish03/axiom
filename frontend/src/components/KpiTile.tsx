import { useEffect, useRef, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

/** Smoothly animate a number toward its latest value (the "count up" effect). */
function useCountUp(target: number, active: boolean) {
  const [val, setVal] = useState(target);
  const from = useRef(target);
  const raf = useRef<number>();

  useEffect(() => {
    if (!active) { setVal(target); return; }
    const start = performance.now();
    const dur = 700;
    const a = from.current;
    const b = target;
    const tick = (now: number) => {
      const t = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setVal(a + (b - a) * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
      else from.current = b;
    };
    raf.current = requestAnimationFrame(tick);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [target, active]);

  return val;
}

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
  const isNum = typeof value === "number";
  const animated = useCountUp(isNum ? (value as number) : 0, isNum);
  const decimals = isNum && !Number.isInteger(value as number) ? 1 : 0;
  const display = isNum ? animated.toFixed(decimals) : value;

  const borderTone =
    tone === "positive" ? "border-l-mint" :
    tone === "negative" ? "border-l-danger" :
    tone === "warning" ? "border-l-warn" :
    "border-l-border";

  return (
    <div className={`bg-surface border border-border ${borderTone} border-l-2 p-4 rounded`}>
      <div className="text-[10px] uppercase tracking-widest text-muted font-mono">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <div className={`font-mono font-bold text-text tabular-nums ${size === "lg" ? "text-3xl" : "text-2xl"}`}>
          {display}
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
