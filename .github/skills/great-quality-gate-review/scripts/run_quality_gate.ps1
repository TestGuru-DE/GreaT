$ErrorActionPreference = "Continue"
Write-Host "G.R.E.A.T. Quality Gate - PowerShell"
if (Test-Path "src") { $env:PYTHONPATH = "src" }
python -m compileall src tests
python -m pytest tests/ -v
python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
