# -*- mode: python ; coding: utf-8 -*-
# REQ-5001: PyInstaller Spec fuer G.R.E.A.T. Portable Windows-EXE
# RISK-B-002: Kein Installationspaket fuer Nicht-Techniker

import os
from pathlib import Path

# Pfade relativ zum Projektroot (wo GREAT.spec liegt)
project_root = Path(__file__).parent
src_dir = project_root / "src"
frontend_dist = project_root / "frontend" / "dist"

# Daten-Dateien: Frontend-Build einbetten
datas = []
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))
else:
    print("WARNUNG: frontend/dist existiert nicht. Fuehre zuerst 'npm run build' aus.")

# PySide6-Plugins fuer portables EXE (QT-Bildschirm, Platform-Plugins)
# Diese werden in _MEIxxxxx extrahiert und von PySide6 automatisch gefunden
hiddenimports = [
    "uvicorn",
    "uvicorn.main",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.config",
    "fastapi",
    "fastapi.staticfiles",
    "sqlalchemy",
    "jinja2",
    "alembic",
    "structlog",
    "dotenv",
]

a = Analysis(
    [str(src_dir / "app" / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Nicht noetig fuer portable EXE
        "pytest",
        "playwright",
        "setuptools",
        "tkinter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_modules=[],
    name="GREAT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Kein Konsolenfenster – REQ-5001: Nicht-technische Nutzer
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)