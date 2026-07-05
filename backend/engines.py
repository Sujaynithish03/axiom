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


async def run_engine(key: str, extra: str | None = None) -> dict:
    """Run one engine's AI generation and persist the latest output.

    `extra` injects a founder instruction so the engine's chatbot can steer the
    regenerated plan (e.g. "make pricing 20% cheaper", "go heavier on WhatsApp").
    """
    if key not in ENGINE_BUILDERS:
        raise ValueError(f"unknown engine: {key}")
    ctx = _business_ctx()
    system, user = ENGINE_BUILDERS[key](ctx)
    if extra:
        user += (
            f"\n\nIMPORTANT — the founder asked you to revise the plan. "
            f"Regenerate it, keeping the same JSON shape, to satisfy this: {extra}"
        )
    # Engine schemas are richer than agent calls — give the model room so the
    # JSON isn't truncated mid-object (which would fail to parse). Small local
    # models occasionally return empty/malformed output, so retry once.
    result = await complete_json(system, user, max_tokens=1400)
    if result.get("error"):
        result = await complete_json(system, user, max_tokens=1400)

    # Never persist a broken result over a previously-good plan.
    if not result.get("error"):
        with Session(db_engine) as s:
            biz = s.exec(select(Business)).first()
            bid = biz.id if biz else 1
            row = EngineOutput(business_id=bid, engine=key, payload=result)
            s.add(row)
            s.commit()
    return result


_ENGINE_PERSONA = {
    "strategy": "the Strategy Engine — market research, positioning and pricing",
    "marketing": "the Marketing Engine — 360° multi-channel marketing",
    "leadgen": "the Lead Gen Engine — acquiring and converting leads",
    "sales": "the Sales Engine — funnel, deals and outreach",
    "analytics": "the Analytics Engine — forecasting, insight and roadmaps",
    "success": "the Customer Success Engine — churn, support and success plays",
}


async def engine_chat(key: str, message: str) -> dict:
    """A dedicated chatbot per engine. Answers grounded in that engine's current
    plan — and if the founder asks to change something, regenerates the plan so
    the engine's data updates dynamically."""
    if key not in ENGINE_BUILDERS:
        raise ValueError(f"unknown engine: {key}")
    import json as _json

    latest = latest_engine(key)
    payload = latest["payload"] if latest else {}
    ctx = _business_ctx()
    k = ctx["kpis"]

    persona = _ENGINE_PERSONA.get(key, "an AI business engine")
    system = (
        f"You are {persona} for {ctx['name']} ({ctx['industry']}). "
        "Answer the founder's message conversationally and specifically, grounded in the "
        "current plan and metrics. Decide whether they are asking you to CHANGE the plan. "
        "Return only valid JSON."
    )
    user = f"""Current plan (JSON): {_json.dumps(payload)[:1600]}
Live metrics: Business Health {k['business_health']}/100 · MRR ₹{k['mrr']:,.0f} · Growth {k['growth_pct']:+.1f}%.

Founder says: "{message}"

Return JSON:
{{
  "reply": "your answer to the founder, 2-4 sentences, specific",
  "apply_change": true or false,
  "instruction": "if apply_change is true, a crisp instruction describing how to revise the plan; otherwise empty string"
}}"""

    meta = await complete_json(system, user, max_tokens=450)
    reply = meta.get("reply") or "Here's my take."
    apply = bool(meta.get("apply_change"))
    instruction = (meta.get("instruction") or "").strip()

    new_payload = None
    if apply and instruction:
        try:
            candidate = await run_engine(key, extra=instruction)
            if candidate and not candidate.get("error"):
                new_payload = candidate
        except Exception:
            new_payload = None
        if new_payload is None:
            reply += " (I couldn't cleanly rewrite the plan just now — try rephrasing, or hit Regenerate.)"

    return {"reply": reply, "updated": new_payload is not None, "payload": new_payload}


