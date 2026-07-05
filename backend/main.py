import asyncio
import json
import random
from datetime import datetime, date
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from db import engine, init_db
from models import Business, Recommendation, RiskAlert, AgentEvent, Decision, StripeTxn
from mocks.seed import seed_all
from metrics import compute_kpis, kpi_history
from orchestrator import run_boardroom
from engines import (
    run_engine, latest_engine, ENGINE_KEYS,
    capture_leads, list_leads, convert_lead,
)
from llm import stream_chat, check_ollama


# ------- WebSocket bus -------
class Bus:
    def __init__(self):
        self.subs: Set[WebSocket] = set()

    async def subscribe(self, ws: WebSocket):
        await ws.accept()
        self.subs.add(ws)

    def unsubscribe(self, ws: WebSocket):
        self.subs.discard(ws)

    async def publish(self, payload: dict):
        dead = []
        msg = json.dumps(payload, default=str)
        for ws in list(self.subs):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.subs.discard(d)


bus = Bus()


# ------- Live heartbeat -------
# Keeps the app feeling alive: trickles a little real revenue every few seconds
# and streams a rotating "live monitoring" pulse to the boardroom, so the
# dashboard numbers move and the event log never sits still.
HEARTBEAT_PULSES = [
    ("marketing", "Marketing", "Monitoring live sessions — traffic steady."),
    ("sales", "Sales", "Watching pipeline — checking for newly-stale deals."),
    ("finance", "Finance", "Cash position nominal. Tracking daily burn."),
    ("strategy", "Strategy", "Scanning competitor feeds for new signals."),
    ("ceo", "CEO", "All systems nominal. Standing by for your next move."),
    ("learning", "Learning", "Listening for your decisions to refine priors."),
]


async def heartbeat():
    """Background loop — only runs when a boardroom session is NOT active."""
    await asyncio.sleep(4)
    i = 0
    while True:
        try:
            if not _boardroom_lock.locked():
                # trickle a small recurring payment so MRR/health drift upward
                with Session(engine) as s:
                    today = date.today().isoformat()
                    for _ in range(random.randint(1, 3)):
                        s.add(StripeTxn(
                            date=today, customer=f"live_{i}",
                            amount_inr=float(random.choice([499, 999, 1999])),
                            kind="recurring",
                        ))
                    s.commit()
                agent, display, line = random.choice(HEARTBEAT_PULSES)
                await bus.publish({
                    "agent": agent, "display": display, "kind": "pulse",
                    "content": line, "ts": datetime.utcnow().isoformat(), "meta": {},
                })
        except Exception:
            pass
        i += 1
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_all()
    hb = asyncio.create_task(heartbeat())
    yield
    hb.cancel()


