#!/bin/bash
# Startup script for AI service

echo "=========================================="
echo "AGBOT AI Pest Detection Service"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the service
echo ""
echo "Starting AI service on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""
python3 main.py
