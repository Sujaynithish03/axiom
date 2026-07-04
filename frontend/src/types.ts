export interface Kpis {
  business_health: number;
  growth_score: number;
  revenue_opportunity: number;
  lead_score_avg: number;
  customer_health: number;
  market_readiness: number;
  mrr: number;
  burn_multiple: number;
  runway_months: number;
  growth_pct: number;
  avg_bounce: number;
  conv_rate: number;
  active_pipeline: number;
  churn_30: number;
  churn_delta: number;
  competitor_signals: number;
}

export interface AgentEventMsg {
  id?: number;
  ts?: string;
  agent: string;
  display?: string;
  kind: string; // thinking | insight | recommendation | done | debate | phase | error | decision | executed | connected
  content: string;
  meta?: any;
}

export interface Recommendation {
  id: number;
  ts: string;
  agent: string;
  title: string;
  body: string;
  predicted_impact_inr: number;
  confidence: number;
  status: string;
  payload?: any;
}

export interface Business {
  id: number;
  name: string;
  industry: string;
  stage: string;
  website?: string;
  description?: string;
  goals?: string;
}
