#!/bin/bash

# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Activate virtual environment and start the app
cd /home/foxcode/Documents/projects/LHU-FaceID
source .venv/bin/activate
python main.py


