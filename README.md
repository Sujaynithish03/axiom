# AXIOM OS

**Your AI Executive Team. Runs entirely on your laptop. Zero API keys, zero cloud bills.**

Six AI agents (CEO, Marketing, Sales, Finance, Strategy, Learning) analyze your business every day, generate ranked decisions, and stream their thinking live to a Bloomberg-terminal-style dashboard. All powered by Ollama and small open models — no GPT, no Claude, no data leaving your machine.

Built to the sponsor 5D framework: **Discover → Design → Deliver → Develop → Dominate.**

---

## 60-second setup

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download the installer from https://ollama.com
```

### 2. Pull the models

```bash
ollama pull qwen2.5:7b-instruct       # main brain (~4.7GB)
ollama pull nomic-embed-text          # embeddings (~275MB, optional)
```

**Low on RAM?** Edit `backend/config.py` and swap in a smaller model:

| Your RAM | Model to pull                          |
|----------|----------------------------------------|
| 8 GB     | `qwen2.5:3b` or `phi3.5:3.8b`          |
| 16 GB    | `qwen2.5:7b-instruct` (recommended)    |
| 24+ GB   | `qwen2.5:14b-instruct` or `llama3.1:8b`|

### 3. Install prerequisites

- **Python 3.10+**
- **Node.js 18+**

### 4. Run everything

```bash
# macOS / Linux
chmod +x run.sh
./run.sh

# Windows
run.bat
```

Open **http://localhost:5173**. Click **Start day**. Watch six agents think.

---

## What you'll see

- **Dashboard** — an **Executive Summary** (the CEO Agent's morning briefing, with a 🔊 *Listen* text-to-speech button) on top of the 9 required KPIs (Business Health, Growth, Revenue Opportunity, Lead Score, Customer Health, Market Readiness, MRR, Runway, Burn Multiple) + a live recommendations feed with **Approve / Execute / Dismiss** buttons. A pulsing **● LIVE** badge shows the numbers are updating on their own.
- **Boardroom** — the signature view. Six agent cards side-by-side, each streaming their token-by-token thinking in real time via WebSocket. When idle, every card shows a live "monitoring" pulse so the room is never dead. Below: a full event log.
- **Copilot** — chat with your AI executive team. Every reply is grounded in your live KPIs and recent agent recommendations.
- **Business** — the onboarding profile. Edit anytime; agents pick up new context on the next boardroom run.

### Always-on, never static

A **live heartbeat** runs in the background the whole time the app is open: it trickles a little real revenue every few seconds (so MRR, Growth, and Business Health drift on their own) and streams a rotating per-agent "monitoring" pulse over the WebSocket. The Dashboard auto-refreshes every 6 seconds, so the trend chart and KPI tiles move without a manual reload. The heartbeat pauses automatically while a boardroom session is running, so it never interferes with the real agents.

Responsive out of the box: on a phone the sidebar collapses into a top bar + bottom tab navigation.

---

## The demo story

Pre-seeded business: **GlowVeda Skincare**, a fictional D2C ayurvedic skincare brand in India. The seed data intentionally contains:
- A bounce-rate spike in the last 3 days (Marketing Agent flags it)
- ~28 stale deals in an active pipeline (Sales Agent prioritizes 3)
- Churn accelerating vs prior period (Finance Agent raises the flag)
- 4 real-looking competitor moves — Kaya price cut, Mamaearth launch, Sugar funding round, Plum negative reviews (Strategy Agent surfaces the biggest threat)

Watch the CEO Agent synthesize all four into a coherent morning briefing.

---

## Architecture

```
Frontend (Vite + React + Tailwind + Recharts, localhost:5173)
    ↓ HTTP + WebSocket
Backend (FastAPI + SQLModel, localhost:8000)
    ↓
