#!/bin/bash
# GraphRAG Note Service - Startup Script

set -e

echo "=============================================================================="
echo "GraphRAG Note Service - Startup"
echo "=============================================================================="

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    PYTHON_CMD="python"
else
    echo "Running locally"
    PYTHON_CMD="python3"
fi

# Run the main application
echo "Starting GraphRAG Note Service..."
echo ""

cd /app 2>/dev/null || cd "$(dirname "$0")"

export PYTHONPATH=/app/src:${PYTHONPATH}

exec $PYTHON_CMD -m note_service.main
