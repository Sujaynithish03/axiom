#!/usr/bin/env bash
# AXIOM OS — one-shot dev runner.
# Prereqs (see README):
#   1. Ollama installed + running (`ollama serve` in another terminal, or auto-starts on Mac)
#   2. `ollama pull qwen2.5:7b-instruct` (or your chosen model)
#   3. Python 3.10+ and Node 18+

set -e
cd "$(dirname "$0")"

echo "▶ Checking Ollama…"
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "✗ Ollama not running. Start it with: ollama serve"
  exit 1
fi

# ---- Backend ----
if [ ! -d backend/.venv ]; then
  echo "▶ Creating Python venv…"
  python3 -m venv backend/.venv
fi
echo "▶ Installing backend deps…"
backend/.venv/bin/pip install -q -r backend/requirements.txt

# ---- Frontend ----
if [ ! -d frontend/node_modules ]; then
  echo "▶ Installing frontend deps…"
  (cd frontend && npm install)
fi

# ---- Start both ----
echo "▶ Starting backend (localhost:8000)…"
(cd backend && ../backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload) &
BACK_PID=$!
sleep 2

echo "▶ Starting frontend (localhost:5173)…"
(cd frontend && npm run dev) &
FRONT_PID=$!

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AXIOM OS is live at http://localhost:5173"
echo "  Backend API:         http://localhost:8000/docs"
echo "  Ctrl+C to stop everything."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

trap "kill $BACK_PID $FRONT_PID 2>/dev/null; exit" INT TERM
wait
