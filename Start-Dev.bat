@echo off
setlocal

:: Port konfigurieren (REQ-4007: GREAT_PORT Umgebungsvariable)
if "%GREAT_PORT%"=="" set GREAT_PORT=8000

echo ================================================
echo  G.R.E.A.T. - Entwicklungsmodus
echo ================================================
echo  Backend:  http://localhost:%GREAT_PORT%
echo  Frontend: http://localhost:5173 (Vite Hot-Reload)
echo ================================================
echo.

:: Backend starten
echo [1/2] Starte FastAPI Backend auf Port %GREAT_PORT%...
start "GREAT Backend" cmd /k "cd /d %~dp0 && set PYTHONPATH=src && set GREAT_PORT=%GREAT_PORT% && python -m uvicorn src.app.main:app --host 0.0.0.0 --port %GREAT_PORT% --reload"

:: Kurz warten (Backend-Start abwarten)
timeout /t 3 /nobreak >nul

:: Frontend Dev Server starten
echo [2/2] Starte Vite Dev Server auf Port 5173...
start "GREAT Frontend Dev" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
pause
