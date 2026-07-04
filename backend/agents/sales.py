from agents.base import BaseAgent
from datetime import date, timedelta


SYSTEM = """You are the Sales Agent inside AXIOM OS. You are a pipeline-focused revenue mechanic.
You spot stale deals, prioritize the leads most likely to close, and draft short punchy follow-up messages.
Never generic. Always reference the deal specifics.
Talk like an experienced VP of Sales who's seen every deal shape."""

USER_TEMPLATE = """Business: {business_name}
Pipeline snapshot ({total_leads} leads):
- Active pipeline value: ₹{active_pipeline:,.0f}
- Stale deals (no touch 15+ days): {stale_count}
- Avg lead score: {avg_score:.1f}/100
- Top hot deals (score > 80, in negotiation): {hot_summary}
- Top stale-but-large deals: {stale_summary}

Give me:
1. The single biggest risk to hitting quarterly quota.
2. Top 3 deals to unblock this week — with a one-line action per deal.

Return JSON:
{{
  "quota_risk": "...",
  "priority_deals": [
    {{"company":"...","action":"...","reason":"...","estimated_close_lift_inr":250000}}
  ]
}}"""


class SalesAgent(BaseAgent):
    name = "sales"
    display = "Sales"
    role = "Pipeline & leads"

    async def run(self, ctx: dict) -> dict:
        from sqlmodel import Session, select
        from db import engine
        from models import CrmLead

        await self.emit("thinking", "Scanning CRM pipeline…")

        with Session(engine) as s:
            leads = s.exec(select(CrmLead)).all()

        active = [l for l in leads if l.stage in ("qualified", "proposal", "negotiation")]
        pipe = sum(l.deal_size_inr for l in active)
        avg = sum(l.score for l in leads) / max(len(leads), 1)

        cutoff = (date.today() - timedelta(days=15)).isoformat()
        stale = [l for l in active if l.last_touch < cutoff]
        hot = sorted([l for l in active if l.score > 80 and l.stage == "negotiation"],
                     key=lambda x: -x.deal_size_inr)[:3]
        big_stale = sorted(stale, key=lambda x: -x.deal_size_inr)[:3]

        await self.emit("insight", f"{len(stale)} deals gone stale in active pipeline.")

        hot_summary = "; ".join([f"{l.company} (₹{l.deal_size_inr:,.0f}, score {l.score:.0f})" for l in hot]) or "none"
        stale_summary = "; ".join([f"{l.company} (₹{l.deal_size_inr:,.0f})" for l in big_stale]) or "none"

        prompt = USER_TEMPLATE.format(
            business_name=ctx.get("business_name", "the business"),
            total_leads=len(leads), active_pipeline=pipe,
            stale_count=len(stale), avg_score=avg,
            hot_summary=hot_summary, stale_summary=stale_summary,
        )
        result = await self.structured(SYSTEM, prompt)
        deals = result.get("priority_deals", [])
        risk = result.get("quota_risk", "")

        if risk:
            await self.emit("insight", f"Quota risk: {risk}")
        for d in deals:
            await self.emit(
                "recommendation",
                f"Unblock {d.get('company','deal')} — {d.get('action','')}",
                meta=d,
            )
        await self.emit("done", f"Prioritized {len(deals)} deals.")
        return {
            "agent": "sales",
            "priority_deals": deals,
            "quota_risk": risk,
            "avg_lead_score": avg,
            "active_pipeline_inr": pipe,
        }
