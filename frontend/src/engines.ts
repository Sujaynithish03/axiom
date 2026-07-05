import {
  Target, Megaphone, Magnet, TrendingUp, LineChart, HeartHandshake, ImageIcon,
} from "lucide-react";

export interface EngineDef {
  key: string;
  label: string;
  title: string;
  subtitle: string;
  icon: any;
  color: string; // hex accent
  cta: string;
}

// The six AI-driven business engines, in the order the sponsor lists them.
export const ENGINES: EngineDef[] = [
  {
    key: "strategy",
    label: "Strategy",
    title: "Strategy Engine",
    subtitle: "Market research, brand positioning and AI pricing — the plan behind everything.",
    icon: Target,
    color: "#AFA9EC",
    cta: "Generate strategy brief",
  },
  {
    key: "marketing",
    label: "Marketing",
    title: "Marketing Engine",
    subtitle: "A 360° multi-channel marketing plan with budgets, creative and expected ROAS.",
    icon: Megaphone,
    color: "#F0997B",
    cta: "Design 360° plan",
  },
  {
    key: "leadgen",
    label: "Lead Gen",
    title: "Lead Generation Engine",
    subtitle: "Bring in leads across digital, WhatsApp and physical channels — and convert them.",
    icon: Magnet,
    color: "#5EA0FF",
    cta: "Generate lead playbook",
  },
  {
    key: "sales",
    label: "Sales",
    title: "Sales Engine",
    subtitle: "Build the funnel, prioritize deals and draft outreach that closes.",
    icon: TrendingUp,
    color: "#5DCAA5",
    cta: "Build sales plan",
  },
  {
    key: "analytics",
    label: "Analytics",
    title: "Analytics Engine",
    subtitle: "Forecasting, competitive insight and a roadmap — on top of the live KPI dashboard.",
    icon: LineChart,
    color: "#00E5A0",
    cta: "Run forecast & roadmap",
  },
  {
    key: "success",
    label: "Customer Success",
    title: "Customer Success Engine",
    subtitle: "Reduce churn, run success playbooks and power the AI support copilot.",
    icon: HeartHandshake,
    color: "#ED93B1",
    cta: "Generate success plan",
  },
  {
    key: "adposter",
    label: "Ad Poster",
    title: "Ad Poster Engine",
    subtitle: "Real-time ad creative, generated on demand by Gemini — the one engine that isn't fully local.",
    icon: ImageIcon,
    color: "#FFB454",
    cta: "Generate poster",
  },
];

export const engineByKey = (k: string) => ENGINES.find((e) => e.key === k);
