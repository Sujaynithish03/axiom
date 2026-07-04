from agents.base import BaseAgent
from llm import safe_num, safe_str


SYSTEM = """You are the Marketing Agent inside AXIOM OS, an AI executive team for a D2C skincare founder in India.
You obsess over web traffic, ad ROAS, funnel conversion, and creative performance.
Style: crisp, numbers-first, no marketing fluff. Talk like a growth lead in a war room.
Always ground observations in the numbers given. Never invent metrics."""

USER_TEMPLATE = """Business: {business_name} — {industry}
Last 30 days:
- Sessions: {sessions:,}   Conversions: {conv:,}   Conv rate: {conv_rate:.2%}
- Avg bounce rate: {bounce:.1%} (baseline ~47%)
- Top sources: {sources}

Anomaly window (last 3 days):
- Bounce rate spiked to {recent_bounce:.1%}
- Session volume down ~20% vs 30-day average

Give me:
1. What likely caused the anomaly (one sentence, specific).
2. Two concrete campaign recommendations to run this week.
3. For each: predicted ROAS and estimated budget in ₹.

Return JSON:
{{
  "cause": "...",
  "recommendations": [
    {{"title":"...","action":"...","budget_inr":50000,"predicted_roas":3.2,"why":"..."}}
  ]
}}"""


class MarketingAgent(BaseAgent):
    name = "marketing"
    display = "Marketing"
    role = "Campaigns & growth"

    async def run(self, ctx: dict) -> dict:
        from sqlmodel import Session, select
        from db import engine
        from models import GaEvent
        from datetime import date, timedelta

        await self.emit("thinking", "Pulling GA4 traffic — 90 days…")

        with Session(engine) as s:
            d30 = (date.today() - timedelta(days=30)).isoformat()
            d3 = (date.today() - timedelta(days=3)).isoformat()
            g30 = s.exec(select(GaEvent).where(GaEvent.date >= d30)).all()
            g3 = s.exec(select(GaEvent).where(GaEvent.date >= d3)).all()

        sessions = sum(g.sessions for g in g30)
        conv = sum(g.conversions for g in g30)
        conv_rate = conv / max(sessions, 1)
        bounce = sum(g.bounce_rate for g in g30) / max(len(g30), 1)
        recent_bounce = sum(g.bounce_rate for g in g3) / max(len(g3), 1)
        sources = {}
        for g in g30:
            sources[g.top_source] = sources.get(g.top_source, 0) + g.sessions
        top_srcs = ", ".join([f"{k} ({v:,})" for k, v in sorted(sources.items(), key=lambda x: -x[1])[:3]])

        await self.emit("insight", f"Bounce spike detected: {recent_bounce:.0%} vs {bounce:.0%} baseline. Investigating…")

        prompt = USER_TEMPLATE.format(
            business_name=ctx.get("business_name", "the business"),
            industry=ctx.get("industry", "D2C"),
            sessions=sessions, conv=conv, conv_rate=conv_rate,
            bounce=bounce, sources=top_srcs, recent_bounce=recent_bounce,
        )
        result = await self.structured(SYSTEM, prompt)
        recs = result.get("recommendations", [])
        cause = result.get("cause", "")

        if cause:
            await self.emit("insight", f"Root cause: {cause}")
        # Normalize model output so downstream formatting/persistence never crashes
        for r in recs:
            r["budget_inr"] = safe_num(r.get("budget_inr"), 0)
            r["predicted_roas"] = safe_num(r.get("predicted_roas"), 1)
            r["title"] = safe_str(r.get("title"), "Campaign")
            r["action"] = safe_str(r.get("action"))
            r["why"] = safe_str(r.get("why"))

        for r in recs:
            await self.emit(
                "recommendation",
                f"{r['title']} — {r['action']} (Budget ₹{r['budget_inr']:,.0f}, ROAS {r['predicted_roas']}x)",
                meta=r,
            )
        await self.emit("done", f"{len(recs)} campaign plays drafted.")
        return {"agent": "marketing", "recommendations": recs, "cause": safe_str(cause)}