Orchestrator (async parallel agents)
    ↓                    ↓
  Agents             Data layer
  ├── CEO            ├── SQLite (business + KPIs + events)
  ├── Marketing      ├── Mock GA4 / Stripe / CRM / Competitors
  ├── Sales          └── (Chroma vector DB — optional add)
  ├── Finance
  ├── Strategy
  └── Learning       ← closes the Develop→Discover loop
    ↓
Ollama (localhost:11434) — Qwen 2.5 7B locally
```

Every layer runs on your machine. The only network call is when Ollama serves a token to the backend, and Ollama runs locally too.

---

## The 5 required + 1 bonus agents

| Agent      | Role               | Reads                          | Produces                                   |
|------------|--------------------|--------------------------------|--------------------------------------------|
| CEO        | Synthesizer        | All 4 tactical agent reports   | Morning briefing + 3 ranked decisions      |
| Marketing  | Growth hacker      | GA4 traffic, funnel, sources   | Campaign recs with ROAS + budget           |
| Sales      | Pipeline doctor    | CRM leads, stages, activity    | Priority deals to unblock                  |
| Finance    | CFO                | Stripe txns, MRR, burn         | Cash decision + spending guardrail         |
| Strategy   | Board advisor      | Competitor signals             | Top threat + strategic bet + stop-doing    |
| Learning   | Feedback loop      | Recommendation history         | Prior adjustments per agent (Develop phase)|

Each agent is defined in `backend/agents/*.py`. All inherit `BaseAgent` (event emission + streaming). Add your own by copying `marketing.py` as a template.

---

## For the "hosted URL" deliverable

The sponsor requires a public URL. Free option: expose your local instance with Cloudflare Tunnel.

```bash
# One-time install
brew install cloudflared          # macOS
# Windows / Linux: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# When ready to demo:
cloudflared tunnel --url http://localhost:5173
```

Cloudflare prints a public `*.trycloudflare.com` URL. Screenshot it, submit it, keep the tunnel running during your demo.

**Alternative:** ngrok — `ngrok http 5173`.

---

## Troubleshooting

**"Ollama not running"** → `ollama serve` in another terminal (or on macOS, just open the Ollama app).

**Agents feel slow** → You're on CPU only. Options:
- Switch to a smaller model in `backend/config.py` (`qwen2.5:3b`).
- Set `OLLAMA_NUM_PARALLEL=1` (default) — running one model at a time is faster than swapping.
- **Fallback for demo day:** point Ollama at [Groq](https://groq.com) — same open models, ~500 tok/s, generous free tier. Change `ollama_host` in `config.py` to the Groq OpenAI-compatible endpoint.

**Agent produces malformed JSON** → Rare with Qwen 2.5, but if it happens, the `llm.py` recovery code extracts the first `{...}` block. If persistent, lower `llm_temperature` in `config.py` to `0.1`.

**Frontend can't reach backend** → Check that both are running. Backend logs go to your terminal.

**Reset all data** → Delete `backend/axiom.db` and restart. Seeder repopulates on startup.

---

## Project layout

```
axiom-os/
├── backend/
│   ├── main.py              # FastAPI app + WebSocket + copilot
│   ├── orchestrator.py      # runs all agents, streams events
│   ├── agents/              # 6 agent implementations
│   ├── mocks/seed.py        # deterministic seed data
│   ├── metrics.py           # computes the 9 KPIs
│   ├── llm.py               # Ollama client (streaming + JSON)
│   ├── db.py, models.py     # SQLModel schema
│   └── config.py            # settings (model, temperature)
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── store.ts         # Zustand + WebSocket
│       └── components/      # Boardroom, Dashboard, Copilot, ...
├── run.sh / run.bat         # one-shot dev runner
└── README.md
```

---

## The pitch

> *"Every other AI dashboard sends your financials to Silicon Valley. AXIOM runs entirely on your laptop. Your revenue, your strategy, your customer data — nothing leaves the room. In a country where MSMEs are terrified of data leaks, that's not a compromise. That's the moat."*

Ship it.
