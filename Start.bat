@echo off
setlocal

rem G.R.E.A.T. Startskript fuer Windows
rem Installiert fehlende oder geaenderte Abhaengigkeiten automatisch:
rem   - Python-Pakete, wenn sich requirements.txt seit der letzten Installation geaendert hat
rem   - Frontend-Pakete, wenn frontend\node_modules fehlt oder package-lock.json geaendert wurde
rem Merker der letzten erfolgreichen Installation liegen in .great-start\ (nicht versioniert).

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

cd /d "%~dp0"
if not exist ".great-start" mkdir ".great-start"

rem ---------------------------------------------------------------
rem [1/4] Python pruefen
rem ---------------------------------------------------------------
echo [1/4] Pruefe Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 goto :old_python

rem ---------------------------------------------------------------
rem [2/4] Python-Pakete (nur wenn requirements.txt geaendert)
rem ---------------------------------------------------------------
fc /b "requirements.txt" ".great-start\requirements.installed" >nul 2>&1
if not errorlevel 1 (
  echo [2/4] Python-Pakete sind aktuell.
  goto :frontend_deps
)
echo [2/4] Installiere Python-Pakete aus requirements.txt...
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :pip_failed
copy /y "requirements.txt" ".great-start\requirements.installed" >nul

:frontend_deps
rem ---------------------------------------------------------------
rem [3/4] Frontend-Pakete (nur wenn fehlend oder package-lock.json geaendert)
rem ---------------------------------------------------------------
call npm.cmd --version >nul 2>&1
if errorlevel 1 goto :no_node
pushd frontend
if errorlevel 1 goto :no_frontend_dir
if not exist "node_modules" goto :npm_install
fc /b "package-lock.json" "..\.great-start\package-lock.installed" >nul 2>&1
if errorlevel 1 goto :npm_install
echo [3/4] Frontend-Pakete sind aktuell.
goto :build

:npm_install
echo [3/4] Installiere Frontend-Pakete (npm ci), das dauert beim ersten Mal etwas...
call npm.cmd ci --no-audit --no-fund
if errorlevel 1 goto :npm_failed
copy /y "package-lock.json" "..\.great-start\package-lock.installed" >nul

:build
rem ---------------------------------------------------------------
rem [4/4] Frontend bauen und Backend starten
rem ---------------------------------------------------------------
echo [4/4] Baue Frontend fuer Port %GREAT_PORT%...
call npm.cmd run build
if errorlevel 1 goto :build_failed
popd

echo.
echo Starte FastAPI Backend...
set PYTHONPATH=src
python -m uvicorn src.app.main:app --host 0.0.0.0 --port %GREAT_PORT%
goto :eof

rem ---------------------------------------------------------------
rem Fehlerbehandlung
rem ---------------------------------------------------------------
:no_python
echo.
echo FEHLER: Python wurde nicht gefunden.
echo        Python 3.10 oder neuer installieren: https://www.python.org/downloads/
echo        Bei der Installation "Add python.exe to PATH" anhaken, dann Start.bat neu starten.
pause
exit /b 1

:old_python
echo.
echo FEHLER: Python 3.10 oder neuer erforderlich.
python --version
pause
exit /b 1

:pip_failed
echo.
echo FEHLER: Installation der Python-Pakete fehlgeschlagen. Bitte die Meldung oben pruefen.
pause
exit /b 1

:no_node
echo.
echo FEHLER: Node.js / npm wurde nicht gefunden.
echo        Node.js LTS installieren: https://nodejs.org/ und Start.bat neu starten.
pause
exit /b 1

:no_frontend_dir
echo.
echo FEHLER: Verzeichnis "frontend" nicht gefunden.
pause
exit /b 1

:npm_failed
echo.
echo FEHLER: Installation der Frontend-Pakete fehlgeschlagen. Bitte die Meldung oben pruefen.
popd
pause
exit /b 1

:build_failed
echo.
echo FEHLER: Frontend-Build fehlgeschlagen. Bitte die Meldung oben pruefen.
echo        Tipp: Ordner frontend\node_modules loeschen und Start.bat erneut starten.
popd
pause
exit /b 1
