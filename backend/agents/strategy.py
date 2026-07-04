from agents.base import BaseAgent


SYSTEM = """You are the Strategy Agent inside AXIOM OS — the outside-in board advisor.
You track competitor moves, market shifts, and category positioning.
You think in bets, moats, and windows. Not tactics.
Never generic 'be customer-obsessed' fluff. Every recommendation must reference a specific competitor move or market signal."""

USER_TEMPLATE = """Business: {business_name} — {industry}
Recent competitor signals:
{signals}

Give me:
1. The most dangerous competitor move and why it matters to us specifically.
2. One strategic bet we should make in the next 30 days.
3. One thing we should stop doing.

Return JSON:
{{
  "top_threat": {{"competitor":"...","move":"...","why_it_matters":"..."}},
  "strategic_bet": {{"bet":"...","rationale":"...","confidence":0.7}},
  "stop_doing": "..."
}}"""


class StrategyAgent(BaseAgent):
    name = "strategy"
    display = "Strategy"
    role = "Market & competitors"

    async def run(self, ctx: dict) -> dict:
        from sqlmodel import Session, select
        from db import engine
        from models import CompetitorSignal

        await self.emit("thinking", "Scraping competitor signals — last 14 days…")

        with Session(engine) as s:
            sigs = s.exec(select(CompetitorSignal).order_by(CompetitorSignal.date.desc())).all()

        signal_lines = "\n".join([f"- [{s.date}] {s.competitor} ({s.signal}): {s.detail}" for s in sigs])
        await self.emit("insight", f"{len(sigs)} competitor signals in scope.")

        prompt = USER_TEMPLATE.format(
            business_name=ctx.get("business_name", "the business"),
            industry=ctx.get("industry", "D2C"),
            signals=signal_lines,
        )
        result = await self.structured(SYSTEM, prompt)
        threat = result.get("top_threat", {})
        bet = result.get("strategic_bet", {})
        stop = result.get("stop_doing", "")

        if threat.get("competitor"):
            await self.emit("insight",
                f"Top threat — {threat['competitor']}: {threat.get('move','')} → {threat.get('why_it_matters','')}",
                meta=threat)
        if bet.get("bet"):
            await self.emit("recommendation", f"Strategic bet — {bet['bet']}", meta=bet)
        if stop:
            await self.emit("debate", f"Stop doing: {stop}")
        await self.emit("done", "Strategic review complete.")
        return {"agent": "strategy", **result}
