#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
import requests
import json
import os
import sys
import time
import logging
import threading
from datetime import datetime
from web3 import Web3
import hashlib

# Global variables that will be initialized later
CHAIN_ID = None
UP = None
rpc_config = None
initialization_lock = threading.Lock()

def initialize_rpc():
    """Initialize RPC configuration - called when app starts"""
    global CHAIN_ID, UP, rpc_config, rpc_initialized
    
    # Skip if already initialized
    if rpc_initialized:
        return
    
    # Get chain ID from environment
    CHAIN_ID = os.environ.get('CHAIN_ID', '1')
    print(f"\n🔍 Starting with Chain ID: {CHAIN_ID}", flush=True)
    
    # Load RPC configuration
    try:
        with open('rpc.json', 'r') as f:
            rpc_config = json.load(f)
            print(f"✅ Loaded rpc.json with {len(rpc_config)} configured chains", flush=True)
            print(f"   Available chains: {', '.join(str(k) for k in rpc_config.keys())}", flush=True)
    except FileNotFoundError:
        print("❌ ERROR: rpc.json not found! Please create it from rpc.json.example", flush=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in rpc.json: {e}", flush=True)
        sys.exit(1)
    
    # Find RPC endpoint for the chain (NO FALLBACKS)
    UP = rpc_config.get(str(CHAIN_ID)) or rpc_config.get(int(CHAIN_ID))
    if not UP:
        print(f"\n❌ ERROR: No RPC endpoint configured for chain {CHAIN_ID}!", flush=True)
        print(f"   Please add chain {CHAIN_ID} to rpc.json", flush=True)
        print(f"   Available chains: {', '.join(str(k) for k in rpc_config.keys())}", flush=True)
        sys.exit(1)
    
    print(f"✅ Using RPC endpoint: {UP[:50]}..." if len(UP) > 50 else f"✅ Using RPC endpoint: {UP}", flush=True)
    
    # Test the RPC endpoint
    print(f"\n🧪 Testing RPC endpoint...", flush=True)
    try:
        test_response = requests.post(
            UP,
            json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
            timeout=5
        )
        if test_response.status_code == 200:
            result = test_response.json()
            if 'result' in result:
                returned_chain_id = int(result['result'], 16)
                expected_chain_id = int(CHAIN_ID)
                if returned_chain_id == expected_chain_id:
                    print(f"✅ RPC endpoint verified! Chain ID matches: {returned_chain_id}", flush=True)
                else:
                    print(f"⚠️  WARNING: Chain ID mismatch!", flush=True)
                    print(f"   Expected: {expected_chain_id}, Got: {returned_chain_id}", flush=True)
                    print(f"   The RPC endpoint might be for a different chain!", flush=True)
            else:
                print(f"⚠️  WARNING: RPC endpoint returned unexpected response: {result}", flush=True)
        else:
            print(f"⚠️  WARNING: RPC endpoint returned status {test_response.status_code}", flush=True)
    except requests.exceptions.Timeout:
        print(f"⚠️  WARNING: RPC endpoint timed out during test", flush=True)
    except Exception as e:
        print(f"⚠️  WARNING: Could not test RPC endpoint: {e}", flush=True)
    
    # Mark as initialized
    rpc_initialized = True

# Configure Flask logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # Suppress Flask's default logs

app = Flask(__name__)

# Flag to track if RPC has been initialized
rpc_initialized = False

# Methods to block
BLOCK_METHODS = {
    "eth_sendRawTransaction", "eth_sendTransaction", "personal_sendTransaction",
    "parity_sendTransaction", "eth_sendRawPrivateTransaction",
    "eth_sendPrivateTransaction", "mev_sendBundle"
}

# Directories for transaction management
TX_DIR = "intercepted_txs"
SUBMITTED_DIR = "submitted_txs"
os.makedirs(TX_DIR, exist_ok=True)
os.makedirs(SUBMITTED_DIR, exist_ok=True)

# Custom logging with prefixes
def log_rpc(message, level="INFO"):
    """Log RPC-related messages with a distinct prefix"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if level == "TX":
        print(f"\n🔴 [{timestamp}] TRANSACTION INTERCEPTED: {message}", flush=True)
    elif level == "BLOCK":
        print(f"🚫 [{timestamp}] BLOCKED: {message}", flush=True)
    elif level == "RPC":
        print(f"📡 [{timestamp}] RPC: {message}", flush=True)
    elif level == "DEBUG":
        print(f"   [{timestamp}] DEBUG: {message}", flush=True)
    elif level == "ERROR":
        print(f"❌ [{timestamp}] ERROR: {message}", flush=True)
    else:
        print(f"   [{timestamp}] {message}", flush=True)

def decode_raw_tx(raw_tx_hex):
    """Decode raw transaction and return formatted dict"""
    try:
        from eth_account import Account
        from eth_utils import to_hex
        import rlp
        
        # Ensure we have the hex string without 0x prefix
        if raw_tx_hex.startswith('0x'):
            tx_hex = raw_tx_hex[2:]
        else:
            tx_hex = raw_tx_hex
            
        raw_bytes = bytes.fromhex(tx_hex)
        
        # Recover sender address
        from_addr = Account.recover_transaction('0x' + tx_hex)
        
        # Check transaction type by first byte
        tx_type = raw_bytes[0] if raw_bytes[0] < 0x80 else 0
        
        if tx_type == 2:  # EIP-1559 transaction
            # Skip the type byte
            tx_data = raw_bytes[1:]
            decoded = rlp.decode(tx_data)
            
            # EIP-1559 structure: [chain_id, nonce, max_priority_fee_per_gas, max_fee_per_gas, gas_limit, to, value, data, access_list, v, r, s]
            tx_log = {
                "from": from_addr,
                "to": to_hex(decoded[5]) if decoded[5] else "0x",
                "value": to_hex(int.from_bytes(decoded[6], 'big')) if decoded[6] else "0x0",
                "gas": to_hex(int.from_bytes(decoded[4], 'big')) if decoded[4] else "0x5208",
                "gasPrice": to_hex(int.from_bytes(decoded[3], 'big')) if decoded[3] else "0x0",  # max_fee_per_gas
                "input": to_hex(decoded[7]) if decoded[7] else "0x",
                "nonce": to_hex(int.from_bytes(decoded[1], 'big')) if decoded[1] else "0x0",
                "type": "0x2",
                "chainId": to_hex(int.from_bytes(decoded[0], 'big')) if decoded[0] else to_hex(int(CHAIN_ID))
            }
            
            # Add EIP-1559 specific fields
            if decoded[2]:  # max_priority_fee_per_gas
                tx_log["maxPriorityFeePerGas"] = to_hex(int.from_bytes(decoded[2], 'big'))
            if decoded[3]:  # max_fee_per_gas
                tx_log["maxFeePerGas"] = to_hex(int.from_bytes(decoded[3], 'big'))
                
        elif tx_type == 1:  # EIP-2930 transaction
            # Skip the type byte
            tx_data = raw_bytes[1:]
            decoded = rlp.decode(tx_data)
            
            # EIP-2930 structure: [chain_id, nonce, gas_price, gas_limit, to, value, data, access_list, v, r, s]
            tx_log = {
                "from": from_addr,
                "to": to_hex(decoded[4]) if decoded[4] else "0x",
                "value": to_hex(int.from_bytes(decoded[5], 'big')) if decoded[5] else "0x0",
                "gas": to_hex(int.from_bytes(decoded[3], 'big')) if decoded[3] else "0x5208",
                "gasPrice": to_hex(int.from_bytes(decoded[2], 'big')) if decoded[2] else "0x0",
                "input": to_hex(decoded[6]) if decoded[6] else "0x",
                "nonce": to_hex(int.from_bytes(decoded[1], 'big')) if decoded[1] else "0x0",
                "type": "0x1",
                "chainId": to_hex(int.from_bytes(decoded[0], 'big')) if decoded[0] else to_hex(int(CHAIN_ID))
            }
            
        else:  # Legacy transaction
            decoded = rlp.decode(raw_bytes)
            
            # Legacy structure: [nonce, gas_price, gas_limit, to, value, data, v, r, s]
            tx_log = {
                "from": from_addr,
                "to": to_hex(decoded[3]) if decoded[3] else "0x",
                "value": to_hex(int.from_bytes(decoded[4], 'big')) if decoded[4] else "0x0",
                "gas": to_hex(int.from_bytes(decoded[2], 'big')) if decoded[2] else "0x5208",
                "gasPrice": to_hex(int.from_bytes(decoded[1], 'big')) if decoded[1] else "0x0",
                "input": to_hex(decoded[5]) if decoded[5] else "0x",
                "nonce": to_hex(int.from_bytes(decoded[0], 'big')) if decoded[0] else "0x0",
                "type": "0x0",
                "chainId": to_hex(int(CHAIN_ID))  # Try to extract from v value if needed
            }
            
            # Try to extract chainId from v value for legacy transactions
            if len(decoded) > 6 and decoded[6]:
                v = int.from_bytes(decoded[6], 'big') if isinstance(decoded[6], bytes) else decoded[6]
                if v > 35:
                    chain_id = (v - 35) // 2
                    tx_log["chainId"] = to_hex(chain_id)
        
        return tx_log
        
    except Exception as e:
        # Fallback: at least get the sender
        try:
            from eth_account import Account
            from_addr = Account.recover_transaction('0x' + tx_hex if not raw_tx_hex.startswith('0x') else raw_tx_hex)
            return {
                "from": from_addr,
                "to": "0x",
                "value": "0x0",
                "gas": "0x5208",
                "gasPrice": "0x0",
                "input": "0x",
                "nonce": "0x0",
                "type": "0x0",
                "chainId": to_hex(int(CHAIN_ID)),
                "note": "Partial decode - showing sender only"
            }
        except Exception as e2:
            return {"error": str(e2), "raw": raw_tx_hex[:100]}

def save_transaction(method, params, tx_decoded):
    """Save intercepted transaction to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tx_id = f"{timestamp}_{int(time.time() * 1000000) % 1000000}"
    
    # Save decoded transaction JSON
    json_file = os.path.join(TX_DIR, f"tx_{tx_id}.json")
    with open(json_file, 'w') as f:
        json.dump(tx_decoded, f, indent=2)
    
    # Save raw transaction if available
    raw_file = None
    if method == "eth_sendRawTransaction" and params and len(params) > 0:
        raw_file = os.path.join(TX_DIR, f"tx_{tx_id}.raw")
        with open(raw_file, 'w') as f:
            f.write(params[0])
    
    # Save metadata
    meta_file = os.path.join(TX_DIR, f"tx_{tx_id}.meta")
    with open(meta_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "method": method,
            "tx_id": tx_id,
            "json_file": json_file,
            "raw_file": raw_file if method == "eth_sendRawTransaction" else None
        }, f, indent=2)
    
    return tx_id

