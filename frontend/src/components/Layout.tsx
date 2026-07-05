import { useAxiom } from "../store";
import { LayoutDashboard, MessageSquare, Users, Rocket, Building2, ShieldCheck } from "lucide-react";
import { ENGINES } from "../engines";

interface NavItem { key: string; label: string; icon: any; color?: string; }

export default function Layout({
  view,
  setView,
  children,
}: {
  view: string;
  setView: (v: string) => void;
  children: React.ReactNode;
}) {
  const { connected, business, runBoardroom } = useAxiom();

  const overview: NavItem[] = [
    { key: "boardroom", label: "Command Center", icon: Users },
    { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  ];
  const engineNav: NavItem[] = ENGINES.map((e) => ({ key: e.key, label: e.label, icon: e.icon, color: e.color }));
  const extras: NavItem[] = [
    { key: "copilot", label: "Copilot", icon: MessageSquare },
    { key: "security", label: "Security", icon: ShieldCheck },
    { key: "onboarding", label: "Business", icon: Building2 },
  ];

  const NavButton = ({ item }: { item: NavItem }) => {
    const active = view === item.key;
    const Icon = item.icon;
    return (
      <button
        onClick={() => setView(item.key)}
        className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded transition
          ${active ? "bg-mint/10 text-mint border-l-2 border-mint" : "text-muted hover:text-text hover:bg-surface2"}`}
      >
        <Icon size={16} style={item.color && !active ? { color: item.color } : undefined} />
        {item.label}
      </button>
    );
  };

  const SectionLabel = ({ children }: { children: React.ReactNode }) => (
    <div className="px-3 pt-4 pb-1.5 text-[10px] uppercase tracking-widest text-muted/70 font-mono">
      {children}
    </div>
  );

  // Mobile: a flat, horizontally-scrollable tab bar of the most-used views.
  const mobileNav: NavItem[] = [overview[0], ...engineNav, overview[1], extras[0]];

  return (
    <div className="flex flex-col md:flex-row h-screen bg-bg text-text">
      {/* Mobile top bar */}
      <header className="md:hidden flex items-center justify-between px-4 h-14 border-b border-border bg-surface/60 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full bg-mint pulse-ring shrink-0" />
          <div className="font-mono text-mint font-bold tracking-wider text-sm">AXIOM</div>
          <div className="text-xs text-muted font-mono truncate ml-1">{business?.name || "—"}</div>
        </div>
        <button
          onClick={runBoardroom}
          className="flex items-center gap-1.5 bg-mint text-bg font-medium text-xs py-2 px-3 rounded hover:bg-mint/90 transition shrink-0"
        >
          <Rocket size={13} /> Start day
        </button>
      </header>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-60 border-r border-border bg-surface/60 flex-col shrink-0">
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-mint pulse-ring" />
            <div className="font-mono text-mint font-bold tracking-wider text-sm">AXIOM OS</div>
          </div>
          <div className="text-xs text-muted mt-1 font-mono truncate">{business?.name || "—"}</div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          <SectionLabel>Overview</SectionLabel>
          {overview.map((i) => <NavButton key={i.key} item={i} />)}
          <SectionLabel>Engines</SectionLabel>
          {engineNav.map((i) => <NavButton key={i.key} item={i} />)}
          <SectionLabel>More</SectionLabel>
          {extras.map((i) => <NavButton key={i.key} item={i} />)}
        </nav>

        <div className="p-3 border-t border-border space-y-2">
          <button
            onClick={runBoardroom}
            className="w-full flex items-center justify-center gap-2 bg-mint text-bg font-medium text-sm py-2.5 rounded hover:bg-mint/90 transition"
          >
            <Rocket size={14} /> Start day
          </button>
          <div className="flex items-center gap-2 text-xs text-muted font-mono">
            <div className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-mint" : "bg-danger"}`} />
            {connected ? "boardroom live" : "reconnecting…"}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto pb-16 md:pb-0">{children}</main>

      {/* Mobile bottom tab bar — horizontally scrollable */}
      <nav className="md:hidden fixed bottom-0 inset-x-0 h-16 border-t border-border bg-surface/95 backdrop-blur flex items-stretch overflow-x-auto z-20">
        {mobileNav.map((item) => {
          const active = view === item.key;
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              onClick={() => setView(item.key)}
              className={`flex-none w-[76px] flex flex-col items-center justify-center gap-1 text-[9.5px] font-mono transition
                ${active ? "text-mint" : "text-muted hover:text-text"}`}
            >
              <Icon size={17} />
              {item.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
