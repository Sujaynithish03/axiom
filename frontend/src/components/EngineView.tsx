import { useEffect } from "react";
import { useAxiom } from "../store";
import { engineByKey } from "../engines";
import EngineChat from "./EngineChat";
import { Sparkles, Loader2, RefreshCw } from "lucide-react";

const humanize = (k: string) =>
  k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function isPrimitive(v: any) {
  return v === null || ["string", "number", "boolean"].includes(typeof v);
}

/** Renders one object as a stack of label → value blocks. */
function ObjectBlock({ obj, accent }: { obj: Record<string, any>; accent: string }) {
  return (
    <div className="flex flex-col gap-4">
      {Object.entries(obj).map(([k, v]) => (
        <div key={k}>
          <div
            className="text-[10px] uppercase tracking-widest font-mono mb-1.5"
            style={{ color: accent }}
          >
            {humanize(k)}
          </div>
          <Value v={v} accent={accent} />
        </div>
      ))}
    </div>
  );
}

/** Recursive value renderer — copes with whatever shape the model returns. */
function Value({ v, accent }: { v: any; accent: string }): JSX.Element {
  if (isPrimitive(v)) {
    return <p className="text-sm text-text/90 leading-relaxed">{String(v ?? "—")}</p>;
  }
  if (Array.isArray(v)) {
    if (v.every(isPrimitive)) {
      return (
        <ul className="flex flex-col gap-1.5">
          {v.map((item, i) => (
            <li key={i} className="text-sm text-text/90 flex gap-2">
              <span style={{ color: accent }} className="mt-0.5">▸</span>
              <span>{String(item)}</span>
            </li>
          ))}
        </ul>
      );
    }
    // array of objects → cards
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {v.map((item, i) => (
          <div key={i} className="bg-surface2 border border-border rounded-lg p-3.5">
            {isPrimitive(item) ? (
              <p className="text-sm text-text/90">{String(item)}</p>
            ) : (
              <ObjectBlock obj={item} accent={accent} />
            )}
          </div>
        ))}
      </div>
    );
  }
  // nested object
  return (
    <div className="bg-surface2 border border-border rounded-lg p-3.5">
      <ObjectBlock obj={v} accent={accent} />
    </div>
  );
}

export default function EngineView({ engineKey }: { engineKey: string }) {
  const def = engineByKey(engineKey)!;
  const { engineOutputs, engineBusy, fetchEngine, runEngine } = useAxiom();
  const output = engineOutputs[engineKey];
  const busy = !!engineBusy[engineKey];
  const Icon = def.icon;

  useEffect(() => {
    fetchEngine(engineKey);
  }, [engineKey]);

  const failed = output && output.error;
  const hasOutput = output && !output.error;

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
              Engine · AI-driven
            </div>
            <h1 className="text-xl sm:text-2xl font-bold mt-0.5">{def.title}</h1>
            <p className="text-muted text-sm mt-1 max-w-xl">{def.subtitle}</p>
          </div>
        </div>
        <button
          onClick={() => runEngine(engineKey)}
          disabled={busy}
          className="flex items-center justify-center gap-2 font-medium text-sm py-2.5 px-4 rounded transition disabled:opacity-60 shrink-0"
          style={{ background: def.color, color: "#070A14" }}
        >
          {busy ? <Loader2 size={15} className="animate-spin" /> : hasOutput ? <RefreshCw size={14} /> : <Sparkles size={14} />}
          {busy ? "Generating…" : hasOutput ? "Regenerate" : def.cta}
        </button>
      </header>

      {busy && !hasOutput && (
        <div className="bg-surface border border-border rounded-lg p-8 text-center">
          <Loader2 size={22} className="animate-spin mx-auto mb-3" style={{ color: def.color }} />
          <div className="text-muted text-sm">
            The {def.label} Engine is thinking on your business… (local model, ~30–60s)
          </div>
        </div>
      )}

      {failed && (
        <div className="bg-surface border border-danger/40 rounded-lg p-5 text-sm">
          <div className="text-danger font-medium mb-1">The model returned malformed output.</div>
          <div className="text-muted">Hit “Regenerate” — small local models occasionally slip. It usually succeeds on the next run.</div>
        </div>
      )}

      {!busy && !output && (
        <div className="bg-surface border border-border rounded-lg p-10 text-center">
          <Icon size={30} style={{ color: def.color }} className="mx-auto mb-3 opacity-70" />
          <div className="text-sm text-muted max-w-md mx-auto">
            No plan yet. Click <b className="text-text">{def.cta}</b> and the {def.label} Engine will
            generate one from your live business data.
          </div>
        </div>
      )}

      {hasOutput && (
        <div className="bg-surface border border-border rounded-xl p-5 sm:p-6">
          <ObjectBlock obj={output} accent={def.color} />
        </div>
      )}

      {/* Dedicated AI chatbot for this engine — can rewrite the plan above */}
      {hasOutput && <EngineChat engineKey={engineKey} accent={def.color} label={def.label} />}
    </div>
  );
}
