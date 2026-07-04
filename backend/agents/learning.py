from agents.base import BaseAgent
from sqlmodel import Session, select, func
from db import engine
from models import Recommendation, Decision


SYSTEM = """You are the Learning Agent inside AXIOM OS.
Your job: look at past agent recommendations and how the founder actually decided (approved/dismissed),
and write a one-line prior adjustment for each other agent.
Be honest — if an agent's recommendations are getting dismissed a lot, say so."""


class LearningAgent(BaseAgent):
    name = "learning"
    display = "Learning"
    role = "Feedback loop"

    async def run(self, ctx: dict) -> dict:
        await self.emit("thinking", "Analyzing decision history across agents…")

        # Compute approve/dismiss ratio per agent
        stats: dict[str, dict] = {}
        with Session(engine) as s:
            recs = s.exec(select(Recommendation)).all()
            for r in recs:
                a = r.agent
                stats.setdefault(a, {"approved": 0, "dismissed": 0, "pending": 0, "executed": 0})
                if r.status in stats[a]:
                    stats[a][r.status] += 1

        insights = []
        for agent, s in stats.items():
            total_decided = s["approved"] + s["dismissed"] + s["executed"]
            if total_decided == 0:
                continue
            approve_rate = (s["approved"] + s["executed"]) / total_decided
            if approve_rate < 0.35:
                nudge = f"{agent} agent: {approve_rate:.0%} approval rate — recommendations feel too aggressive. Lower confidence, add more context."
                insights.append({"agent": agent, "approve_rate": approve_rate, "nudge": nudge})
                await self.emit("insight", nudge)
            elif approve_rate > 0.7:
                nudge = f"{agent} agent: {approve_rate:.0%} approval rate — trusted. Increase weight in CEO synthesis."
                insights.append({"agent": agent, "approve_rate": approve_rate, "nudge": nudge})
                await self.emit("insight", nudge)

        if not insights:
            await self.emit("insight", "Not enough decision history yet — learning loop primed and waiting.")

        await self.emit("done", f"Feedback loop updated: {len(insights)} agent priors adjusted.")
        return {"agent": "learning", "adjustments": insights}
