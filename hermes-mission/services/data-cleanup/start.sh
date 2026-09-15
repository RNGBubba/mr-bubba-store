#!/bin/bash
# Mr Bubba Data Services — Data Cleanup Pipeline Startup Script
# Usage: ./start.sh [once|daemon|api]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="/home/vboxuser/mr-bubba-mission/micro-saas/venv"
PYTHON="$VENV/bin/python3"

# Ensure virtual environment exists
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Virtual environment not found at $VENV"
    echo "Create it with: python3 -m venv $VENV && $VENV/bin/pip install pandas openpyxl numpy requests flask"
    exit 1
fi

# Create directories
mkdir -p "$SCRIPT_DIR"/{input,output,reports,logs,payments}

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

MODE="${1:-daemon}"

case "$MODE" in
    once)
        echo "Running one-time inbox check..."
        "$PYTHON" "$SCRIPT_DIR/pipeline.py" once
        ;;
    daemon)
        echo "Starting Mr Bubba Data Cleanup Service (daemon mode)..."
        echo "Logs: $SCRIPT_DIR/logs/pipeline.log"
        exec "$PYTHON" "$SCRIPT_DIR/pipeline.py" daemon --interval 60
        ;;
    api)
        echo "Starting Mr Bubba Data Cleanup API Server on port ${PORT:-8080}..."
        export FLASK_APP="$SCRIPT_DIR/api_server.py"
        exec "$PYTHON" "$SCRIPT_DIR/api_server.py"
        ;;
    test)
        echo "Running test cleanup..."
        "$PYTHON" "$SCRIPT_DIR/pipeline.py" test-clean --file "$SCRIPT_DIR/input/test_messy_data.csv"
        ;;
    *)
        echo "Usage: $0 {once|daemon|api|test}"
        exit 1
        ;;
esac
