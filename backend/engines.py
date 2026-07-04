"""The six AI-driven business engines.

Each engine runs a single structured llama3.2 call over the live business
context and returns a typed result the frontend renders. This is the
"structured skeleton" layer — real AI output, one shot per engine — that the
deeper multi-step workflows will later grow into.
"""
from sqlmodel import Session, select
from db import engine as db_engine
from models import Business, CrmLead, EngineOutput
from metrics import compute_kpis
from llm import complete_json


def _business_ctx() -> dict:
    with Session(db_engine) as s:
        biz = s.exec(select(Business)).first()
        kpis = compute_kpis()
        return {
            "name": biz.name if biz else "the business",
            "industry": biz.industry if biz else "D2C",
            "stage": biz.stage if biz else "Seed",
            "description": biz.description if biz else "",
            "goals": biz.goals if biz else "",
            "kpis": kpis,
        }


# ---- Each engine: system prompt + a user-prompt builder + JSON shape hint ----

def _strategy_prompt(ctx: dict) -> tuple[str, str]:
    k = ctx["kpis"]
    system = (
        "You are the Strategy Engine of an AI business operating system. "
        "You do market research, brand positioning, and pricing. "
        "Be specific and numbers-first. Return only valid JSON."
    )
    user = f"""Business: {ctx['name']} — {ctx['industry']} ({ctx['stage']})
About: {ctx['description']}
Goals: {ctx['goals']}
Market readiness: {k['market_readiness']}/100 · {k['competitor_signals']} competitor signals.

Produce a strategy brief as JSON:
{{
  "market_research": "3-4 sentence read on the market and where this business fits",
  "brand_positioning": "one crisp positioning statement",
  "pricing_suggestions": [
    {{"tier":"...","price_inr":999,"rationale":"..."}}
  ],
  "go_to_market": ["3 concrete GTM moves"]
}}"""
    return system, user


def _marketing_prompt(ctx: dict) -> tuple[str, str]:
    k = ctx["kpis"]
    system = (
        "You are the Marketing Engine of an AI business OS. You design 360° "
        "multi-channel marketing plans. Be concrete about channels, budget and "
        "creative. Return only valid JSON."
    )
    user = f"""Business: {ctx['name']} — {ctx['industry']}
Conversion rate: {k['conv_rate']:.2%} · Avg bounce: {k['avg_bounce']:.0%}

Design a 360° marketing plan as JSON:
{{
  "big_idea": "the central campaign theme in one line",
  "channels": [
    {{"channel":"Instagram","plan":"...","monthly_budget_inr":50000,"expected_roas":3.0}}
  ],
  "content_samples": ["2 ready-to-post caption/ad lines"]
}}
Include 4 channels across social, search, influencer and email."""
    return system, user


def _leadgen_prompt(ctx: dict) -> tuple[str, str]:
    system = (
        "You are the Lead Generation Engine of an AI business OS. You bring in "
        "and convert leads across digital, messaging and physical channels. "
        "Be tactical and India-market aware. Return only valid JSON."
    )
    user = f"""Business: {ctx['name']} — {ctx['industry']} ({ctx['stage']})
About: {ctx['description']}

Produce a lead-gen playbook as JSON:
{{
  "target_segments": ["2-3 sharp ICP segments"],
  "digital_campaigns": [
    {{"channel":"Meta Ads","idea":"...","cta":"..."}}
  ],
  "whatsapp_campaign": {{"hook":"...","message":"ready-to-send WhatsApp broadcast","offer":"..."}},
  "physical_ideas": ["2 offline/physical lead ideas"],
  "conversion_tip": "one line on converting these leads"
}}
Include 3 digital campaigns."""
    return system, user


