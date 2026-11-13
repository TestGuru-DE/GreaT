#!/usr/bin/env bash
set -u
echo "G.R.E.A.T. Quality Gate - Bash"
if [ -d "src" ]; then export PYTHONPATH="src"; fi
python -m compileall src tests
python -m pytest tests/ -v
python -m pytest --cov=src --cov-report=term-missing --cov-branch tests/
