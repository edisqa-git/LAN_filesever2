#!/usr/bin/env sh
set -eu

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
pip install -r requirements.txt
PORT="${PORT:-8443}" python app.py