def log_transaction(method, params):
    """Log transaction details based on method type"""
    tx_decoded = None
    raw_tx = None
    
    if method == "eth_sendRawTransaction":
        if params and len(params) > 0:
            raw_tx = params[0]
            tx_decoded = decode_raw_tx(raw_tx)
            log_rpc(f"{method}", "TX")
            print(f"   From: {tx_decoded.get('from', 'unknown')}")
            print(f"   To:   {tx_decoded.get('to', 'unknown')}")
            print(f"   Raw:  {raw_tx[:66]}...")
    elif method in ["eth_sendTransaction", "personal_sendTransaction", "parity_sendTransaction"]:
        if params and len(params) > 0:
            tx = params[0]
            # These methods already have decoded transaction objects
            tx_decoded = {
                "from": tx.get("from", "0x"),
                "to": tx.get("to", "0x"),
                "value": tx.get("value", "0x0"),
                "gas": tx.get("gas", "0x5208"),
                "gasPrice": tx.get("gasPrice", "0x0"),
                "input": tx.get("data", tx.get("input", "0x")),
                "nonce": tx.get("nonce", "0x0"),
                "type": "0x0",
                "chainId": to_hex(int(CHAIN_ID))
            }
            log_rpc(f"{method}", "TX")
            print(f"   From: {tx_decoded.get('from', 'unknown')}")
            print(f"   To:   {tx_decoded.get('to', 'unknown')}")
    else:
        log_rpc(f"{method}", "TX")
    
    # Save transaction to file
    tx_id = None
    if tx_decoded and not tx_decoded.get("error"):
        tx_id = save_transaction(method, params, tx_decoded)
        print(f"   💾 Saved as: tx_{tx_id}")
    
    return tx_decoded, raw_tx, tx_id

