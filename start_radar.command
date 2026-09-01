#!/bin/bash
# Flight Radar - One Click Start for macOS
# Double-click this file to launch the radar

echo "============================================"
echo "       FLIGHT RADAR - Starting..."
echo "============================================"
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed!"
    echo "Install from: https://www.python.org/downloads/"
    echo "Or run: brew install python"
    read -p "Press Enter to exit"
    exit 1
fi

echo "Found: $(python3 --version)"

# Install dependencies
echo "Installing dependencies..."
pip3 install flask requests -q

# Check if flight_radar.py exists
if [ ! -f "flight_radar.py" ]; then
    echo "[ERROR] flight_radar.py not found!"
    echo "Download from: https://github.com/anserabdullah791-collab/flight-radar"
    read -p "Press Enter to exit"
    exit 1
fi

echo ""
echo "============================================"
echo "  Radar is LIVE! Browser opening..."
echo "  http://localhost:5656"
echo "  Press Ctrl+C to stop"
echo "============================================"
echo ""

# Open browser (macOS)
open http://localhost:5656

# Run radar
python3 flight_radar.py
