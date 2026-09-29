#!/bin/bash
# Start.sh – G.R.E.A.T. Startskript für Linux / Raspberry Pi (Produktiv)
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

# Virtual Environment aktivieren falls vorhanden
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Installiere Abhängigkeiten..."
pip install -r requirements.txt --quiet

# Einmaliger Frontend-Build falls dist/ fehlt
if [ ! -d "frontend/dist" ]; then
    echo "Frontend-Build wird erstellt..."
    cd frontend && npm install --quiet && npm run build --quiet && cd ..
fi

# Port konfigurieren (REQ-4007: GREAT_PORT Umgebungsvariable)
GREAT_PORT=${GREAT_PORT:-8000}

BANNER_PORT_ADJUSTMENT=$(printf ' %.0s' $(seq ${#GREAT_PORT} 5))
# Server starten
echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║  G.R.E.A.T. – Test Case Designer          ║"
echo "║  Port: ${GREAT_PORT}${BANNER_PORT_ADJUSTMENT}                             ║"
echo "║  http://localhost:${GREAT_PORT}${BANNER_PORT_ADJUSTMENT}                  ║"
echo "║  API-Doku: http://localhost:${GREAT_PORT}/docs${BANNER_PORT_ADJUSTMENT}   ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

GREAT_PORT=$GREAT_PORT PYTHONPATH=src python -m uvicorn src.app.main:app --host 0.0.0.0 --port "$GREAT_PORT"

