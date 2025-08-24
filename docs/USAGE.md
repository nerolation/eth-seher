# Usage Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Intercepting Transactions](#intercepting-transactions)
- [Tracing Transactions](#tracing-transactions)
- [Simulating Transactions](#simulating-transactions)
- [Submitting Transactions](#submitting-transactions)
- [Advanced Features](#advanced-features)

## Quick Start

Start both the interceptor and monitor:
```bash
eth-interceptor start
```

Or using the script directly:
```bash
./scripts/start.sh
```

## Intercepting Transactions

### Configure Your Wallet

1. Open your wallet (MetaMask, Rabby, etc.)
2. Go to Settings → Networks → Add Network
3. Configure:
   - Network Name: `Local Interceptor`
   - RPC URL: `http://localhost:8545`
   - Chain ID: `1`
   - Currency Symbol: `ETH`

### Start Interceptor Only

```bash
eth-interceptor intercept
```

Or on a different port:
```bash
eth-interceptor intercept --port 8546
```

### Monitor Intercepted Transactions

In a separate terminal:
```bash
eth-interceptor monitor
```

## Tracing Transactions

### Trace an Existing Transaction

```bash
eth-interceptor trace 0x457091a405e99a6579cbef5c04d515f2498d90df7b809627a1cb08094d1f9529
```

### Trace with State Changes

```bash
eth-interceptor trace 0x457091a405e99a6579cbef5c04d515f2498d90df7b809627a1cb08094d1f9529 --state
```

### Export to Spreadsheet

```bash
eth-interceptor trace 0x457091a405e99a6579cbef5c04d515f2498d90df7b809627a1cb08094d1f9529 --odf output.ods
```

## Simulating Transactions

### From Raw Transaction

```bash
eth-interceptor trace sim --raw "0x02f88e..." --block 23141310
```

### From JSON File

```bash
eth-interceptor trace sim --raw-tx-json examples/sample_tx.json
```

### With State Changes

```bash
eth-interceptor trace sim --raw-tx-json examples/sample_tx.json --state
```

## Submitting Transactions

### Submit Latest Intercepted

```bash
eth-interceptor submit --latest
```

### Submit Specific File

```bash
eth-interceptor submit intercepted_txs/tx_20231124_123456.raw
```

### Submit to Different Chain

```bash
eth-interceptor submit --latest --chain 11155111
```

## Advanced Features

### Batch Processing

Process multiple transactions from a directory:
```bash
for file in intercepted_txs/*.json; do
    eth-interceptor trace sim --raw-tx-json "$file" --state
done
```

### Custom RPC Endpoints

Override the default RPC:
```bash
ETH_RPC_URL="https://your-rpc-url" eth-interceptor trace 0x...
```

### Debug Mode

Enable verbose logging:
```bash
DEBUG=1 eth-interceptor start
```

### Using with Scripts

Integrate into your scripts:
```python
import subprocess
import json

# Trace a transaction
result = subprocess.run(
    ["eth-interceptor", "trace", "0x...", "--state"],
    capture_output=True,
    text=True
)

# Parse the output
print(result.stdout)
```

## Interactive Monitor Options

When a transaction is intercepted, the monitor shows:

1. **Transaction Details** - From, To, Value, Gas, etc.
2. **Simulation Results** - Call tree and gas usage
3. **Interactive Options**:
   - `1` - Submit transaction to network
   - `2` - Export simulation to ODF
   - `3` - Continue monitoring (default)
   - `4` - Exit

## Tips and Best Practices

1. **Always simulate first** - Check the simulation before submitting
2. **Watch gas usage** - The simulator shows exact gas consumption
3. **Check state changes** - Use `--state` to see balance and storage changes
4. **Save important transactions** - Intercepted transactions are saved in `intercepted_txs/`
5. **Review before submit** - Always review transaction details before submission

## Troubleshooting

### No Transactions Intercepted

- Ensure wallet is configured with `http://localhost:8545`
- Check interceptor is running: `lsof -i :8545`
- Verify chain ID matches your wallet settings

### Simulation Fails

- Ensure your RPC has debug methods enabled
- Check block number is valid
- Verify transaction format is correct

### Cannot Submit Transaction

- Check RPC endpoint is accessible
- Ensure you have the raw transaction file
- Verify chain ID matches the transaction