def latest_engine(key: str) -> dict | None:
    """Return the most recent stored output for an engine, if any."""
    with Session(db_engine) as s:
        row = s.exec(
            select(EngineOutput)
            .where(EngineOutput.engine == key)
            .order_by(EngineOutput.ts.desc())
        ).first()
        return {"engine": key, "payload": row.payload, "ts": row.ts.isoformat()} if row else None


# ============================================================
# Lead Gen Engine — the deep, interactive one:
# acquire leads → capture into CRM → convert each with AI.
# ============================================================
import random  # noqa: E402
from datetime import date  # noqa: E402

_LEAD_FIRST = ["Aarav", "Diya", "Kabir", "Ananya", "Vivaan", "Isha", "Reyansh",
               "Myra", "Arjun", "Saanvi", "Aditya", "Kiara", "Rohan", "Navya"]
_LEAD_LAST = ["Sharma", "Iyer", "Nair", "Mehta", "Reddy", "Kapoor", "Bose", "Rao"]
_LEAD_CO = ["Bloom Wellness", "PureLeaf Co", "Nira Beauty", "SkinCraft", "Ojas Naturals",
            "Lumen Labs", "Rasa Beauty", "Prakriti Organics", "Vayu Cosmetics", "Ira Aesthetics"]
_LEAD_SRC = ["Meta Ads", "Instagram Reels", "WhatsApp broadcast", "Google Search", "Influencer collab", "Pop-up event"]


def capture_leads(channel: str | None = None, n: int = 4) -> list[dict]:
    """Simulate a lead-gen campaign bringing fresh leads into the CRM."""
    src = channel or random.choice(_LEAD_SRC)
    created = []
    with Session(db_engine) as s:
        for _ in range(n):
            lead = CrmLead(
                company=random.choice(_LEAD_CO),
                contact=f"{random.choice(_LEAD_FIRST)} {random.choice(_LEAD_LAST)}",
                stage="discovery",
                deal_size_inr=float(random.choice([50_000, 120_000, 250_000, 500_000])),
                last_touch=date.today().isoformat(),
                owner=f"AI · {src}",
                score=round(random.uniform(45, 92), 1),
            )
            s.add(lead)
            s.commit()
            s.refresh(lead)
            created.append({
                "id": lead.id, "company": lead.company, "contact": lead.contact,
                "stage": lead.stage, "deal_size_inr": lead.deal_size_inr,
                "score": lead.score, "source": src,
            })
    return created


def list_leads(limit: int = 12) -> list[dict]:
    """Most recent leads — the captured pipeline."""
    with Session(db_engine) as s:
        rows = s.exec(select(CrmLead).order_by(CrmLead.id.desc()).limit(limit)).all()
        return [{
            "id": l.id, "company": l.company, "contact": l.contact, "stage": l.stage,
            "deal_size_inr": l.deal_size_inr, "score": l.score, "owner": l.owner,
        } for l in rows]


async def convert_lead(lead_id: int) -> dict:
    """AI generates a personalized conversion play for one specific lead."""
    with Session(db_engine) as s:
        lead = s.get(CrmLead, lead_id)
        if not lead:
            raise ValueError("lead not found")
        biz = s.exec(select(Business)).first()
    system = (
        "You are the Lead Gen Engine's conversion assistant. Given one lead, "
        "write the single best next action to convert them. Return only JSON."
    )
    user = f"""Our business: {biz.name if biz else 'the business'} — {biz.industry if biz else 'D2C'}
Lead: {lead.contact} at {lead.company} · stage {lead.stage} · score {lead.score}/100 · deal ~₹{lead.deal_size_inr:,.0f}

Return JSON:
{{
  "channel": "best channel to reach them (WhatsApp / email / call)",
  "message": "the actual ready-to-send message, personalized to this lead",
  "next_step": "the follow-up action after they respond"
}}"""
    result = await complete_json(system, user, max_tokens=500)
    result["lead_id"] = lead_id
    return result
