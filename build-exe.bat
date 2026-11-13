@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   G.R.E.A.T. – Portable Windows EXE Build (REQ-5001)
echo ============================================================
echo.

REM Projekt-Root ermitteln
cd /d %~dp0
set PROJECT_ROOT=%CD%

REM ----------------------------------------------------------
REM Schritt 0: Voraussetzungen pruefen
REM ----------------------------------------------------------
echo [0/5] Pruefe Voraussetzungen...

python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python nicht gefunden. Installiere Python 3.10+ und fuehre dieses Skript erneut aus.
    pause
    exit /b 1
)
echo    Python: OK

where npm >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Node.js/npm nicht gefunden. Installiere Node.js 20+ LTS und fuehre dieses Skript erneut aus.
    pause
    exit /b 1
)
echo    Node.js/npm: OK

REM ----------------------------------------------------------
REM Schritt 1: Python-Abhaengigkeiten installieren
REM ----------------------------------------------------------
echo.
echo [1/5] Installiere Python-Abhaengigkeiten...

pip install -r requirements.txt >nul
if errorlevel 1 (
    echo FEHLER: pip install fehlgeschlagen. Siehe requirements.txt.
    pause
    exit /b 1
)

REM PyInstaller installieren (Build-Tool, kein Runtime-Dependency)
pip install pyinstaller >nul
if errorlevel 1 (
    echo FEHLER: PyInstaller-Installation fehlgeschlagen.
    pause
    exit /b 1
)
echo    Python-Pakete: OK

REM ----------------------------------------------------------
REM Schritt 2: Frontend bauen
REM ----------------------------------------------------------
echo.
echo [2/5] Baue React-Frontend (npm run build)...

pushd frontend
if not exist "node_modules" (
    echo    Installiere Frontend-Abhaengigkeiten...
    call npm install >nul
    if errorlevel 1 (
        echo FEHLER: npm install fehlgeschlagen.
        popd
        pause
        exit /b 1
    )
)

call npm run build >nul
if errorlevel 1 (
    echo FEHLER: npm run build fehlgeschlagen.
    popd
    pause
    exit /b 1
)
popd

if not exist "frontend\dist\index.html" (
    echo FEHLER: frontend\dist\index.html nicht gefunden nach Build.
    pause
    exit /b 1
)
echo    Frontend-Build: OK (frontend\dist\index.html vorhanden)

REM ----------------------------------------------------------
REM Schritt 3: PyInstaller ausfuehren
REM ----------------------------------------------------------
echo.
echo [3/5] Baue GREAT.exe mit PyInstaller...

REM Alte Build-Artefakte bereinigen
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

pyinstaller GREAT.spec --clean
if errorlevel 1 (
    echo FEHLER: PyInstaller-Build fehlgeschlagen.
    pause
    exit /b 1
)

REM ----------------------------------------------------------
REM Schritt 4: Ergebnis pruefen
REM ----------------------------------------------------------
echo.
echo [4/5] Pruefe Build-Ergebnis...

if not exist "dist\GREAT.exe" (
    echo FEHLER: dist\GREAT.exe nicht gefunden nach PyInstaller-Build.
    pause
    exit /b 1
)

for %%I in ("dist\GREAT.exe") do set FILE_SIZE=%%~zI
echo    GREAT.exe: !FILE_SIZE! Bytes

REM ----------------------------------------------------------
REM Schritt 5: Smoke-Test (optional)
REM ----------------------------------------------------------
echo.
echo [5/5] Smoke-Test: Starte GREAT.exe im Hintergrund...

start /B "" dist\GREAT.exe >nul 2>&1

echo    Warte 10 Sekunden auf Server-Start...
timeout /t 10 /nobreak >nul

curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo    WARNUNG: /health-Endpoint antwortet nicht. Der Server startet moeglicherweise noch.
    echo    Versuche es in 30 Sekunden erneut...
    timeout /t 20 /nobreak >nul
    curl -s http://localhost:8000/health >nul 2>&1
    if errorlevel 1 (
        echo    FEHLER: /health-Endpoint antwortet auch nach 30 Sekunden nicht.
        echo    Beende GREAT.exe-Prozess...
        taskkill /im GREAT.exe /f >nul 2>&1
        pause
        exit /b 1
    )
)
echo    /health-Endpoint: OK

echo    Beende GREAT.exe-Prozess...
taskkill /im GREAT.exe /f >nul 2>&1

echo.
echo ============================================================
echo   BUILD ERFOLGREICH!
echo.
echo   GREAT.exe befindet sich in: dist\GREAT.exe
echo.
echo   Zum Starten: Doppelklick auf dist\GREAT.exe
echo   Der Browser oeffnet sich automatisch auf http://localhost:8000
echo.
echo   Zum Stoppen: Task-Manager ^→ GREAT.exe beenden
echo ============================================================
echo.
pause