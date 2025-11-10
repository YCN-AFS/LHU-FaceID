#!/bin/bash
# Start script for LHU FaceID

echo "=== LHU FaceID - Student Face Recognition System ==="
echo ""

# Check if Cassandra is running
echo "Checking Cassandra connection..."
python -c "from cassandra.cluster import Cluster; Cluster(['127.0.0.1']).connect()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Warning: Could not connect to Cassandra. Please ensure Cassandra is running."
    echo ""
fi

# Create logs directory if not exists
mkdir -p logs

# Run the application
echo "Starting LHU FaceID API..."
echo ""
python main.py

