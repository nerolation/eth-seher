#!/bin/bash

# Start the Ethereum Transaction Interceptor with Monitor

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║      ETHEREUM TRANSACTION INTERCEPTOR & SIMULATOR       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if interceptor is already running
if lsof -Pi :8545 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8545 is already in use!"
    echo "Kill the existing process or use a different port."
    exit 1
fi

# Create directories if they don't exist
mkdir -p intercepted_txs
mkdir -p submitted_txs

echo "📡 Starting RPC Interceptor on port 8545..."
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│ Configure your wallet:                                 │"
echo "├─────────────────────────────────────────────────────────┤"
echo "│  Network Name:     Local Interceptor                   │"
echo "│  RPC URL:          http://localhost:8545               │"
echo "│  Chain ID:         1                                   │"
echo "│  Currency Symbol:  ETH                                 │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

# Start interceptor in background with logging
echo "Starting interceptor (logs in interceptor.log)..."
python3 -u -m src.eth_interceptor.interceptor > interceptor.log 2>&1 &
INTERCEPTOR_PID=$!

# Wait for interceptor to start
sleep 2

# Check if interceptor started successfully
if ! kill -0 $INTERCEPTOR_PID 2>/dev/null; then
    echo "❌ Failed to start interceptor!"
    cat interceptor.log
    exit 1
fi

echo "✅ Interceptor started (PID: $INTERCEPTOR_PID)"
echo "📊 RPC activity is being logged to interceptor.log"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    # Kill the interceptor
    pkill -f "src.eth_interceptor.interceptor" 2>/dev/null
    sleep 1
    echo "✅ All processes stopped."
    
    # Show summary if transactions were intercepted
    if [ -d "intercepted_txs" ] && [ "$(ls -A intercepted_txs/*.json 2>/dev/null)" ]; then
        echo ""
        echo "📦 Intercepted transactions saved in: intercepted_txs/"
        echo "   $(ls intercepted_txs/*.json 2>/dev/null | wc -l) transaction(s) intercepted"
    fi
    
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Start the monitor in foreground
echo "Starting transaction monitor..."
echo "──────────────────────────────────────────────────────────"
echo ""
python3 -m src.eth_interceptor.monitor

# If monitor exits normally, cleanup
cleanup