#!/bin/bash
# Start.sh – G.R.E.A.T. Startskript für Linux / Raspberry Pi
# REQ-0010: Zielplattform Raspberry Pi
# REQ-4007: GREAT_PORT Umgebungsvariable
#
# Verwendung:
#   chmod +x Start.sh
#   ./Start.sh
#   GREAT_PORT=9000 ./Start.sh  # Custom Port

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python-Version prüfen (mindestens 3.10)
PYTHON=$(command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "FEHLER: Python 3.10+ erforderlich (gefunden: $PYTHON_VERSION)"
    exit 1
fi

echo "Python $PYTHON_VERSION gefunden."

# Python-Abhängigkeiten in .venv (nur neu installieren, wenn requirements.txt geändert)
if [ ! -d ".venv" ]; then
    echo "Erstelle virtuelle Umgebung..."
    $PYTHON -m venv .venv
fi

source .venv/bin/activate

if cmp -s requirements.txt .venv/.great-requirements.installed; then
    echo "Python-Pakete sind aktuell."
else
    echo "Installiere Python-Pakete aus requirements.txt..."
    pip install --disable-pip-version-check -r requirements.txt --quiet
    cp requirements.txt .venv/.great-requirements.installed
fi

# Frontend: Pakete bei Bedarf installieren und bauen.
# Ohne Node.js (z. B. Raspberry Pi) wird ein vorhandener Build verwendet.
if command -v npm >/dev/null 2>&1; then
    pushd frontend >/dev/null
    if [ ! -d node_modules ] || ! cmp -s package-lock.json node_modules/.great-package-lock.installed; then
        echo "Installiere Frontend-Pakete (npm ci)..."
        npm ci --no-audit --no-fund
        cp package-lock.json node_modules/.great-package-lock.installed
    else
        echo "Frontend-Pakete sind aktuell."
    fi
    echo "Baue Frontend..."
    if ! npm run build; then
        echo "FEHLER: Frontend-Build fehlgeschlagen. Tipp: frontend/node_modules löschen und erneut starten."
        exit 1
    fi
    popd >/dev/null
elif [ -f frontend/dist/index.html ]; then
    echo "HINWEIS: npm nicht gefunden – verwende vorhandenen Frontend-Build (frontend/dist)."
else
    echo "FEHLER: Kein Frontend-Build vorhanden und npm nicht gefunden."
    echo "        Node.js LTS installieren (https://nodejs.org/) oder frontend/dist von einem anderen Rechner kopieren."
    exit 1
fi

# Port konfigurieren (REQ-4007: GREAT_PORT Umgebungsvariable)
GREAT_PORT=${GREAT_PORT:-8000}

# Server starten
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  G.R.E.A.T. – Test Case Designer         ║"
echo "║  Port: $GREAT_PORT                             ║"
echo "║  http://localhost:$GREAT_PORT                   ║"
echo "║  API-Doku: http://localhost:$GREAT_PORT/docs    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

GREAT_PORT=$GREAT_PORT uvicorn app.main:app --app-dir src --port $GREAT_PORT

