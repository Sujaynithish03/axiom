from agents.base import BaseAgent


SYSTEM = """You are the CEO Agent inside AXIOM OS — the chief of staff.
You've just received briefings from Marketing, Sales, Finance, and Strategy.
Your job is to SYNTHESIZE — not repeat. Find where they agree, resolve where they conflict, and deliver a 90-second morning briefing to the human founder.
Style: direct, warm, human. Talk like you're standing next to them with a coffee.
Never bullet-list everything. Write it like a real briefing.
End with exactly 3 decisions the founder must make today, ranked."""

USER_TEMPLATE = """Founder briefing — {business_name}
Overall business health: {business_health}/100

Marketing said:
- Root cause of traffic dip: {mkt_cause}
- Top recommendation: {mkt_top}

Sales said:
- Quota risk: {sales_risk}
- Top deal to unblock: {sales_top}

Finance said:
- Verdict: {fin_verdict}
- Top cash decision: {fin_top}
- Guardrail on spend: {fin_guard}

Strategy said:
- Top threat: {strat_threat}
- Strategic bet: {strat_bet}

Write:
1. A 3-sentence morning briefing spoken directly to the founder. Warm, direct, specific.
2. The 3 decisions they must make today, ranked. Each: 1-line title + 1-line why.

Return JSON:
{{
  "briefing": "...",
  "decisions": [
    {{"rank":1,"title":"...","why":"..."}},
    {{"rank":2,"title":"...","why":"..."}},
    {{"rank":3,"title":"...","why":"..."}}
  ]
}}"""


class CeoAgent(BaseAgent):
    name = "ceo"
    display = "CEO"
    role = "Synthesis & decisions"

    async def run(self, ctx: dict) -> dict:
        await self.emit("thinking", "Reading briefs from Marketing, Sales, Finance, Strategy…")

        reports = ctx.get("reports", {})
        m = reports.get("marketing", {})
        s = reports.get("sales", {})
        f = reports.get("finance", {})
        st = reports.get("strategy", {})

        mkt_top = m.get("recommendations", [{}])[0].get("title", "n/a") if m.get("recommendations") else "n/a"
        sales_top = s.get("priority_deals", [{}])[0].get("company", "n/a") if s.get("priority_deals") else "n/a"
        fin_top = f.get("top_decision", {}).get("action", "n/a")
        strat_threat = st.get("top_threat", {}).get("competitor", "n/a") + " — " + st.get("top_threat", {}).get("move", "")
        strat_bet = st.get("strategic_bet", {}).get("bet", "n/a")

        prompt = USER_TEMPLATE.format(
            business_name=ctx.get("business_name", "your business"),
            business_health=ctx["kpis"]["business_health"],
            mkt_cause=m.get("cause", "n/a"),
            mkt_top=mkt_top,
            sales_risk=s.get("quota_risk", "n/a"),
            sales_top=sales_top,
            fin_verdict=f.get("verdict", "n/a"),
            fin_top=fin_top,
            fin_guard=f.get("spending_guardrail", "n/a"),
            strat_threat=strat_threat,
            strat_bet=strat_bet,
        )

        await self.emit("thinking", "Resolving conflicts, ranking decisions…")
        result = await self.structured(SYSTEM, prompt)
        briefing = result.get("briefing", "")
        decisions = result.get("decisions", [])

        if briefing:
            await self.emit("insight", briefing, meta={"briefing": True})
        for d in decisions:
            await self.emit(
                "recommendation",
                f"[Priority {d.get('rank','?')}] {d.get('title','')} — {d.get('why','')}",
                meta=d,
            )
        await self.emit("done", "Morning briefing ready.")
        return {"agent": "ceo", "briefing": briefing, "decisions": decisions}
