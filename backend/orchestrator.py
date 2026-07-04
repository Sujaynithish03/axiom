"""The boardroom scheduler. Runs 4 tactical agents in parallel, then CEO synthesizes,
then Learning updates priors. Streams every event out through the websocket bus."""
import asyncio
from typing import Callable, Awaitable
from sqlmodel import Session, select
from db import engine
from models import Business, Recommendation
from metrics import compute_kpis
from llm import safe_num
from agents import (
    CeoAgent, MarketingAgent, SalesAgent,
    FinanceAgent, StrategyAgent, LearningAgent,
)


async def _load_business_ctx() -> dict:
    with Session(engine) as s:
        biz = s.exec(select(Business)).first()
        if not biz:
            return {"business_name": "the business", "industry": "D2C"}
        return {
            "business_name": biz.name,
            "industry": biz.industry,
            "stage": biz.stage,
            "description": biz.description,
            "goals": biz.goals,
            "business_id": biz.id,
        }


def _s(value, default: str = "") -> str:
    """Null-safe string for building recommendation bodies."""
    return default if value is None else str(value)


async def _persist_recommendations(reports: dict, business_id: int):
    """Turn agent recommendation events into persisted Recommendation rows the UI can list.

    Each agent block is isolated in its own try/except so one malformed field
    from the local model can never wipe out every other agent's recommendations.
    """
    rows: list[Recommendation] = []

    # Marketing
    try:
        for r in reports.get("marketing", {}).get("recommendations", []) or []:
            rows.append(Recommendation(
                business_id=business_id, agent="marketing",
                title=_s(r.get("title"), "Campaign"),
                body=_s(r.get("action")) + " — " + _s(r.get("why")),
                predicted_impact_inr=safe_num(r.get("budget_inr")) * safe_num(r.get("predicted_roas"), 1),
                confidence=0.7, payload=r,
            ))
    except Exception:
        pass

    # Sales
    try:
        for d in reports.get("sales", {}).get("priority_deals", []) or []:
            rows.append(Recommendation(
                business_id=business_id, agent="sales",
                title=f"Unblock {_s(d.get('company'), 'deal')}",
                body=_s(d.get("action")) + " — " + _s(d.get("reason")),
                predicted_impact_inr=safe_num(d.get("estimated_close_lift_inr")),
                confidence=0.65, payload=d,
            ))
    except Exception:
        pass

    # Finance
    try:
        fd = reports.get("finance", {}).get("top_decision", {}) or {}
        if fd.get("action"):
            rows.append(Recommendation(
                business_id=business_id, agent="finance",
                title=_s(fd.get("action"), "Cash decision"),
                body=_s(fd.get("rationale")),
                predicted_impact_inr=safe_num(fd.get("amount_inr")),
                confidence=0.8, payload=fd,
            ))
    except Exception:
        pass

    # Strategy
    try:
        sb = reports.get("strategy", {}).get("strategic_bet", {}) or {}
        if sb.get("bet"):
            rows.append(Recommendation(
                business_id=business_id, agent="strategy",
                title=_s(sb.get("bet"), "Strategic bet"),
                body=_s(sb.get("rationale")),
                predicted_impact_inr=0,
                confidence=safe_num(sb.get("confidence"), 0.6),
                payload=sb,
            ))
    except Exception:
        pass

    # CEO decisions
    try:
        for dec in reports.get("ceo", {}).get("decisions", []) or []:
            rows.append(Recommendation(
                business_id=business_id, agent="ceo",
                title=f"P{_s(dec.get('rank'), '?')}: {_s(dec.get('title'), 'Decision')}",
                body=_s(dec.get("why")),
                predicted_impact_inr=0,
                confidence=0.85, payload=dec,
            ))
    except Exception:
        pass

    if rows:
        with Session(engine) as s:
            for row in rows:
                s.add(row)
            s.commit()


async def run_boardroom(emit: Callable[[dict], Awaitable[None]]) -> dict:
    """The full 5D cycle: Discover→Design→Deliver→Develop→Dominate, one pass."""
    ctx = await _load_business_ctx()
    business_id = ctx.get("business_id", 1)

    # Discover: compute KPIs
    await emit({"agent": "system", "kind": "phase", "content": "🔍 DISCOVER — computing KPIs and pulling data streams…"})
    kpis = compute_kpis(business_id)
    ctx["kpis"] = kpis
    await emit({"agent": "system", "kind": "phase", "content": f"Business Health: {kpis['business_health']}/100 · MRR ₹{kpis['mrr']:,.0f} · Runway {kpis['runway_months']:.1f}mo"})

    # Design: 4 tactical agents in parallel
    await emit({"agent": "system", "kind": "phase", "content": "🎨 DESIGN — 4 agents thinking in parallel…"})
    tactical = [
        MarketingAgent(emit), SalesAgent(emit),
        FinanceAgent(emit), StrategyAgent(emit),
    ]
    results = await asyncio.gather(*[a.run(ctx) for a in tactical], return_exceptions=True)

    reports = {}
    for a, r in zip(tactical, results):
        if isinstance(r, Exception):
            await emit({"agent": a.name, "kind": "error", "content": f"Agent failed: {r}"})
            reports[a.name] = {}
        else:
            reports[a.name] = r

    # Deliver: CEO synthesizes into decisions
    await emit({"agent": "system", "kind": "phase", "content": "🚀 DELIVER — CEO synthesizing morning briefing…"})
    ctx["reports"] = reports
    ceo = CeoAgent(emit)
    try:
        ceo_result = await ceo.run(ctx)
        reports["ceo"] = ceo_result
    except Exception as e:
        await emit({"agent": "ceo", "kind": "error", "content": f"CEO synthesis failed: {e}"})
        reports["ceo"] = {}

    # Persist recommendations so dashboard can list them
    await _persist_recommendations(reports, business_id)

    # Develop: Learning agent updates priors from past decisions
    await emit({"agent": "system", "kind": "phase", "content": "📈 DEVELOP — Learning agent updating priors…"})
    learn = LearningAgent(emit)
    try:
        learn_result = await learn.run(ctx)
        reports["learning"] = learn_result
    except Exception as e:
        await emit({"agent": "learning", "kind": "error", "content": f"Learning failed: {e}"})

    # Dominate: signal complete
    await emit({"agent": "system", "kind": "phase", "content": "👑 DOMINATE — boardroom complete. Dashboard updated."})
    return {"kpis": kpis, "reports": reports}
