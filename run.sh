#!/bin/bash
# Script to run LHU FaceID

echo "🚀 Starting LHU FaceID..."

# Kill any existing process on port 8000
echo "Checking port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the application
echo "Starting FastAPI server..."
python main.py


