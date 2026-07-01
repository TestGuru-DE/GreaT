#!/bin/bash
# Start.sh – G.R.E.A.T. Startskript für Linux / Raspberry Pi
# REQ-0010: Zielplattform Raspberry Pi
#
# Verwendung:
#   chmod +x Start.sh
#   ./Start.sh

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

# Abhängigkeiten installieren (falls noch nicht geschehen)
if [ ! -d ".venv" ]; then
    echo "Erstelle virtuelle Umgebung..."
    $PYTHON -m venv .venv
fi

source .venv/bin/activate

echo "Installiere Abhängigkeiten..."
pip install -r requirements.txt --quiet

# Server starten
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  G.R.E.A.T. – Test Case Designer         ║"
echo "║  http://localhost:8000                   ║"
echo "║  API-Doku: http://localhost:8000/docs    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

uvicorn app.main:app --reload --app-dir src --reload-dir src --port 8000