def generate_tx_hash(raw_tx):
    """Generate a deterministic transaction hash from raw transaction"""
    try:
        # Use keccak256 to generate a proper transaction hash
        w3 = Web3()
        if raw_tx.startswith('0x'):
            raw_tx = raw_tx[2:]
        tx_bytes = bytes.fromhex(raw_tx)
        tx_hash = w3.keccak(tx_bytes).hex()
        # Ensure it has 0x prefix
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash
        log_rpc(f"Generated tx hash: {tx_hash}", "DEBUG")
        return tx_hash
    except Exception as e:
        log_rpc(f"Error generating tx hash: {e}", "ERROR")
        # Fallback to a random hash
        import hashlib
        fallback_hash = '0x' + hashlib.sha256(raw_tx.encode()).hexdigest()
        log_rpc(f"Using fallback hash: {fallback_hash}", "DEBUG")
        return fallback_hash

def intercept_response(req_id, raw_tx=None):
    """Return a valid transaction hash response for intercepted transactions"""
    if raw_tx:
        tx_hash = generate_tx_hash(raw_tx)
    else:
        # Generate a placeholder hash if no raw tx available
        timestamp = str(time.time()).encode()
        tx_hash = '0x' + hashlib.sha256(timestamp).hexdigest()
        log_rpc(f"Generated placeholder hash: {tx_hash}", "DEBUG")
    
    log_rpc(f"Returning intercepted response with tx hash: {tx_hash}", "BLOCK")
    
    # Return a valid response that MetaMask will accept
    return {"jsonrpc": "2.0", "id": req_id, "result": tx_hash}

