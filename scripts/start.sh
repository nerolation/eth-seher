#!/bin/bash

# Start Seher - Ethereum Transaction Simulation with Monitor

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Get chain ID and port from environment or use defaults
CHAIN_ID="${CHAIN_ID:-1}"
PORT="${PORT:-8545}"

clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           SEHER - ETHEREUM TRANSACTION SIMULATION        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if interceptor is already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use!"
    echo "Kill the existing process or use a different port."
    exit 1
fi

# Create directories if they don't exist
mkdir -p intercepted_txs
mkdir -p submitted_txs

echo "📡 Starting RPC Interceptor on port $PORT for chain $CHAIN_ID..."
echo ""
echo "┌─────────────────────────────────────────────────────────┐"
echo "│ Configure your wallet:                                 │"
echo "├─────────────────────────────────────────────────────────┤"
echo "│  Network Name:     Local Interceptor                   │"
printf "│  RPC URL:          http://localhost:%-18s │\n" "$PORT"
printf "│  Chain ID:         %-36s │\n" "$CHAIN_ID"
echo "│  Currency Symbol:  ETH                                 │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

# Start interceptor in background with logging
echo "Starting interceptor (logs in interceptor.log)..."
CHAIN_ID=$CHAIN_ID python3 -u -c "import os; os.environ['CHAIN_ID'] = '$CHAIN_ID'; from src.eth_seher.interceptor import app; app.run(host='0.0.0.0', port=$PORT, debug=False, use_reloader=False)" > interceptor.log 2>&1 &
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
    kill $INTERCEPTOR_PID 2>/dev/null
    wait $INTERCEPTOR_PID 2>/dev/null
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
python3 -c "from src.eth_seher.monitor import TransactionMonitor; m = TransactionMonitor(chain_id=$CHAIN_ID); m.watch()"

# If monitor exits normally, cleanup
cleanup