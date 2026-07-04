import { create } from "zustand";
import type { AgentEventMsg, Kpis, Recommendation, Business } from "./types";

interface State {
  connected: boolean;
  events: AgentEventMsg[]; // most recent last
  kpis: Kpis | null;
  history: any[];
  recommendations: Recommendation[];
  business: Business | null;
  executiveSummary: string | null; // CEO morning briefing
  agentStreams: Record<string, string>; // running text per agent
  agentPhase: Record<string, string>; // last kind per agent
  agentPulse: Record<string, string>; // live heartbeat line per agent (idle)
  currentPhase: string;
  engineOutputs: Record<string, any>; // latest payload per engine
  engineBusy: Record<string, boolean>; // is an engine currently generating
  connect: () => void;
  fetchAll: () => Promise<void>;
  runBoardroom: () => Promise<void>;
  decide: (id: number, action: "approved" | "dismissed") => Promise<void>;
  execute: (id: number) => Promise<void>;
  saveBusiness: (b: Partial<Business>) => Promise<void>;
  fetchEngine: (key: string) => Promise<void>;
  runEngine: (key: string) => Promise<void>;
}

const AGENTS = ["ceo", "marketing", "sales", "finance", "strategy", "learning"];

export const useAxiom = create<State>((set, get) => ({
  connected: false,
  events: [],
  kpis: null,
  history: [],
  recommendations: [],
  business: null,
  executiveSummary: null,
  agentStreams: Object.fromEntries(AGENTS.map((a) => [a, ""])),
  agentPhase: {},
  agentPulse: {},
  currentPhase: "",
  engineOutputs: {},
  engineBusy: {},

  connect: () => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/ws`);
    ws.onopen = () => set({ connected: true });
    ws.onclose = () => {
      set({ connected: false });
      setTimeout(() => get().connect(), 2000); // auto-reconnect
    };
    ws.onmessage = (msg) => {
      try {
        const e: AgentEventMsg = JSON.parse(msg.data);

        // Live heartbeat pulses drive a per-agent "monitoring" line without
        // cluttering the real event log.
        if (e.kind === "pulse") {
          set({ agentPulse: { ...get().agentPulse, [e.agent]: e.content } });
          return;
        }

        const events = [...get().events, e].slice(-300);
        const patch: Partial<State> = { events };

        if (e.kind === "phase") {
          patch.currentPhase = e.content;
        }

        if (AGENTS.includes(e.agent)) {
          const streams = { ...get().agentStreams };
          if (e.kind === "thinking") {
            streams[e.agent] = (streams[e.agent] || "") + e.content;
          } else if (e.kind === "done") {
            // Keep the last stream visible
          } else if (e.kind === "insight" || e.kind === "recommendation" || e.kind === "debate") {
            streams[e.agent] = e.content;
          }
          patch.agentStreams = streams;
          patch.agentPhase = { ...get().agentPhase, [e.agent]: e.kind };
        }

        if (e.kind === "done" && e.agent === "learning") {
          // Boardroom finished — refresh KPIs + recs
          get().fetchAll();
        }
        set(patch);
      } catch (err) {
        console.error("ws msg parse error", err);
      }
    };
  },

  fetchAll: async () => {
    const [kpis, hist, recs, biz, brief] = await Promise.all([
      fetch("/api/kpis").then((r) => r.json()),
      fetch("/api/kpis/history?days=30").then((r) => r.json()),
      fetch("/api/recommendations?limit=30").then((r) => r.json()),
      fetch("/api/business").then((r) => r.json()),
      fetch("/api/briefing").then((r) => r.json()).catch(() => ({ briefing: null })),
    ]);
    set({
      kpis, history: hist, recommendations: recs, business: biz,
      executiveSummary: brief?.briefing ?? null,
    });
  },

  runBoardroom: async () => {
    // Reset agent streams
    set({ agentStreams: Object.fromEntries(AGENTS.map((a) => [a, ""])), agentPhase: {} });
    await fetch("/api/boardroom/run", { method: "POST" });
  },

  decide: async (id, action) => {
    await fetch(`/api/recommendations/${id}/decide`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action }),
    });
    await get().fetchAll();
  },

  execute: async (id) => {
    await fetch(`/api/recommendations/${id}/execute`, { method: "POST" });
    await get().fetchAll();
  },

  saveBusiness: async (b) => {
    const merged = { ...(get().business || {}), ...b };
    const res = await fetch("/api/business", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(merged),
    });
    const saved = await res.json();
    set({ business: saved });
  },

  fetchEngine: async (key) => {
    try {
      const r = await fetch(`/api/engines/${key}`).then((x) => x.json());
      if (r?.payload) {
        set({ engineOutputs: { ...get().engineOutputs, [key]: r.payload } });
      }
    } catch {}
  },

  runEngine: async (key) => {
    set({ engineBusy: { ...get().engineBusy, [key]: true } });
    try {
      const r = await fetch(`/api/engines/${key}/run`, { method: "POST" }).then((x) => x.json());
      if (r?.payload) {
        set({ engineOutputs: { ...get().engineOutputs, [key]: r.payload } });
      }
    } catch {
      // leave previous output in place
    } finally {
      set({ engineBusy: { ...get().engineBusy, [key]: false } });
    }
  },
}));