app = FastAPI(title="AXIOM OS", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ------- Health -------
@app.get("/api/health")
async def health():
    err = await check_ollama()
    return {
        "backend": "ok",
        "ollama": "ok" if err is None else "error",
        "ollama_message": err,
    }


# ------- Business / onboarding -------
class OnboardingPayload(BaseModel):
    name: str
    industry: str
    stage: str = "Seed"
    website: str | None = None
    description: str | None = None
    goals: str | None = None


@app.get("/api/business")
async def get_business():
    with Session(engine) as s:
        b = s.exec(select(Business)).first()
        if not b:
            return None
        return b


@app.post("/api/business")
async def update_business(payload: OnboardingPayload):
    with Session(engine) as s:
        b = s.exec(select(Business)).first()
        if b:
            b.name = payload.name
            b.industry = payload.industry
            b.stage = payload.stage
            b.website = payload.website
            b.description = payload.description
            b.goals = payload.goals
        else:
            b = Business(**payload.model_dump())
            s.add(b)
        s.commit()
        s.refresh(b)
        return b


# ------- KPIs / dashboard -------
@app.get("/api/kpis")
async def get_kpis():
    return compute_kpis()


@app.get("/api/kpis/history")
async def get_kpi_history(days: int = 30):
    return kpi_history(days=days)


@app.get("/api/recommendations")
async def list_recommendations(status: str | None = None, limit: int = 50):
    with Session(engine) as s:
        q = select(Recommendation).order_by(Recommendation.ts.desc()).limit(limit)
        if status:
            q = select(Recommendation).where(Recommendation.status == status).order_by(Recommendation.ts.desc()).limit(limit)
        return s.exec(q).all()


class DecisionPayload(BaseModel):
    action: str  # approved | dismissed


@app.post("/api/recommendations/{rec_id}/decide")
async def decide(rec_id: int, payload: DecisionPayload):
    if payload.action not in ("approved", "dismissed"):
        raise HTTPException(400, "action must be approved or dismissed")
    with Session(engine) as s:
        r = s.get(Recommendation, rec_id)
        if not r:
            raise HTTPException(404, "not found")
        r.status = payload.action
        s.add(r)
        s.add(Decision(recommendation_id=rec_id, action=payload.action))
        s.commit()
        s.refresh(r)
    # Notify boardroom stream
    await bus.publish({"agent": "system", "kind": "decision",
                       "content": f"Founder {payload.action} recommendation #{rec_id}",
                       "meta": {"rec_id": rec_id, "action": payload.action}})
    return r


@app.post("/api/recommendations/{rec_id}/execute")
async def execute(rec_id: int):
    """One-click execute — for the demo, this just marks as executed and broadcasts.
    In production, this would fire the actual action (draft email, launch campaign, etc.)."""
    with Session(engine) as s:
        r = s.get(Recommendation, rec_id)
        if not r:
            raise HTTPException(404, "not found")
        r.status = "executed"
        s.add(r)
        s.commit()
    await bus.publish({"agent": "system", "kind": "executed",
                       "content": f"✅ Executed: {r.title}",
                       "meta": {"rec_id": rec_id}})
    return {"ok": True, "rec_id": rec_id}


@app.get("/api/risks")
async def list_risks():
    with Session(engine) as s:
        return s.exec(select(RiskAlert).order_by(RiskAlert.ts.desc()).limit(20)).all()


@app.get("/api/events")
async def list_events(limit: int = 100):
    with Session(engine) as s:
        return s.exec(select(AgentEvent).order_by(AgentEvent.ts.desc()).limit(limit)).all()


@app.get("/api/briefing")
async def get_briefing():
    """The CEO Agent's latest morning briefing — the dashboard Executive Summary."""
    with Session(engine) as s:
        ev = s.exec(
            select(AgentEvent)
            .where(AgentEvent.agent == "ceo", AgentEvent.kind == "insight")
            .order_by(AgentEvent.ts.desc())
        ).first()
        return {
            "briefing": ev.content if ev else None,
            "ts": ev.ts.isoformat() if ev else None,
        }


# ------- The six business engines -------
@app.get("/api/engines/{key}")
async def get_engine(key: str):
    """Latest stored output for one engine (null if never run)."""
    if key not in ENGINE_KEYS:
        raise HTTPException(404, f"unknown engine: {key}")
    return latest_engine(key)


@app.post("/api/engines/{key}/run")
async def run_engine_endpoint(key: str):
    """Run one engine's AI generation now and return the fresh output."""
    if key not in ENGINE_KEYS:
        raise HTTPException(404, f"unknown engine: {key}")
    try:
        result = await run_engine(key)
    except Exception as e:
        raise HTTPException(500, f"engine failed: {e}")
    await bus.publish({
        "agent": key, "kind": "engine",
        "content": f"✳️ {key.capitalize()} Engine generated a fresh plan.",
        "meta": {"engine": key},
    })
    return {"engine": key, "payload": result}


# ------- Lead Gen Engine: capture + convert -------
class CapturePayload(BaseModel):
    channel: str | None = None
    count: int = 4


@app.get("/api/leadgen/leads")
async def leadgen_leads(limit: int = 12):
    return list_leads(limit=limit)


@app.post("/api/leadgen/capture")
async def leadgen_capture(payload: CapturePayload):
    leads = capture_leads(channel=payload.channel, n=max(1, min(payload.count, 8)))
    await bus.publish({
        "agent": "leadgen", "kind": "engine",
        "content": f"🧲 Captured {len(leads)} new leads via {payload.channel or 'AI campaign'}.",
        "meta": {"count": len(leads)},
    })
    return leads


@app.post("/api/leadgen/convert/{lead_id}")
async def leadgen_convert(lead_id: int):
    try:
        return await convert_lead(lead_id)
    except ValueError:
        raise HTTPException(404, "lead not found")
    except Exception as e:
        raise HTTPException(500, f"convert failed: {e}")


# ------- "Simulate a busy day" — the cinematic demo moment -------
_sim_lock = asyncio.Lock()
_SIM_CHANNELS = ["Instagram Reels", "Meta Ads", "WhatsApp broadcast",
                 "Google Search", "Influencer collab", "Pop-up event"]


@app.post("/api/simulate/day")
async def simulate_day(background: BackgroundTasks):
    """Fire ~100 events over ~30s: leads arrive, revenue books, a risk fires.
    Every screen animates because it all streams over the WebSocket bus."""
    async def go():
        if _sim_lock.locked():
            await bus.publish({"agent": "system", "kind": "sim",
                               "content": "A day is already being simulated…"})
            return
        async with _sim_lock:
            steps = 24
            await bus.publish({"agent": "system", "kind": "sim_start",
                               "content": "⚡ Simulating a busy day…",
                               "meta": {"steps": steps}})
            total_leads = 0
            total_rev = 0.0
            for i in range(steps):
                n = random.randint(2, 5)
                leads = capture_leads(channel=random.choice(_SIM_CHANNELS), n=n)
                total_leads += n
                booked = 0.0
                with Session(engine) as s:
                    for _ in range(random.randint(2, 6)):
                        amt = float(random.choice([499, 999, 1999, 2999]))
                        s.add(StripeTxn(date=date.today().isoformat(),
                                        customer=f"sim_{i}", amount_inr=amt,
                                        kind=random.choice(["new", "recurring"])))
                        booked += amt
                    s.commit()
                total_rev += booked
                await bus.publish({
                    "agent": "system", "kind": "sim",
                    "content": f"{n} leads via {leads[0]['source']} · ₹{booked:,.0f} booked",
                    "meta": {"leads": n, "revenue": booked, "step": i + 1, "steps": steps},
                })
                # fire one risk alert ~60% of the way through
                if i == int(steps * 0.6):
                    with Session(engine) as s:
                        s.add(RiskAlert(
                            business_id=1, severity="high", agent="sales",
                            title="Conversion rate dropped 12%",
                            detail="WhatsApp channel lead quality fell — avg score 68→51 in the last hour.",
                        ))
                        s.commit()
                    await bus.publish({
                        "agent": "system", "kind": "risk",
                        "content": "⚠️ Conversion rate dropped 12% in WhatsApp channel",
                        "meta": {"severity": "high"},
                    })
                await asyncio.sleep(1.2)
            await bus.publish({
                "agent": "system", "kind": "sim_done",
                "content": f"✅ Day complete — {total_leads} leads in, ₹{total_rev:,.0f} booked.",
                "meta": {"leads": total_leads, "revenue": total_rev},
            })

    background.add_task(go)
    return {"status": "started"}


# ------- Boardroom trigger -------
_boardroom_lock = asyncio.Lock()


@app.post("/api/boardroom/run")
async def start_boardroom(background: BackgroundTasks):
    async def emit(payload: dict):
        await bus.publish(payload)

    async def go():
        if _boardroom_lock.locked():
            await bus.publish({"agent": "system", "kind": "phase",
                               "content": "Boardroom already in session…"})
            return
        async with _boardroom_lock:
            try:
                await run_boardroom(emit)
            except Exception as e:
                await bus.publish({"agent": "system", "kind": "error",
                                   "content": f"Boardroom failed: {e}"})

    background.add_task(go)
    return {"status": "started", "ts": datetime.utcnow().isoformat()}


# ------- Copilot -------
class CopilotMessage(BaseModel):
    message: str


COPILOT_SYSTEM = """You are AXIOM, an AI copilot for a D2C founder in India.
You have access to their business KPIs, recent agent recommendations, and competitor signals.
Be direct, specific, and grounded in the numbers you're given. No fluff.
Talk like a smart chief of staff — warm but sharp. Reference specific metrics when relevant."""


@app.post("/api/copilot/chat")
async def copilot(msg: CopilotMessage):
    """Streamed copilot response via Server-Sent Events."""
    kpis = compute_kpis()
    with Session(engine) as s:
        biz = s.exec(select(Business)).first()
        recs = s.exec(select(Recommendation).order_by(Recommendation.ts.desc()).limit(8)).all()

    context = f"""Business: {biz.name if biz else 'demo'} ({biz.industry if biz else 'D2C'})
Business Health: {kpis['business_health']}/100
MRR: ₹{kpis['mrr']:,.0f} · Growth: {kpis['growth_pct']:+.1f}%
Runway: {kpis['runway_months']:.1f} months · Burn multiple: {kpis['burn_multiple']:.2f}
Recent recommendations from your AI team:
{chr(10).join(f'- [{r.agent}] {r.title}: {r.body[:100]}' for r in recs[:5])}

Founder asks: {msg.message}"""

    async def stream():
        async for tok in stream_chat(COPILOT_SYSTEM, context, max_tokens=500):
            yield f"data: {json.dumps({'token': tok})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ------- WebSocket bus -------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await bus.subscribe(ws)
    try:
        await ws.send_text(json.dumps({
            "agent": "system", "kind": "connected",
            "content": "Connected to AXIOM boardroom stream.",
        }))
        while True:
            await ws.receive_text()  # keepalive
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(ws)
