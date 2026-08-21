@echo off
setlocal

if "%GREAT_PORT%"=="" set GREAT_PORT=8000

echo ================================================
echo  G.R.E.A.T. - Entwicklungsmodus
echo ================================================
echo  Backend:  http://localhost:%GREAT_PORT%
echo  Frontend: http://localhost:5173 (Vite Hot-Reload)
echo.
echo  Dieses Fenster = Backend  (Strg+C zum Stoppen)
echo  Ein zweites Fenster startet fuer den Vite-Server
echo  -^> Bitte beide Fenster schliessen zum Beenden!
echo ================================================
echo.

cd /d %~dp0

echo [1/2] Starte Vite Dev-Server in separatem Fenster...
start "GREAT Frontend Dev (Port 5173) - Fenster schliessen zum Stoppen" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo [2/2] Starte FastAPI Backend (dieses Fenster)...
echo.
set PYTHONPATH=src
python -m uvicorn src.app.main:app --host 0.0.0.0 --port %GREAT_PORT% --reload