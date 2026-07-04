from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON


class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    industry: str
    stage: str = "Seed"
    website: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KpiSnapshot(SQLModel, table=True):
    """Time-series of the 9 dashboard metrics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(foreign_key="business.id")
    ts: datetime = Field(default_factory=datetime.utcnow)
    business_health: float = 0
    growth_score: float = 0
    revenue_opportunity: float = 0
    lead_score_avg: float = 0
    customer_health: float = 0
    market_readiness: float = 0
    burn_multiple: float = 0
    runway_months: float = 0
    mrr: float = 0


class AgentEvent(SQLModel, table=True):
    """Every thought/token/decision an agent produces — for the live boardroom stream."""
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    agent: str  # "ceo", "marketing", "sales", "finance", "strategy", "learning"
    kind: str  # "thinking" | "insight" | "recommendation" | "done" | "debate"
    content: str
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(foreign_key="business.id")
    ts: datetime = Field(default_factory=datetime.utcnow)
    agent: str
    title: str
    body: str
    predicted_impact_inr: float = 0
    confidence: float = 0.7
    status: str = "pending"  # pending | approved | dismissed | executed
    payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class RiskAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(foreign_key="business.id")
    ts: datetime = Field(default_factory=datetime.utcnow)
    severity: str  # low | medium | high | critical
    agent: str
    title: str
    detail: str
    acknowledged: bool = False


class Decision(SQLModel, table=True):
    """Records CEO decisions — the learning agent trains off this."""
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(default_factory=datetime.utcnow)
    recommendation_id: int
    action: str  # approved | dismissed
    outcome_inr: float = 0  # filled in by learning loop


# Mock external data tables
class GaEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    sessions: int
    users: int
    bounce_rate: float
    conversions: int
    top_source: str


class StripeTxn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    customer: str
    amount_inr: float
    kind: str  # new | recurring | refund | churn


class CrmLead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company: str
    contact: str
    stage: str  # discovery | qualified | proposal | negotiation | closed_won | closed_lost
    deal_size_inr: float
    last_touch: str
    owner: str
    score: float = 0


class CompetitorSignal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str
    competitor: str
    signal: str
    detail: str
