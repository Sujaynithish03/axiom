import { useEffect, useState } from "react";
import { ShieldCheck, EyeOff, ShieldAlert, ScanLine, FileLock2 } from "lucide-react";

interface Entry {
  id: number; ts: string; action: string; input_hash: string; output_hash: string;
  input_chars: number; output_chars: number; pii_redacted: number; secrets_blocked: number; status: string;
}
interface Audit { totals: { calls: number; pii_redacted: number; secrets_blocked: number }; entries: Entry[]; }

const LAYERS = [
  { icon: EyeOff, title: "PII redaction", body: "Emails, phones, PAN/GST and card numbers are masked to typed placeholders before any text reaches the model. Real personal data never leaves the boundary." },
  { icon: ShieldAlert, title: "Injection defense", body: "Untrusted user text is fenced in <untrusted_content> tags and blatant override phrases (\"ignore previous instructions\") are neutralised. The model is told to treat it as data, not commands." },
  { icon: ScanLine, title: "Output filtering", body: "Every model response is scanned for leaked secrets — OpenAI/AWS/GitHub/Slack/Google key patterns are scrubbed to [REDACTED_SECRET] before returning to the user." },
  { icon: FileLock2, title: "Audit log", body: "Every LLM call is recorded append-only with SHA-256 hashes and counts — never raw content — so activity is provable without storing sensitive data." },
];

const ACCENT = "#5EA0FF";

export default function SecurityView() {
  const [audit, setAudit] = useState<Audit | null>(null);

  const load = () => fetch("/api/audit?limit=50").then((r) => r.json()).then(setAudit).catch(() => {});
  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const t = audit?.totals;

  return (
    <div className="p-4 sm:p-6 max-w-[1100px] mx-auto">
      <header className="flex items-start gap-3 mb-6">
        <div className="w-11 h-11 rounded-lg flex items-center justify-center shrink-0"
             style={{ background: `${ACCENT}1A`, border: `1px solid ${ACCENT}55` }}>
          <ShieldCheck size={22} style={{ color: ACCENT }} />
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted font-mono">Security · LLM boundary</div>
          <h1 className="text-xl sm:text-2xl font-bold mt-0.5">Data protection & audit</h1>
          <p className="text-muted text-sm mt-1 max-w-xl">
            Four protections wrap every AI call. Nothing sensitive reaches the model, and everything is logged.
          </p>
        </div>
      </header>

      {/* Live totals */}
      <section className="grid grid-cols-3 gap-3 mb-6">
        <Stat label="AI calls audited" value={t?.calls ?? 0} />
        <Stat label="PII items masked" value={t?.pii_redacted ?? 0} accent="#00E5A0" />
        <Stat label="Secrets blocked" value={t?.secrets_blocked ?? 0} accent="#FF6B6B" />
      </section>

      {/* The four layers */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
        {LAYERS.map((l) => {
          const Icon = l.icon;
          return (
            <div key={l.title} className="bg-surface border border-border rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Icon size={16} style={{ color: ACCENT }} />
                <div className="font-semibold text-sm">{l.title}</div>
              </div>
              <p className="text-xs text-muted leading-relaxed">{l.body}</p>
            </div>
          );
        })}
      </section>

      <div className="text-[11px] text-muted/80 mb-4 font-mono">
        Note: multi-tenant Row-Level Security &amp; JWT scoping apply to the hosted multi-business deployment.
        This local single-tenant build focuses on the LLM-boundary protections above — where the real leak risk sits.
      </div>

      {/* Audit log */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <FileLock2 size={14} style={{ color: ACCENT }} />
          <h2 className="text-sm font-mono uppercase tracking-widest text-muted">Audit log · append-only</h2>
        </div>
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[560px]">
              <thead>
                <tr className="text-muted font-mono uppercase tracking-widest text-[10px]">
                  <th className="text-left p-3">Time</th>
                  <th className="text-left p-3">Action</th>
                  <th className="text-left p-3">Input hash</th>
                  <th className="text-right p-3">PII</th>
                  <th className="text-right p-3">Secrets</th>
                  <th className="text-right p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {(!audit || audit.entries.length === 0) && (
                  <tr><td colSpan={6} className="p-6 text-center text-muted">
                    No AI calls yet. Use the Copilot or an engine chat, then watch this fill.
                  </td></tr>
                )}
                {audit?.entries.map((e) => (
                  <tr key={e.id} className="border-t border-border font-mono">
                    <td className="p-3 text-muted whitespace-nowrap">{new Date(e.ts + "Z").toLocaleTimeString()}</td>
                    <td className="p-3" style={{ color: ACCENT }}>{e.action}</td>
                    <td className="p-3 text-muted">{e.input_hash}</td>
                    <td className="p-3 text-right" style={{ color: e.pii_redacted ? "#00E5A0" : "#8B93A7" }}>{e.pii_redacted}</td>
                    <td className="p-3 text-right" style={{ color: e.secrets_blocked ? "#FF6B6B" : "#8B93A7" }}>{e.secrets_blocked}</td>
                    <td className="p-3 text-right text-mint">{e.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, accent = "#E8ECF5" }: { label: string; value: number; accent?: string }) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <div className="text-[10px] uppercase tracking-widest text-muted font-mono">{label}</div>
      <div className="text-2xl font-mono font-bold mt-1 tabular-nums" style={{ color: accent }}>{value}</div>
    </div>
  );
}
