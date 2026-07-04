import { useAxiom } from "../store";
import { Activity, LayoutDashboard, MessageSquare, Users, Rocket } from "lucide-react";

type View = "boardroom" | "dashboard" | "copilot" | "onboarding";

export default function Layout({
  view,
  setView,
  children,
}: {
  view: View;
  setView: (v: View) => void;
  children: React.ReactNode;
}) {
  const { connected, business, runBoardroom } = useAxiom();

  const nav: { key: View; label: string; icon: any }[] = [
    { key: "boardroom", label: "Boardroom", icon: Users },
    { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { key: "copilot", label: "Copilot", icon: MessageSquare },
    { key: "onboarding", label: "Business", icon: Activity },
  ];

  return (
    <div className="flex h-screen bg-bg text-text">
      <aside className="w-56 border-r border-border bg-surface/60 flex flex-col">
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-mint pulse-ring" />
            <div className="font-mono text-mint font-bold tracking-wider text-sm">
              AXIOM
            </div>
          </div>
          <div className="text-xs text-muted mt-1 font-mono">
            {business?.name || "—"}
          </div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5">
          {nav.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded transition
                ${view === key
                  ? "bg-mint/10 text-mint border-l-2 border-mint"
                  : "text-muted hover:text-text hover:bg-surface2"}`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </nav>

        <div className="p-3 border-t border-border space-y-2">
          <button
            onClick={runBoardroom}
            className="w-full flex items-center justify-center gap-2 bg-mint text-bg font-medium text-sm py-2.5 rounded hover:bg-mint/90 transition"
          >
            <Rocket size={14} />
            Start day
          </button>
          <div className="flex items-center gap-2 text-xs text-muted font-mono">
            <div className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-mint" : "bg-danger"}`} />
            {connected ? "boardroom live" : "reconnecting…"}
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
