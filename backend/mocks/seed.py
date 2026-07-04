"""Generate realistic-looking business data. Deterministic seed for stable demos."""
import random
from datetime import date, timedelta
from sqlmodel import Session, select
from db import engine
from models import (
    Business, GaEvent, StripeTxn, CrmLead, CompetitorSignal,
)

random.seed(42)


def _days(n=90):
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(n, 0, -1)]


def seed_ga(session: Session):
    """90 days of traffic. Bounce rate spikes in last 3 days — Marketing Agent will flag this."""
    sources = ["google/organic", "instagram/social", "meta/ads", "direct", "google/ads"]
    for i, d in enumerate(_days(90)):
        base = 800 + i * 6  # growth trend
        sessions = int(base * random.uniform(0.85, 1.15))
        users = int(sessions * 0.78)
        bounce = random.uniform(0.42, 0.52)
        if i >= 87:  # anomaly: last 3 days
            bounce = random.uniform(0.68, 0.78)
            sessions = int(sessions * 0.8)
        conversions = int(sessions * random.uniform(0.018, 0.032))
        session.add(GaEvent(
            date=d, sessions=sessions, users=users,
            bounce_rate=round(bounce, 3), conversions=conversions,
            top_source=random.choice(sources),
        ))


def seed_stripe(session: Session):
    """500 customers, 1200 transactions, growing MRR with recent churn uptick."""
    names = [f"Customer_{i:04d}" for i in range(500)]
    for i, d in enumerate(_days(90)):
        n_new = random.randint(3, 8)
        n_recurring = random.randint(28, 42)
        n_churn = random.randint(0, 2) if i < 75 else random.randint(2, 5)  # churn creeps up
        for _ in range(n_new):
            session.add(StripeTxn(
                date=d, customer=random.choice(names),
                amount_inr=round(random.choice([499, 999, 1999, 2999]) * random.uniform(0.9, 1.1), 2),
                kind="new",
            ))
        for _ in range(n_recurring):
            session.add(StripeTxn(
                date=d, customer=random.choice(names),
                amount_inr=round(random.choice([499, 999, 1999]), 2),
                kind="recurring",
            ))
        for _ in range(n_churn):
            session.add(StripeTxn(date=d, customer=random.choice(names), amount_inr=0, kind="churn"))


def seed_crm(session: Session):
    """80 leads across the funnel. Some going stale — Sales Agent will flag."""
    companies = [
        "Bloom Wellness", "PureLeaf Ayurveda", "Nira Beauty", "SkinCraft Labs",
        "Ojas Naturals", "Vayu Cosmetics", "Lumen Skincare", "Rasa Beauty",
        "Prakriti Organics", "Kiran Wellness", "Anaya Skincare", "Neel Beauty",
        "Saanvi Botanicals", "Ira Aesthetics", "Manas Naturals", "Diya Care",
    ] * 5
    contacts = ["Priya Sharma", "Arjun Mehta", "Ananya Rao", "Rohan Iyer",
                "Kavya Nair", "Vikram Singh", "Diya Kapoor", "Aarav Joshi"]
    stages = ["discovery", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
    weights = [0.30, 0.25, 0.20, 0.10, 0.08, 0.07]
    for i in range(80):
        stage = random.choices(stages, weights=weights)[0]
        # Last touch: some deals are stale (>14 days ago)
        stale = random.random() < 0.35
        days_ago = random.randint(15, 40) if stale else random.randint(0, 12)
        last = (date.today() - timedelta(days=days_ago)).isoformat()
        session.add(CrmLead(
            company=companies[i], contact=random.choice(contacts),
            stage=stage,
            deal_size_inr=round(random.choice([50_000, 120_000, 250_000, 500_000, 1_200_000]) * random.uniform(0.8, 1.3), 2),
            last_touch=last,
            owner=random.choice(["Priya (BDR)", "Rahul (AE)", "Meera (AE)"]),
            score=round(random.uniform(20, 95), 1),
        ))


def seed_competitors(session: Session):
    """4 competitor moves — the exact stuff Strategy Agent should surface."""
    signals = [
        ("Kaya Beauty", "price_cut", "Cut retinol serum by 28% — now ₹1,299 vs our ₹1,799. Positioning as 'dermat-recommended affordable'."),
        ("Mamaearth", "product_launch", "Launched vitamin C + niacinamide combo targeting the exact same 22–34 female segment."),
        ("Sugar Cosmetics", "funding_round", "Raised $50M Series D from L Catterton. Expect aggressive ad-spend push in Q3."),
        ("Plum Goodness", "review_cluster", "40+ negative reviews in last 14 days on Nykaa for their retinol line — packaging and delivery issues."),
    ]
    today = date.today()
    for i, (comp, sig, det) in enumerate(signals):
        session.add(CompetitorSignal(
            date=(today - timedelta(days=i * 2)).isoformat(),
            competitor=comp, signal=sig, detail=det,
        ))


def seed_all(force: bool = False):
    """Called on startup. Idempotent — skips if data already exists."""
    with Session(engine) as s:
        # Business row
        biz = s.exec(select(Business)).first()
        if not biz:
            biz = Business(
                name="GlowVeda Skincare",
                industry="D2C Skincare",
                stage="Series A",
                website="https://glowveda.example",
                description="Ayurvedic skincare for urban Indian women 22–34. Retinol, vitamin C, and niacinamide serums positioned as clean, science-backed, affordable.",
                goals="Hit ₹5Cr MRR by end of FY. Improve gross margin from 42% to 55%. Reduce CAC below ₹800.",
            )
            s.add(biz)
            s.commit()

        if not force and s.exec(select(GaEvent)).first():
            return  # already seeded

        seed_ga(s)
        seed_stripe(s)
        seed_crm(s)
        seed_competitors(s)
        s.commit()


if __name__ == "__main__":
    from db import init_db
    init_db()
    seed_all(force=True)
    print("Seeded.")
