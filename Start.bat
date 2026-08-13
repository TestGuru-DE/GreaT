@echo off
setlocal

:: Port konfigurieren (REQ-4007: GREAT_PORT Umgebungsvariable)
if "%GREAT_PORT%"=="" set GREAT_PORT=8000

echo ================================================
echo  G.R.E.A.T. - TestcaseDesigner
echo ================================================
echo  Starte Server auf Port %GREAT_PORT%...
echo.
echo  Tipp fuer Entwickler: Fuer Hot-Reload auch
echo  "cd frontend ^&^& npm run dev" ausfuehren.
echo ================================================

start "GREAT Server" cmd /k "cd /d %~dp0 && set PYTHONPATH=src && set GREAT_PORT=%GREAT_PORT% && python -m uvicorn src.app.main:app --host 0.0.0.0 --port %GREAT_PORT% --reload"

timeout /t 3 /nobreak >nul

echo.
echo  GREAT laeuft unter: http://localhost:%GREAT_PORT%
echo  API-Docs:           http://localhost:%GREAT_PORT%/docs
echo  Health-Check:       http://localhost:%GREAT_PORT%/health
echo.
pause
