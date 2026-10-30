#!/usr/bin/env bash
# One command:  ./run.sh          -> installs deps, runs tests, runs the 5 demo prompts
#               ./run.sh serve    -> starts API on :8000   (POST /chat)
set -e
pip install -q -r requirements.txt
if [ "$1" = "serve" ]; then uvicorn app.main:app --port 8000; else python -m pytest -q && python run_demo.py; fi
