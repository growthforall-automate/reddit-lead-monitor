#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "🌿 MintOS — Personal Brand OS by ThoughtMint"
echo "─────────────────────────────────────────────"

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "→ Created .env from .env.example — add your API keys before using AI features"
    fi
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "→ Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies (PYO3 flag needed for Python 3.14+)
echo "→ Installing dependencies..."
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt -q

echo "→ Starting MintOS at http://localhost:8000"
echo ""

# Open browser
sleep 1 && open "http://localhost:8000" 2>/dev/null &

# Start server
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0
