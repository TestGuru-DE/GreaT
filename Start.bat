@echo off
setlocal

if "%GREAT_PORT%"=="" set GREAT_PORT=8000

echo ================================================
echo  G.R.E.A.T. - TestcaseDesigner
echo ================================================
echo  Server laeuft auf Port %GREAT_PORT%
echo  URL:      http://localhost:%GREAT_PORT%
echo  API-Docs: http://localhost:%GREAT_PORT%/docs
echo.
echo  Strg+C zum Beenden des Servers
echo ================================================
echo.

cd /d %~dp0
set PYTHONPATH=src
python -m uvicorn src.app.main:app --host 0.0.0.0 --port %GREAT_PORT% --reload
