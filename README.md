# AXIOM OS

**Your AI Executive Team. Runs entirely on your laptop. Zero API keys, zero cloud bills.**

Six AI agents (CEO, Marketing, Sales, Finance, Strategy, Learning) analyze your business every day, generate ranked decisions, and stream their thinking live to a Bloomberg-terminal-style dashboard. All powered by Ollama and small open models — no GPT, no Claude, no data leaving your machine.

Built to the sponsor 5D framework: **Discover → Design → Deliver → Develop → Dominate.**

---

## The 6 business engines

On top of the live agent boardroom, AXIOM exposes the sponsor's six AI-driven **engines** — each a workspace that runs a structured local-LLM generation over your real business data:

| Engine | What it produces |
|--------|------------------|
| **Strategy** | Market research, brand positioning, AI pricing tiers, go-to-market moves |
| **Marketing** | A 360° multi-channel plan — channels with budgets & expected ROAS, big idea, ready ad copy |
| **Lead Gen** | Target segments, digital campaigns, a ready-to-send WhatsApp broadcast, physical lead ideas |
| **Sales** | A sales funnel, priority actions, and a draft outreach email |
| **Analytics** | A 3-month MRR forecast, competitive insight, and a quarterly roadmap |
| **Customer Success** | Customer-health read, at-risk segments, success playbook, chatbot greeting |

Each engine lives at `POST /api/engines/{key}/run` and persists its latest output. The frontend renders any engine's output through one generic recursive view, so the shape is resilient to small-model variation.

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

## Security (the LLM boundary)

Four protections wrap every AI call — see the **Security** tab in the app:

1. **PII redaction** — emails, phones, PAN/GST and card numbers are masked to typed placeholders (`[EMAIL_1]`) before any text reaches the model. Real personal data never crosses the boundary.
2. **Injection defense** — untrusted user text is fenced in `<untrusted_content>` tags and blatant override phrases ("ignore previous instructions") are neutralised; the model is told to treat it as data, not commands.
3. **Output filtering** — every response is scanned for leaked secrets (OpenAI/AWS/GitHub/Slack/Google key patterns) and scrubbed to `[REDACTED_SECRET]`.
4. **Audit log** — every LLM call is recorded append-only with SHA-256 hashes and counts (never raw content) at `GET /api/audit`.

*Multi-tenant Row-Level Security / JWT scoping is a production concern for the hosted multi-business deployment; this local single-tenant build focuses on the LLM-boundary protections above, where the real leak risk sits.*

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
