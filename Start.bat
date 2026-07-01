@echo off
echo G.R.E.A.T. - Starte Backend und Frontend...
echo.

:: Backend starten
echo [1/2] Starte FastAPI Backend auf Port 8000...
start "GREAT Backend" cmd /k "cd /d %~dp0 && set PYTHONPATH=src && python -m uvicorn src.app.main:app --reload --port 8000"

:: Kurz warten
timeout /t 3 /nobreak > nul

:: Frontend starten
echo [2/2] Starte React Frontend auf Port 5173...
start "GREAT Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API-Docs: http://localhost:8000/docs
echo.
pause
