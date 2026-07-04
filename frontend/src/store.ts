import { create } from "zustand";
import type { AgentEventMsg, Kpis, Recommendation, Business } from "./types";

interface State {
  connected: boolean;
  events: AgentEventMsg[]; // most recent last
  kpis: Kpis | null;
  history: any[];
  recommendations: Recommendation[];
  business: Business | null;
  agentStreams: Record<string, string>; // running text per agent
  agentPhase: Record<string, string>; // last kind per agent
  currentPhase: string;
  connect: () => void;
  fetchAll: () => Promise<void>;
  runBoardroom: () => Promise<void>;
  decide: (id: number, action: "approved" | "dismissed") => Promise<void>;
  execute: (id: number) => Promise<void>;
  saveBusiness: (b: Partial<Business>) => Promise<void>;
}

const AGENTS = ["ceo", "marketing", "sales", "finance", "strategy", "learning"];

export const useAxiom = create<State>((set, get) => ({
  connected: false,
  events: [],
  kpis: null,
  history: [],
  recommendations: [],
  business: null,
  agentStreams: Object.fromEntries(AGENTS.map((a) => [a, ""])),
  agentPhase: {},
  currentPhase: "",

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
    const [kpis, hist, recs, biz] = await Promise.all([
      fetch("/api/kpis").then((r) => r.json()),
      fetch("/api/kpis/history?days=30").then((r) => r.json()),
      fetch("/api/recommendations?limit=30").then((r) => r.json()),
      fetch("/api/business").then((r) => r.json()),
    ]);
    set({ kpis, history: hist, recommendations: recs, business: biz });
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
}));
