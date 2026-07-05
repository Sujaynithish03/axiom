# Citation & Disclosure Sheet — AXIOM OS

Per the sponsor's anti-plagiarism note, every third-party model, API, and library used is disclosed below. All of it is free / open and requires **no paid API keys**. No commercial CRM/BI product (Salesforce, HubSpot, Zoho, etc.) is used or presented as our own work.

## AI model & runtime
| Component | Provider | How it's used | Cost |
|-----------|----------|---------------|------|
| **llama3.2** (3B) | Meta, via Ollama | All AI reasoning — the 6 agents, 6 engines, copilot, engine chatbots, day-recap | Free, runs **locally** |
| **Ollama** | ollama.com | Local model runtime & streaming/JSON API | Free, local |
| nomic-embed-text *(optional)* | Nomic, via Ollama | Embeddings (optional add-on) | Free, local |

No data leaves the machine for inference — the only outbound calls are the two public data feeds below.

## External data (real, live, no API key)
| Source | Endpoint | How it's used |
|--------|----------|---------------|
| **Wikipedia Pageviews API** | `wikimedia.org/api/rest_v1/metrics/pageviews` | Real 30-day category-interest trend on the dashboard + fed to the Strategy engine |
| **Google News RSS** | `news.google.com/rss/search` | Real, on-topic industry headlines with source links |

Both are public, key-less, and rate-limit-friendly (cached 15 min server-side).

## Backend libraries (Python)
FastAPI, Uvicorn, SQLModel, SQLAlchemy, httpx, Pydantic, pydantic-settings, python-multipart, websockets. Database: **SQLite** (local file). All open-source (MIT/BSD/Apache).

## Frontend libraries (JavaScript/TypeScript)
React, Vite, TypeScript, Tailwind CSS, Zustand, Recharts, Framer Motion, lucide-react. All open-source (MIT).

## Data
All business data (GlowVeda Skincare, its GA4/Stripe/CRM streams, competitor signals, simulated leads/revenue) is **synthetic**, generated deterministically by `backend/mocks/seed.py`. It is clearly labelled as simulation mode. No real customer or company data is used.

## What is original
The multi-agent orchestration, the six business engines and their data-rewriting chatbots, the 5D pipeline, the KPI model, the "Simulate a busy day" engine, the LLM-boundary security layer (PII redaction / injection defense / output filtering / audit log), and all UI are original work built for this hackathon.
