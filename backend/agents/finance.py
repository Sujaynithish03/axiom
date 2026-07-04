from agents.base import BaseAgent


SYSTEM = """You are the Finance Agent inside AXIOM OS — a hawkish CFO for an early-stage D2C brand.
You care about runway, burn multiple, unit economics, and cash discipline.
Every recommendation must include a specific ₹ number. No vague guidance.
You will push back on Marketing or Sales if they propose spend that breaks unit economics."""

USER_TEMPLATE = """Business: {business_name}
Financial snapshot (last 30 days):
- Revenue: ₹{mrr:,.0f}
- Revenue growth vs prior 30d: {growth_pct:+.1f}%
- Estimated monthly burn: ₹{burn:,.0f}
- Runway: {runway:.1f} months (bank ~₹2.5Cr)
- Burn multiple: {burn_mult:.2f}
- Churn events this period: {churn_30} (delta +{churn_delta})

Give me:
1. A one-line CFO verdict on financial health.
2. The single most important cash decision this month — with a specific ₹ number.
3. One line pushing back on any risky spend if warranted.

Return JSON:
{{
  "verdict": "...",
  "top_decision": {{"action":"...","amount_inr":500000,"rationale":"..."}},
  "spending_guardrail": "..."
}}"""


class FinanceAgent(BaseAgent):
    name = "finance"
    display = "Finance"
    role = "Cashflow & runway"

    async def run(self, ctx: dict) -> dict:
        k = ctx["kpis"]
        burn = k["mrr"] * 0.65
        await self.emit("thinking", "Reading Stripe txn stream, computing burn multiple…")

        prompt = USER_TEMPLATE.format(
            business_name=ctx.get("business_name", "the business"),
            mrr=k["mrr"], growth_pct=k["growth_pct"],
            burn=burn, runway=k["runway_months"],
            burn_mult=k["burn_multiple"], churn_30=k["churn_30"], churn_delta=k["churn_delta"],
        )
        result = await self.structured(SYSTEM, prompt)
        verdict = result.get("verdict", "")
        decision = result.get("top_decision", {})
        guard = result.get("spending_guardrail", "")

        if verdict:
            await self.emit("insight", f"CFO verdict: {verdict}")
        if decision.get("action"):
            await self.emit(
                "recommendation",
                f"{decision['action']} — ₹{decision.get('amount_inr',0):,}",
                meta=decision,
            )
        if guard:
            await self.emit("debate", f"Guardrail: {guard}")
        await self.emit("done", "Finance review complete.")
        return {"agent": "finance", **result, "burn_monthly_inr": burn}
