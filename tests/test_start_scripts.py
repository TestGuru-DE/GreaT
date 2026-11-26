import re
from pathlib import Path

# Start.bat ruft npm.cmd direkt auf (PowerShell blockiert npm.ps1); beide Schreibweisen gelten.
_BUILD = re.compile(r"\bnpm(?:\.cmd)? run build\b")


def _build_pos(content: str) -> int:
    match = _BUILD.search(content)
    return match.start() if match else -1


def test_start_bat_builds_frontend_for_port_8000():
    # REQ-4015
    content = Path('Start.bat').read_text(encoding='utf-8')
    build_pos = _build_pos(content)
    uvicorn_pos = content.find('python -m uvicorn')
    assert build_pos != -1, 'Start.bat must build the frontend for the 8000-start path'
    assert uvicorn_pos != -1, 'Start.bat must still start uvicorn'
    assert build_pos < uvicorn_pos, 'Frontend build must happen before backend start so port 8000 shows the updated UI'


def test_start_bat_installs_frontend_packages_before_build():
    # Frischer Klon: ohne npm ci fehlt tsc und der Build bricht ab
    content = Path('Start.bat').read_text(encoding='utf-8')
    install_pos = content.find('npm.cmd ci')
    assert install_pos != -1, 'Start.bat must install frontend packages'
    assert install_pos < _build_pos(content), 'Packages must be installed before the build'


def test_start_dev_bat_builds_frontend_before_backend_start():
    # REQ-1202
    content = Path('start-dev.bat').read_text(encoding='utf-8')
    build_pos = _build_pos(content)
    uvicorn_pos = content.find('python -m uvicorn')
    assert build_pos != -1, 'start-dev.bat must build frontend so port 8000 and 5173 share the same UI baseline'
    assert uvicorn_pos != -1, 'start-dev.bat must still start uvicorn'
    assert build_pos < uvicorn_pos, 'Frontend build must happen before backend start in start-dev workflow'
