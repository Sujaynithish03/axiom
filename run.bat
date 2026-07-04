@echo off
REM AXIOM OS — Windows dev runner
setlocal

cd /d "%~dp0"

echo Checking Ollama...
curl -s http://localhost:11434/api/tags > nul
if errorlevel 1 (
  echo Ollama not running. Start it with: ollama serve
  exit /b 1
)

if not exist backend\.venv (
  echo Creating Python venv...
  python -m venv backend\.venv
)

echo Installing backend deps...
backend\.venv\Scripts\pip install -q -r backend\requirements.txt

if not exist frontend\node_modules (
  echo Installing frontend deps...
  cd frontend
  call npm install
  cd ..
)

echo Starting backend...
start "AXIOM backend" cmd /k "cd backend && ..\backend\.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 > nul

echo Starting frontend...
start "AXIOM frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo   AXIOM OS is starting up.
echo   Open http://localhost:5173 in your browser.
echo ============================================
