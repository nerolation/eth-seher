#!/usr/bin/env python3
"""Submit a raw transaction to the Ethereum network"""
import argparse
import json
import requests
import sys
import os
import shutil
from datetime import datetime

def load_rpc_config():
    """Load RPC configuration"""
    with open('rpc.json', 'r') as f:
        return json.load(f)

def move_to_submitted(tx_id):
    """Move transaction files from intercepted to submitted directory"""
    intercepted_dir = "intercepted_txs"
    submitted_dir = "submitted_txs"
    
    # Create submitted directory if it doesn't exist
    os.makedirs(submitted_dir, exist_ok=True)
    
    # Find all files with this tx_id
    moved_files = []
    for filename in os.listdir(intercepted_dir):
        if tx_id in filename:
            src = os.path.join(intercepted_dir, filename)
            dst = os.path.join(submitted_dir, filename)
            shutil.move(src, dst)
            moved_files.append(filename)
    
    if moved_files:
        print(f"Moved {len(moved_files)} files to submitted_txs/")
        for f in moved_files:
            print(f"  - {f}")
    
    return moved_files

def submit_raw_transaction(raw_tx, rpc_url=None, chain_id=1, tx_id=None):
    """Submit a raw transaction to the network"""
    if not rpc_url:
        rpc_config = load_rpc_config()
        rpc_url = rpc_config.get(str(chain_id), rpc_config.get(chain_id))
    
    if not rpc_url:
        print(f"Error: No RPC URL configured for chain {chain_id}")
        return None
    
    # Prepare the RPC request
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_sendRawTransaction",
        "params": [raw_tx],
        "id": 1
    }
    
    print(f"Submitting transaction to {rpc_url}")
    print(f"Raw TX: {raw_tx[:66]}...")
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=30)
        result = response.json()
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return None
        
        tx_hash = result.get("result")
        print(f"Transaction submitted successfully!")
        print(f"Transaction hash: {tx_hash}")
        
        # Move files to submitted directory if tx_id is provided
        if tx_id:
            move_to_submitted(tx_id)
        
        return tx_hash
        
    except Exception as e:
        print(f"Error submitting transaction: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Submit a raw Ethereum transaction")
    parser.add_argument("raw_tx", nargs="?", help="Raw transaction hex or path to .raw file")
    parser.add_argument("--file", "-f", help="Path to raw transaction file")
    parser.add_argument("--chain", "-c", type=int, default=1, help="Chain ID (default: 1)")
    parser.add_argument("--rpc", help="Override RPC URL")
    parser.add_argument("--latest", "-l", action="store_true", help="Submit the latest intercepted transaction")
    
    args = parser.parse_args()
    
    raw_tx = None
    
    # Variable to track tx_id for file management
    tx_id = None
    
    # Determine the raw transaction to submit
    if args.latest:
        # Find the latest .raw file in intercepted_txs
        tx_dir = "intercepted_txs"
        if not os.path.exists(tx_dir):
            print("Error: No intercepted transactions found")
            sys.exit(1)
        
        raw_files = [f for f in os.listdir(tx_dir) if f.endswith(".raw")]
        if not raw_files:
            print("Error: No raw transaction files found")
            sys.exit(1)
        
        latest_file = sorted(raw_files)[-1]
        file_path = os.path.join(tx_dir, latest_file)
        print(f"Using latest transaction: {latest_file}")
        
        # Extract tx_id from filename (format: tx_YYYYMMDD_HHMMSS_XXXXXX.raw)
        if latest_file.startswith("tx_"):
            tx_id = latest_file[3:].replace(".raw", "")
        
        with open(file_path, 'r') as f:
            raw_tx = f.read().strip()
            
    elif args.file:
        with open(args.file, 'r') as f:
            raw_tx = f.read().strip()
        
        # Try to extract tx_id from filename if it's from intercepted_txs
        if "intercepted_txs" in args.file and os.path.basename(args.file).startswith("tx_"):
            base_name = os.path.basename(args.file)
            tx_id = base_name[3:].replace(".raw", "").replace(".json", "").replace(".meta", "")
            
    elif args.raw_tx:
        if os.path.exists(args.raw_tx):
            with open(args.raw_tx, 'r') as f:
                raw_tx = f.read().strip()
            
            # Try to extract tx_id from filename if it's from intercepted_txs
            if "intercepted_txs" in args.raw_tx and os.path.basename(args.raw_tx).startswith("tx_"):
                base_name = os.path.basename(args.raw_tx)
                tx_id = base_name[3:].replace(".raw", "").replace(".json", "").replace(".meta", "")
        else:
            raw_tx = args.raw_tx
    else:
        print("Error: No transaction specified. Use --latest, provide hex, or specify a file")
        parser.print_help()
        sys.exit(1)
    
    # Ensure raw_tx starts with 0x
    if not raw_tx.startswith("0x"):
        raw_tx = "0x" + raw_tx
    
    # Submit the transaction
    tx_hash = submit_raw_transaction(raw_tx, args.rpc, args.chain, tx_id)
    
    if tx_hash:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()