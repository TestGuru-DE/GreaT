from pathlib import Path


def test_start_bat_builds_frontend_for_port_8000():
    # REQ-4015
    content = Path('Start.bat').read_text(encoding='utf-8')
    build_pos = content.find('npm run build')
    uvicorn_pos = content.find('python -m uvicorn')
    assert build_pos != -1, 'Start.bat must build the frontend for the 8000-start path'
    assert uvicorn_pos != -1, 'Start.bat must still start uvicorn'
    assert build_pos < uvicorn_pos, 'Frontend build must happen before backend start so port 8000 shows the updated UI'
