# Ethereum Transaction Tracer

Advanced transaction tracer for Ethereum with comprehensive call trace visualization.

## Features

- Trace existing transactions or simulate raw transactions
- Visual tree structure of all internal calls
- Method signature resolution via 4byte directory
- State change tracking (balances, storage, nonces)
- Gas usage analysis and efficiency metrics
- Support for all transaction types (transfers, tokens, DeFi, failed txs)
- Export traces to ODF spreadsheet format

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your RPC endpoints in `rpc.json`:
```json
{
  "1": "https://your-mainnet-rpc-url",
  "11155111": "https://your-sepolia-rpc-url"
}
```

**Note:** Make sure your RPC endpoint has debug_traceCall/debug_traceTransaction enabled

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
# Note: 'sim' is required to indicate simulation mode
python3 trace.py sim --raw-tx-json sample_tx.json
```

## Options

- `--chain`: Chain ID (default: 1 for mainnet)
- `--rpc`: Override RPC URL
- `--block`: Block number for simulation (default: latest)
- `--tracer`: Tracer type (default: callTracer)
- `--state`: Show state changes (balance, nonce, storage)
- `--odf`: Export trace to ODF spreadsheet file

### Show State Changes
```bash
# View balance and nonce changes
python3 trace.py sim --raw-tx-json sample_tx.json --state

# View storage changes for token transfers
python3 trace.py sim --raw-tx-json sample_token_tx.json --state
```

### Export to ODF
```bash
python3 trace.py sim --raw-tx-json sample_tx.json --odf output.ods
```

## Sample Transactions

The repository includes two sample transactions:

1. **sample_tx.json** - Simple ETH transfer (0.1 ETH)
2. **sample_token_tx.json** - USDC token transfer (1 USDC)

## Sample Output

Running a simple ETH transfer with `python3 trace.py sim --raw-tx-json sample_tx.json`:

```
════════════════════════════════════════════════════════════════════════════════
  ETHEREUM TRANSACTION TRACE
════════════════════════════════════════════════════════════════════════════════

  ◆ Network: Mainnet
  ◆ Tracer: callTracer

────────────────────────────────────────────────────────────────────────────────

📞 CALL
  From: 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 → 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8
  💰 Value: 100000000.00 Gwei
  ⛽ Gas: 21,000


⛽ GAS METRICS
  • Gas Used: 21,000
  • Gas Limit: 21,000
  • Efficiency: 100.0%
  • [████████████████████████████████████████]

────────────────────────────────────────────────────────────────────────────────

TRANSACTION SUMMARY

  ✅ SUCCESS
  • Total Internal Calls: 0
  • Total Gas Used: 21,000

════════════════════════════════════════════════════════════════════════════════
```

Running a USDC token transfer with `python3 trace.py sim --raw-tx-json sample_token_tx.json`:

```
════════════════════════════════════════════════════════════════════════════════
  ETHEREUM TRANSACTION TRACE
════════════════════════════════════════════════════════════════════════════════

  ◆ Network: Mainnet
  ◆ Tracer: callTracer

────────────────────────────────────────────────────────────────────────────────

📞 CALL
  From: 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 → 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
  Method: transfer(address,uint256)
    └ To: 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8
    └ Amount: 1,000,000
  ⛽ Gas: 45,148
  Output: 0x0000000000000000000000000000000000000000000000000000000000000001

└─🔀 DELEGATECALL
  From: 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 → 0x43506849d7c04f9138d1a2050bbf3a0c054402dd
  Method: transfer(address,uint256)
    └ To: 0xbe0eb53f46cd790cd13851d5eff43d12404d33e8
    └ Amount: 1,000,000
  ⛽ Gas: 16,263
  Output: 0x0000000000000000000000000000000000000000000000000000000000000001


⛽ GAS METRICS
  • Gas Used: 45,148
  • Gas Limit: 90,000
  • Efficiency: 50.2%
  • [████████████████████░░░░░░░░░░░░░░░░░░░]

────────────────────────────────────────────────────────────────────────────────

TRANSACTION SUMMARY

  ✅ SUCCESS
  • Total Internal Calls: 1
  • Total Gas Used: 45,148

════════════════════════════════════════════════════════════════════════════════
```

### With State Changes

Running with `--state` flag shows balance, nonce, and storage changes:

```bash
python3 trace.py sim --raw-tx-json sample_token_tx.json --state
```

Output includes state changes section:

```
💾 STATE CHANGES

  ◆ Account: 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
    💾 Storage:
      Slot 0x57ac49bd70712791ffcf0d97a6f825e3ed867a6f97d95a3364d8a7accb6a1ac3:
        0x00000000000000000000000000000000000000000000000000000000002dc6c0
        → 0x00000000000000000000000000000000000000000000000000000000003d0900
      Slot 0xbf4954ae1137d99a74d9587692d0c99fcc87859496c91311c267c25a44a35f95:
        0x00000000000000000000000000000000000000000000000000000004f53ee064
        → 0x00000000000000000000000000000000000000000000000000000004f52f9e24

  ◆ Account: 0xd8da6bf26964af9d7eed9e03e53415d37aa96045
    💰 Balance: 4.7887 ETH → 4.7878 ETH
    • Nonce: 1573 → 1574
```