def _sales_prompt(ctx: dict) -> tuple[str, str]:
    k = ctx["kpis"]
    with Session(db_engine) as s:
        leads = s.exec(select(CrmLead)).all()
    stages = {}
    for l in leads:
        stages[l.stage] = stages.get(l.stage, 0) + 1
    system = (
        "You are the Sales Engine of an AI business OS. You build the sales "
        "funnel, prioritize deals and draft outreach. Return only valid JSON."
    )
    user = f"""Business: {ctx['name']}
Pipeline value: ₹{k['active_pipeline']:,.0f} · Avg lead score: {k['lead_score_avg']}/100
Deals by stage: {stages}

Produce a sales plan as JSON:
{{
  "funnel_stages": [
    {{"stage":"Awareness","action":"what to do here","conversion_target":"e.g. 20%"}}
  ],
  "priority_actions": ["3 things to do this week to move deals"],
  "outreach_draft": "a short, personalized follow-up email a rep can send today"
}}
Include 4 funnel stages from Awareness to Close."""
    return system, user


def _analytics_prompt(ctx: dict) -> tuple[str, str]:
    k = ctx["kpis"]
    system = (
        "You are the Analytics Engine of an AI business OS. You forecast, surface "
        "competitive insight and propose a roadmap. Return only valid JSON."
    )
    user = f"""Business: {ctx['name']} — {ctx['industry']}
MRR: ₹{k['mrr']:,.0f} · Growth: {k['growth_pct']:+.1f}% · Runway: {k['runway_months']}mo
Business health: {k['business_health']}/100 · Burn multiple: {k['burn_multiple']}

Produce an analytics brief as JSON:
{{
  "forecast": [
    {{"month":"Month +1","mrr_inr":1600000,"basis":"..."}}
  ],
  "competitive_insight": "one sharp competitive read",
  "roadmap": [
    {{"quarter":"Q1","focus":"...","outcome":"..."}}
  ],
  "headline_metric": "the single number leadership should watch and why"
}}
Include a 3-month MRR forecast and a 3-quarter roadmap."""
    return system, user


def _success_prompt(ctx: dict) -> tuple[str, str]:
    k = ctx["kpis"]
    system = (
        "You are the Customer Success Engine of an AI business OS. You reduce "
        "churn, run support playbooks and power an AI support assistant. "
        "Return only valid JSON."
    )
    user = f"""Business: {ctx['name']} — {ctx['industry']}
Customer health: {k['customer_health']}/100 · Churn last 30d: {k['churn_30']} (delta {k['churn_delta']:+d})

Produce a customer-success brief as JSON:
{{
  "health_summary": "2 sentence read on customer health and churn risk",
  "at_risk_segments": ["2 segments most likely to churn and why"],
  "support_playbook": ["3 proactive success plays to run this week"],
  "chatbot_greeting": "a warm one-line greeting the support chatbot should open with"
}}"""
    return system, user


ENGINE_BUILDERS = {
    "strategy": _strategy_prompt,
    "marketing": _marketing_prompt,
    "leadgen": _leadgen_prompt,
    "sales": _sales_prompt,
    "analytics": _analytics_prompt,
    "success": _success_prompt,
}

ENGINE_KEYS = list(ENGINE_BUILDERS.keys())


async def run_engine(key: str) -> dict:
    """Run one engine's AI generation and persist the latest output."""
    if key not in ENGINE_BUILDERS:
        raise ValueError(f"unknown engine: {key}")
    ctx = _business_ctx()
    system, user = ENGINE_BUILDERS[key](ctx)
    # Engine schemas are richer than agent calls — give the model room so the
    # JSON isn't truncated mid-object (which would fail to parse).
    result = await complete_json(system, user, max_tokens=1400)

    with Session(db_engine) as s:
        biz = s.exec(select(Business)).first()
        bid = biz.id if biz else 1
        row = EngineOutput(business_id=bid, engine=key, payload=result)
        s.add(row)
        s.commit()
    return result


def latest_engine(key: str) -> dict | None:
    """Return the most recent stored output for an engine, if any."""
    with Session(db_engine) as s:
        row = s.exec(
            select(EngineOutput)
            .where(EngineOutput.engine == key)
            .order_by(EngineOutput.ts.desc())
        ).first()
        return {"engine": key, "payload": row.payload, "ts": row.ts.isoformat()} if row else None
