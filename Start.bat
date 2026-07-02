@echo off
echo G.R.E.A.T. - Starte Backend und Frontend...
echo.

:: Port konfigurieren (REQ-4007: GREAT_PORT Umgebungsvariable)
if "%GREAT_PORT%"=="" set GREAT_PORT=8000
echo [0/2] Nutze Port: %GREAT_PORT%

:: Backend starten
echo [1/2] Starte FastAPI Backend auf Port %GREAT_PORT%...
start "GREAT Backend" cmd /k "cd /d %~dp0 && set PYTHONPATH=src && set GREAT_PORT=%GREAT_PORT% && python -m uvicorn src.app.main:app --reload --port %GREAT_PORT%"

:: Kurz warten (Backend-Start abwarten)
timeout /t 5 /nobreak > nul

:: Frontend starten
echo [2/2] Starte React Frontend auf Port 5173...
start "GREAT Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend:  http://localhost:%GREAT_PORT%
echo Frontend: http://localhost:5173
echo API-Docs: http://localhost:%GREAT_PORT%/docs
echo.
pause
