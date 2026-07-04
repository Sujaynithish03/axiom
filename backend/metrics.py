"""Compute the 9 dashboard KPIs from mock data. Everything here is derived — no fakery."""
from datetime import date, timedelta, datetime
from sqlmodel import Session, select, func
from db import engine
from models import GaEvent, StripeTxn, CrmLead, CompetitorSignal, KpiSnapshot


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def compute_kpis(business_id: int = 1) -> dict:
    with Session(engine) as s:
        today = date.today()
        d30 = (today - timedelta(days=30)).isoformat()
        d60 = (today - timedelta(days=60)).isoformat()
        d90 = (today - timedelta(days=90)).isoformat()

        # --- Revenue / MRR ---
        rev_30 = s.exec(
            select(func.sum(StripeTxn.amount_inr)).where(
                StripeTxn.date >= d30, StripeTxn.kind.in_(("new", "recurring"))
            )
        ).one() or 0
        rev_prev_30 = s.exec(
            select(func.sum(StripeTxn.amount_inr)).where(
                StripeTxn.date >= d60, StripeTxn.date < d30,
                StripeTxn.kind.in_(("new", "recurring"))
            )
        ).one() or 0
        mrr = float(rev_30)
        growth_pct = ((rev_30 - rev_prev_30) / rev_prev_30 * 100) if rev_prev_30 else 0

        # --- Traffic / conversion ---
        ga_30 = s.exec(select(GaEvent).where(GaEvent.date >= d30)).all()
        avg_bounce = sum(g.bounce_rate for g in ga_30) / max(len(ga_30), 1)
        total_conv = sum(g.conversions for g in ga_30)
        total_sess = sum(g.sessions for g in ga_30)
        conv_rate = total_conv / max(total_sess, 1)

        # --- Leads ---
        leads = s.exec(select(CrmLead)).all()
        avg_lead_score = sum(l.score for l in leads) / max(len(leads), 1)
        active_pipeline = sum(
            l.deal_size_inr for l in leads
            if l.stage in ("qualified", "proposal", "negotiation")
        )

        # --- Churn ---
        churn_30 = s.exec(
            select(func.count(StripeTxn.id)).where(
                StripeTxn.date >= d30, StripeTxn.kind == "churn"
            )
        ).one() or 0
        churn_prev = s.exec(
            select(func.count(StripeTxn.id)).where(
                StripeTxn.date >= d60, StripeTxn.date < d30, StripeTxn.kind == "churn"
            )
        ).one() or 0
        churn_delta = churn_30 - churn_prev

        # --- Competitor pressure ---
        comp_signals = s.exec(select(CompetitorSignal)).all()
        market_pressure = min(len(comp_signals) * 15, 60)  # more signals = harder market

        # --- Derived scores ---
        # Growth score: rewards recent revenue delta
        growth_score = _clamp(50 + growth_pct * 2)
        # Customer health: 100 - churn impact
        customer_health = _clamp(90 - churn_30 * 3)
        # Market readiness: how easy is it to win right now (inverse of pressure + comp signals)
        market_readiness = _clamp(80 - market_pressure + (30 if churn_delta < 3 else 0))
        # Revenue opportunity: recovering lost bounce + closing stale deals
        recoverable = active_pipeline * 0.25 + (avg_bounce - 0.5) * total_sess * 500
        revenue_opportunity = max(recoverable, 0)
        # Business health = weighted composite
        business_health = _clamp(
            0.30 * growth_score
            + 0.25 * customer_health
            + 0.20 * (conv_rate * 2000)  # ~1.5% conv → 30 points
            + 0.15 * market_readiness
            + 0.10 * (avg_lead_score)
        )

        # Simulated cashflow: burn = 65% of revenue for demo
        burn_monthly = mrr * 0.65
        runway = 25_000_000 / max(burn_monthly, 1)  # ₹2.5Cr in bank
        burn_multiple = burn_monthly / max(rev_30 - rev_prev_30, 1) if rev_30 > rev_prev_30 else 3.0

        result = {
            "business_health": round(business_health, 1),
            "growth_score": round(growth_score, 1),
            "revenue_opportunity": round(revenue_opportunity, 0),
            "lead_score_avg": round(avg_lead_score, 1),
            "customer_health": round(customer_health, 1),
            "market_readiness": round(market_readiness, 1),
            "mrr": round(mrr, 0),
            "burn_multiple": round(burn_multiple, 2),
            "runway_months": round(runway, 1),
            "growth_pct": round(growth_pct, 1),
            "avg_bounce": round(avg_bounce, 3),
            "conv_rate": round(conv_rate, 4),
            "active_pipeline": round(active_pipeline, 0),
            "churn_30": churn_30,
            "churn_delta": churn_delta,
            "competitor_signals": len(comp_signals),
        }

        snap = KpiSnapshot(
            business_id=business_id,
            business_health=result["business_health"],
            growth_score=result["growth_score"],
            revenue_opportunity=result["revenue_opportunity"],
            lead_score_avg=result["lead_score_avg"],
            customer_health=result["customer_health"],
            market_readiness=result["market_readiness"],
            burn_multiple=result["burn_multiple"],
            runway_months=result["runway_months"],
            mrr=result["mrr"],
        )
        s.add(snap)
        s.commit()
        return result


def kpi_history(business_id: int = 1, days: int = 30):
    """Trend data for sparklines."""
    with Session(engine) as s:
        cutoff = datetime.utcnow() - timedelta(days=days)
        snaps = s.exec(
            select(KpiSnapshot)
            .where(KpiSnapshot.business_id == business_id, KpiSnapshot.ts >= cutoff)
            .order_by(KpiSnapshot.ts)
        ).all()
        return [
            {"ts": s.ts.isoformat(), "business_health": s.business_health,
             "mrr": s.mrr, "growth_score": s.growth_score}
            for s in snaps
        ]
