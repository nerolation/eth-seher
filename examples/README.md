# Example Transactions

This directory contains sample transactions for testing and demonstration.

## Files

### sample_tx.json
Simple ETH transfer transaction (0.1 ETH)
- From: vitalik.eth
- To: Binance wallet
- Value: 0.1 ETH
- Gas: 21,000

### sample_token_tx.json
USDC token transfer (1 USDC)
- From: vitalik.eth  
- To: Binance wallet
- Value: 1,000,000 (6 decimals)
- Contract: USDC (0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48)

## Usage

### Simulate ETH Transfer
```bash
eth-interceptor trace sim --raw-tx-json examples/sample_tx.json --state
```

### Simulate Token Transfer
```bash
eth-interceptor trace sim --raw-tx-json examples/sample_token_tx.json --state
```

### Export to Spreadsheet
```bash
eth-interceptor trace sim --raw-tx-json examples/sample_tx.json --odf output.ods
```

## Creating Your Own Examples

1. Intercept a real transaction:
```bash
eth-interceptor start
```

2. Send a transaction through your wallet

3. Find the saved transaction in `intercepted_txs/`

4. Copy to examples directory:
```bash
cp intercepted_txs/tx_*.json examples/my_example.json
```

## Transaction Format

Transactions should be in the following JSON format:
```json
{
  "from": "0x...",
  "to": "0x...",
  "value": "0x...",
  "gas": "0x...",
  "gasPrice": "0x...",
  "input": "0x...",
  "nonce": "0x...",
  "type": "0x2",
  "chainId": "0x1",
  "maxPriorityFeePerGas": "0x...",
  "maxFeePerGas": "0x..."
}
```

All values should be in hexadecimal format.