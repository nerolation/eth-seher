# Ethereum Transaction Tracer

Advanced transaction tracer for Ethereum with comprehensive call trace visualization.

## Features

- Trace existing transactions or simulate raw transactions
- Visual tree structure of all internal calls
- Method signature resolution via 4byte directory
- State change tracking (balances, storage, nonces)
- Gas usage analysis and efficiency metrics
- Support for all transaction types (transfers, tokens, DeFi, failed txs)

## Setup

1. Configure your RPC endpoints in `rpc.json`:
```json
{
  "1": "https://your-mainnet-rpc-url",
  "11155111": "https://your-sepolia-rpc-url"
}
```

2. Install dependencies:
```bash
pip install requests
```

## Usage

### Trace existing transaction
```bash
python3 trace.py 0x457091a405e99a6579cbef5c04d515f2498d90df7b809627a1cb08094d1f9529
```

### Trace with state changes
```bash
python3 trace.py 0x457091a405e99a6579cbef5c04d515f2498d90df7b809627a1cb08094d1f9529 --state
```

### Simulate raw transaction
```bash
python3 trace.py sim --raw "0x02f88e..." --block 23141310
```

### Load transaction from JSON
```bash
python3 trace.py sim --raw-tx-json sample_tx.json --block 23161457
```

## Options

- `--chain`: Chain ID (default: 1 for mainnet)
- `--rpc`: Override RPC URL
- `--block`: Block number for simulation (default: latest)
- `--tracer`: Tracer type (default: callTracer)
- `--state`: Show state changes