# Counter for RPC calls
rpc_counter = {"count": 0, "last_print": 0}

def ensure_rpc_initialized():
    """Ensure RPC is initialized before handling requests"""
    global rpc_initialized
    if not rpc_initialized:
        with initialization_lock:
            # Double-check inside the lock
            if not rpc_initialized:
                initialize_rpc()

@app.route("/", methods=["GET", "POST"])
def rpc():
    # Initialize RPC on first request
    ensure_rpc_initialized()
    if request.method == "GET":
        return "RPC Interceptor Active", 200
    
    try:
        body = request.get_json(force=True)
        
        # Log incoming RPC call
        if isinstance(body, dict):
            method = body.get("method", "unknown")
            log_rpc(f"{method} (id: {body.get('id', 'none')})", "RPC")
            if method in BLOCK_METHODS:
                params = body.get("params", [])
                if params:
                    log_rpc(f"  Parameters: {str(params[0])[:100]}...", "DEBUG")
        elif isinstance(body, list):
            log_rpc(f"Batch request with {len(body)} calls", "RPC")
            for req in body:
                method = req.get("method", "unknown")
                log_rpc(f"  - {method}", "DEBUG")
        
        # Handle batch requests
        if isinstance(body, list):
            responses = []
            for req in body:
                method = req.get("method")
                if method in BLOCK_METHODS:
                    tx_decoded, raw_tx, tx_id = log_transaction(method, req.get("params", []))
                    # Return a valid tx hash response
                    if method == "eth_sendRawTransaction" and req.get("params"):
                        responses.append(intercept_response(req.get("id"), req.get("params")[0]))
                    else:
                        responses.append(intercept_response(req.get("id")))
                else:
                    # Forward non-blocked requests
                    try:
                        resp = requests.post(UP, json=req, timeout=30)
                        responses.append(resp.json())
                        rpc_counter["count"] += 1
                    except Exception as e:
                        responses.append({"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32603, "message": str(e)}})
            return jsonify(responses)
        
        # Handle single request
        method = body.get("method")
        if method in BLOCK_METHODS:
            tx_decoded, raw_tx, tx_id = log_transaction(method, body.get("params", []))
            # Return a valid tx hash response
            if method == "eth_sendRawTransaction" and body.get("params"):
                return jsonify(intercept_response(body.get("id"), body.get("params")[0]))
            else:
                return jsonify(intercept_response(body.get("id")))
        
        # Forward non-blocked request
        try:
            upstream = requests.post(UP, json=body, timeout=30)
            rpc_counter["count"] += 1
            
            # Log response status
            log_rpc(f"  → Forwarded to upstream (status: {upstream.status_code})", "DEBUG")
            
            return Response(upstream.content, status=upstream.status_code, headers={"Content-Type": "application/json"})
        except Exception as e:
            log_rpc(f"Error forwarding request: {e}", "ERROR")
            return jsonify({"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32603, "message": str(e)}})
            
    except Exception as e:
        return jsonify({"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}}), 400

if __name__ == "__main__":
    # Initialize RPC when running directly
    ensure_rpc_initialized()
    
    # Chain names for common networks
    CHAIN_NAMES = {
        "1": "Ethereum Mainnet",
        "11155111": "Sepolia Testnet", 
        "5": "Goerli Testnet",
        "10": "Optimism",
        "137": "Polygon",
        "42161": "Arbitrum One",
        "8453": "Base"
    }
    
    chain_name = CHAIN_NAMES.get(str(CHAIN_ID), f"Chain {CHAIN_ID}")
    
    print("\n" + "="*60, flush=True)
    print("  🔮 SEHER - RPC INTERCEPTOR READY", flush=True)
    print("="*60, flush=True)
    print(f"  Network:   {chain_name} (ID: {CHAIN_ID})", flush=True)
    print(f"  Port:      8545", flush=True)
    print(f"  TX Dir:    {TX_DIR}/", flush=True)
    print("="*60, flush=True)
    print("\n  💡 Configure your wallet:", flush=True)
    print(f"     RPC URL: http://localhost:8545", flush=True)
    print(f"     Chain ID: {CHAIN_ID}", flush=True)
    print("\n  🔍 Monitoring for transactions...\n", flush=True)
    print("-" * 60, flush=True)
    
    app.run(host="0.0.0.0", port=8545, debug=False, use_reloader=False)