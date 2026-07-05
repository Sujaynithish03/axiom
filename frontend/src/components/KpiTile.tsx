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

  const glow =
    tone === "positive" ? "#00E5A0" :
    tone === "negative" ? "#FF6B6B" :
    tone === "warning" ? "#FFB454" :
    "#2A3555";

  return (
    <div
      className="group relative overflow-hidden rounded-lg p-4 border border-border/80 bg-gradient-to-br from-surface to-[#0a1020] hover-lift"
      style={{ borderLeft: `2px solid ${glow}` }}
    >
      {/* faint accent glow that intensifies on hover */}
      <div
        className="pointer-events-none absolute -top-10 -right-10 w-24 h-24 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity"
        style={{ background: glow }}
      />
      <div className="relative">
        <div className="text-[10px] uppercase tracking-widest text-muted font-mono">{label}</div>
        <div className="mt-1.5 flex items-baseline gap-1">
          <div
            className={`font-mono font-bold text-text tabular-nums ${size === "lg" ? "text-3xl" : "text-2xl"}`}
            style={size === "lg" ? { textShadow: `0 0 22px ${glow}55` } : undefined}
          >
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
    </div>
  );
}
