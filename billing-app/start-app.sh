#!/bin/bash
# Start the Shop Billing App (Linux / Mac). Keep this terminal open while using it.
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt --quiet
( sleep 2; xdg-open http://localhost:5000 2>/dev/null || open http://localhost:5000 2>/dev/null ) &
python3 app.py
