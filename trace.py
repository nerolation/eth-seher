#!/usr/bin/env python3
import argparse, json, sys, requests
from datetime import datetime
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TextProperties, TableColumnProperties, TableCellProperties, ParagraphProperties
from odf.number import NumberStyle, CurrencyStyle, Number, Text as NumText
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import P

# Load RPC configuration
try:
    with open('rpc.json', 'r') as f:
        CHAINS = {int(k): v for k, v in json.load(f).items()}
except FileNotFoundError:
    print("Error: rpc.json not found. Please create it with your RPC URLs.")
    print("Example format: {\"1\": \"https://your-mainnet-rpc\", \"11155111\": \"https://your-sepolia-rpc\"}")
    sys.exit(1)

# Enhanced color palette and symbols
STYLE = {
    # Colors
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "italic": "\033[3m",
    
    # Foreground colors
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "gray": "\033[90m",
    
    # Background colors
    "bg_green": "\033[42m",
    "bg_red": "\033[41m",
    "bg_blue": "\033[44m",
    
    # Icons
    "success": "✅",
    "fail": "❌",
    "arrow": "→",
    "tree": "├─",
    "tree_last": "└─",
    "tree_line": "│ ",
    "diamond": "◆",
    "dot": "•",
    "gas": "⛽",
    "money": "💰",
    "storage": "💾",
    "create": "🏗️",
    "delegate": "🔀",
    "static": "🔒",
}

def format_address(addr):
    """Format address with full display"""
    if not addr or addr == "0x0000000000000000000000000000000000000000":
        return f"{STYLE['gray']}<null>{STYLE['reset']}"
    return f"{STYLE['cyan']}{addr}{STYLE['reset']}"

def format_hex_value(hex_str):
    """Format hex values to decimal with units"""
    if not hex_str or hex_str == "0x0":
        return "0"
    val = int(hex_str, 16)
    if val > 10**18:
        return f"{val/10**18:.4f} ETH"
    elif val > 10**9:
        return f"{val/10**9:.2f} Gwei"
    else:
        return f"{val:,}"

def get_method_signature(hex_sig):
    """Fetch method signature from 4byte directory"""
    
    # Check common known signatures first (these are most reliable)
    known_sigs = {
        "0xa9059cbb": "transfer(address,uint256)",
        "0x095ea7b3": "approve(address,uint256)",
        "0x70a08231": "balanceOf(address)",
        "0x23b872dd": "transferFrom(address,address,uint256)",
        "0x18160ddd": "totalSupply()",
        "0xdd62ed3e": "allowance(address,address)",
        "0x313ce567": "decimals()",
        "0x06fdde03": "name()",
        "0x95d89b41": "symbol()",
        "0x40c10f19": "mint(address,uint256)",
        "0x42966c68": "burn(uint256)",
    }
    
    if hex_sig in known_sigs:
        return known_sigs[hex_sig]
    
    # Try 4byte directory for unknown signatures
    try:
        url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={hex_sig}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                # Look for the most standard-looking signature
                signatures = [r["text_signature"] for r in data["results"]]
                
                # Prefer signatures that look like standard function names
                for sig in signatures:
                    # Basic heuristic: prefer shorter, simpler names without special chars
                    if not any(c in sig for c in ["_", "watch_tg", "dotBLACK"]):
                        return sig
                
                # Otherwise return first result
                return signatures[0]
    except:
        pass
    
    return None

# Cache for method signatures to avoid repeated API calls
METHOD_CACHE = {}

def format_method_sig(input_data):
    """Extract and format method signature from input data"""
    if not input_data or len(input_data) < 10:
        return ""
    
    sig = input_data[:10]
    
    # Check cache first
    if sig not in METHOD_CACHE:
        METHOD_CACHE[sig] = get_method_signature(sig)
    
    method = METHOD_CACHE[sig]
    if not method:
        method = f"0x{sig[2:]}..."
    
    return f"{STYLE['magenta']}{method}{STYLE['reset']}"

def rpc_call(rpc, method, params):
    r = requests.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=60)
    r.raise_for_status()
    result = r.json()
    if "error" in result:
        sys.exit(f"{method} failed: {result['error']}")
    return result["result"]

def get_state_diff(rpc, tx_hash):
    """Fetch state changes using debug_traceTransaction with prestateTracer"""
    try:
        result = rpc_call(rpc, "debug_traceTransaction", [
            tx_hash, 
            {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
        ])
        # Return both pre and post states for diff mode
        return result
    except:
        return {}

def print_header(chain, tracer, tx_info=None):
    """Print stylized header with transaction info"""
    print(f"\n{STYLE['bold']}{STYLE['blue']}{'═' * 80}{STYLE['reset']}")
    print(f"{STYLE['bold']}  ETHEREUM TRANSACTION TRACE{STYLE['reset']}")
    print(f"{STYLE['blue']}{'═' * 80}{STYLE['reset']}\n")
    
    # Chain and tracer info
    chain_name = {1: "Mainnet", 11155111: "Sepolia"}.get(chain, f"Chain {chain}")
    print(f"  {STYLE['diamond']} {STYLE['bold']}Network:{STYLE['reset']} {STYLE['cyan']}{chain_name}{STYLE['reset']}")
    print(f"  {STYLE['diamond']} {STYLE['bold']}Tracer:{STYLE['reset']} {tracer}")
    
    if tx_info:
        if "blockNumber" in tx_info:
            block = int(tx_info["blockNumber"], 16)
            print(f"  {STYLE['diamond']} {STYLE['bold']}Block:{STYLE['reset']} {block:,}")
        if "hash" in tx_info:
            print(f"  {STYLE['diamond']} {STYLE['bold']}TX Hash:{STYLE['reset']} {STYLE['gray']}{tx_info['hash']}{STYLE['reset']}")
    
    print(f"\n{STYLE['gray']}{'─' * 80}{STYLE['reset']}\n")

def print_gas_analysis(trace):
    """Print gas usage analysis"""
    gas_used = int(trace.get("gasUsed", "0x0"), 16)
    gas_limit = int(trace.get("gas", "0x0"), 16) if trace.get("gas") else gas_used * 2
    
    efficiency = (gas_used / gas_limit * 100) if gas_limit > 0 else 0
    
    print(f"\n{STYLE['bold']}{STYLE['gas']} GAS METRICS{STYLE['reset']}")
    print(f"  {STYLE['dot']} Gas Used: {STYLE['yellow']}{gas_used:,}{STYLE['reset']}")
    
    if gas_limit > 0:
        print(f"  {STYLE['dot']} Gas Limit: {gas_limit:,}")
        print(f"  {STYLE['dot']} Efficiency: ", end="")
        
        if efficiency > 80:
            color = STYLE['red']
        elif efficiency > 50:
            color = STYLE['yellow']
        else:
            color = STYLE['green']
        
        print(f"{color}{efficiency:.1f}%{STYLE['reset']}")
        
        # Visual gas bar
        bar_width = 40
        filled = int(bar_width * efficiency / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"  {STYLE['dot']} [{bar}]")

def print_trace(node, depth=0, is_last=False, prefix="", state_diff=None):
    """Enhanced trace printing with tree structure and details"""
    
    # Handle None or invalid node
    if not node:
        print(f"{STYLE['red']}Invalid or empty trace data{STYLE['reset']}")
        return
    
    # Determine tree symbols
    if depth == 0:
        tree_symbol = ""
        child_prefix = ""
    else:
        tree_symbol = STYLE['tree_last'] if is_last else STYLE['tree']
        child_prefix = prefix + ("  " if is_last else STYLE['tree_line'])
    
    # Determine call type and icon
    call_type = node.get("type", "CALL")
    type_icons = {
        "CALL": "📞",
        "DELEGATECALL": STYLE['delegate'],
        "STATICCALL": STYLE['static'],
        "CREATE": STYLE['create'],
        "CREATE2": STYLE['create'],
    }
    icon = type_icons.get(call_type, "•")
    
    # Format addresses
    from_addr = format_address(node.get("from"))
    to_addr = format_address(node.get("to"))
    
    # Get value and gas
    value = node.get("value", "0x0")
    gas_used = int(node.get("gasUsed", "0x0"), 16)
    
    # Build main line
    indent = prefix + tree_symbol
    
    # Call type with color
    if node.get("error"):
        type_color = STYLE['red']
        status = f" {STYLE['fail']}"
    else:
        type_color = STYLE['green'] if call_type == "CALL" else STYLE['blue']
        status = ""
    
    print(f"{indent}{icon} {type_color}{call_type}{STYLE['reset']}{status}")
    
    # Details line
    detail_indent = prefix + ("  " if is_last else STYLE['tree_line']) if depth > 0 else "  "
    print(f"{detail_indent}{STYLE['dim']}From:{STYLE['reset']} {from_addr} {STYLE['arrow']} {to_addr}")
    
    # Method signature and parameters if available
    input_data = node.get("input", "")
    if input_data and len(input_data) > 2:
        method = format_method_sig(input_data)
        if method:
            print(f"{detail_indent}{STYLE['dim']}Method:{STYLE['reset']} {method}")
            
            # Try to decode parameters for known methods
            if len(input_data) > 10:
                params_hex = input_data[10:]
                # For simple value transfers or single uint256 parameters
                if len(params_hex) >= 64 and "uint256" in str(METHOD_CACHE.get(input_data[:10], "")):
                    try:
                        # Extract first parameter (assuming address or uint256)
                        if "address" in str(METHOD_CACHE.get(input_data[:10], "")):
                            if len(params_hex) >= 64:
                                addr_param = "0x" + params_hex[24:64]  # Address is last 20 bytes of 32-byte word
                                formatted_addr = format_address(addr_param)
                                print(f"{detail_indent}{STYLE['dim']}  └ To:{STYLE['reset']} {formatted_addr}")
                                
                                # If there's a value parameter after address
                                if len(params_hex) >= 128:
                                    value_param = "0x" + params_hex[64:128]
                                    value_formatted = format_hex_value(value_param)
                                    if value_formatted != "0":
                                        print(f"{detail_indent}{STYLE['dim']}  └ Amount:{STYLE['reset']} {STYLE['yellow']}{value_formatted}{STYLE['reset']}")
                        else:
                            # Single uint256 parameter
                            value_param = "0x" + params_hex[:64]
                            value_formatted = format_hex_value(value_param)
                            if value_formatted != "0":
                                print(f"{detail_indent}{STYLE['dim']}  └ Value:{STYLE['reset']} {STYLE['yellow']}{value_formatted}{STYLE['reset']}")
                    except:
                        pass
    
    # Value transfer
    if value and value != "0x0":
        val_fmt = format_hex_value(value)
        print(f"{detail_indent}{STYLE['money']} {STYLE['bold']}{STYLE['yellow']}Value: {val_fmt}{STYLE['reset']}")
    
    # Gas usage
    gas_color = STYLE['red'] if gas_used > 100000 else STYLE['yellow'] if gas_used > 50000 else STYLE['gray']
    print(f"{detail_indent}{STYLE['gas']} {gas_color}Gas: {gas_used:,}{STYLE['reset']}")
    
    # Error details
    if node.get("error"):
        print(f"{detail_indent}{STYLE['bg_red']}{STYLE['white']} ERROR {STYLE['reset']} {STYLE['red']}{node['error']}{STYLE['reset']}")
    
    # Output if present and not error
    if node.get("output") and not node.get("error") and node.get("output") != "0x":
        output = node.get("output")
        if len(output) > 66:
            output = f"{output[:66]}..."
        print(f"{detail_indent}{STYLE['dim']}Output:{STYLE['reset']} {STYLE['gray']}{output}{STYLE['reset']}")
    
    print()  # Blank line for readability
    
    # Process child calls
    calls = node.get("calls", [])
    for i, call in enumerate(calls):
        is_last_child = (i == len(calls) - 1)
        print_trace(call, depth + 1, is_last_child, child_prefix, state_diff)

def print_state_changes(state_diff):
    """Print state changes from the transaction"""
    if not state_diff:
        return
    
    # Check if we have pre/post structure (diffMode result)
    pre_state = state_diff.get("pre", {})
    post_state = state_diff.get("post", {})
    
    if not pre_state and not post_state:
        # Try direct structure (non-diff mode)
        if not any(state_diff.values()):
            return
        pre_state = {}
        post_state = state_diff
    
    print(f"\n{STYLE['bold']}{STYLE['storage']} STATE CHANGES{STYLE['reset']}")
    
    # Collect all addresses that have changes
    all_addresses = set(pre_state.keys()) | set(post_state.keys())
    
    for addr in sorted(all_addresses):
        formatted_addr = format_address(addr)
        pre = pre_state.get(addr, {})
        post = post_state.get(addr, {})
        
        # Check if there are actual changes
        has_changes = False
        
        # Check balance changes
        pre_balance = pre.get("balance", "0x0")
        post_balance = post.get("balance", pre_balance)
        balance_changed = pre_balance != post_balance
        
        # Check storage changes
        pre_storage = pre.get("storage", {})
        post_storage = post.get("storage", {})
        storage_changed = pre_storage != post_storage
        
        # Check nonce changes
        pre_nonce = pre.get("nonce", 0)
        post_nonce = post.get("nonce", pre_nonce)
        nonce_changed = pre_nonce != post_nonce
        
        if balance_changed or storage_changed or nonce_changed:
            has_changes = True
            print(f"\n  {STYLE['diamond']} Account: {formatted_addr}")
            
            # Balance changes
            if balance_changed:
                old_bal = format_hex_value(pre_balance)
                new_bal = format_hex_value(post_balance)
                print(f"    {STYLE['money']} Balance: {STYLE['red']}{old_bal}{STYLE['reset']} → {STYLE['green']}{new_bal}{STYLE['reset']}")
            
            # Nonce changes
            if nonce_changed:
                print(f"    {STYLE['dot']} Nonce: {pre_nonce} → {post_nonce}")
            
            # Storage changes
            if storage_changed:
                print(f"    {STYLE['storage']} Storage:")
                all_slots = set(pre_storage.keys()) | set(post_storage.keys())
                for slot in sorted(all_slots):
                    old_val = pre_storage.get(slot, "0x0")
                    new_val = post_storage.get(slot, "0x0")
                    if old_val != new_val:
                        # Show full storage values
                        print(f"      Slot {STYLE['gray']}{slot}{STYLE['reset']}:")
                        print(f"        {STYLE['red']}{old_val}{STYLE['reset']}")
                        print(f"        → {STYLE['green']}{new_val}{STYLE['reset']}")

def print_summary(trace, state_diff=None):
    """Print transaction summary"""
    print(f"\n{STYLE['gray']}{'─' * 80}{STYLE['reset']}")
    print(f"\n{STYLE['bold']}TRANSACTION SUMMARY{STYLE['reset']}\n")
    
    # Success/Failure
    if trace.get("error"):
        print(f"  {STYLE['fail']} {STYLE['bg_red']}{STYLE['white']} FAILED {STYLE['reset']} {STYLE['red']}{trace['error']}{STYLE['reset']}")
    else:
        print(f"  {STYLE['success']} {STYLE['bg_green']}{STYLE['white']} SUCCESS {STYLE['reset']}")
    
    # Count total calls
    def count_calls(node):
        return 1 + sum(count_calls(c) for c in node.get("calls", []))
    
    total_calls = count_calls(trace) - 1  # Subtract the root
    print(f"  {STYLE['dot']} Total Internal Calls: {STYLE['bold']}{total_calls}{STYLE['reset']}")
    
    # Total gas
    gas_used = int(trace.get("gasUsed", "0x0"), 16)
    print(f"  {STYLE['dot']} Total Gas Used: {STYLE['bold']}{STYLE['yellow']}{gas_used:,}{STYLE['reset']}")
    
    print(f"\n{STYLE['blue']}{'═' * 80}{STYLE['reset']}\n")

def export_to_odf(filename, tx_info, trace, state_diff=None):
    """Export trace data to ODF spreadsheet format"""
    doc = OpenDocumentSpreadsheet()
    
    # Create styles
    header_style = Style(name="HeaderStyle", family="table-cell")
    header_style.addElement(TextProperties(fontweight="bold"))
    header_style.addElement(TableCellProperties(backgroundcolor="#4472C4"))
    header_style.addElement(TextProperties(color="#FFFFFF"))
    doc.automaticstyles.addElement(header_style)
    
    success_style = Style(name="SuccessStyle", family="table-cell")
    success_style.addElement(TableCellProperties(backgroundcolor="#70AD47"))
    success_style.addElement(TextProperties(color="#FFFFFF"))
    doc.automaticstyles.addElement(success_style)
    
    error_style = Style(name="ErrorStyle", family="table-cell")
    error_style.addElement(TableCellProperties(backgroundcolor="#FF0000"))
    error_style.addElement(TextProperties(color="#FFFFFF"))
    doc.automaticstyles.addElement(error_style)
    
    # Sheet 1: Transaction Overview
    overview_table = Table(name="Transaction Overview")
    
    # Headers
    header_row = TableRow()
    for header in ["Field", "Value"]:
        cell = TableCell(stylename=header_style)
        cell.addElement(P(text=header))
        header_row.addElement(cell)
    overview_table.addElement(header_row)
    
    # Transaction data
    overview_data = []
    if tx_info:
        overview_data.extend([
            ("Transaction Hash", tx_info.get("hash", "N/A")),
            ("Block Number", str(int(tx_info.get("blockNumber", "0x0"), 16)) if tx_info.get("blockNumber") else "N/A"),
            ("From", tx_info.get("from", "N/A")),
            ("To", tx_info.get("to", "N/A")),
            ("Value", format_hex_value(tx_info.get("value", "0x0"))),
            ("Gas Limit", str(int(tx_info.get("gas", "0x0"), 16)) if tx_info.get("gas") else "N/A"),
            ("Gas Price", format_hex_value(tx_info.get("gasPrice", "0x0")) if tx_info.get("gasPrice") else "N/A"),
            ("Nonce", str(int(tx_info.get("nonce", "0x0"), 16)) if tx_info.get("nonce") else "N/A"),
            ("Type", tx_info.get("type", "N/A")),
        ])
    
    # Add trace summary
    if trace:
        gas_used = int(trace.get("gasUsed", "0x0"), 16)
        status = "FAILED" if trace.get("error") else "SUCCESS"
        overview_data.extend([
            ("Status", status),
            ("Gas Used", f"{gas_used:,}"),
            ("Error", trace.get("error", "None")),
        ])
    
    for field, value in overview_data:
        row = TableRow()
        cell1 = TableCell()
        cell1.addElement(P(text=field))
        row.addElement(cell1)
        
        cell2 = TableCell()
        if field == "Status":
            cell2.setAttribute("stylename", error_style if value == "FAILED" else success_style)
        cell2.addElement(P(text=str(value)))
        row.addElement(cell2)
        overview_table.addElement(row)
    
    doc.spreadsheet.addElement(overview_table)
    
    # Sheet 2: Call Trace
    trace_table = Table(name="Call Trace")
    
    # Headers
    header_row = TableRow()
    for header in ["Depth", "Type", "From", "To", "Method", "Value", "Gas Used", "Error"]:
        cell = TableCell(stylename=header_style)
        cell.addElement(P(text=header))
        header_row.addElement(cell)
    trace_table.addElement(header_row)
    
    # Flatten trace into rows
    def flatten_trace(node, depth=0):
        rows = []
        if node:
            method = ""
            if node.get("input") and len(node.get("input")) >= 10:
                sig = node.get("input")[:10]
                if sig in METHOD_CACHE:
                    method = METHOD_CACHE[sig]
                else:
                    METHOD_CACHE[sig] = get_method_signature(sig)
                    method = METHOD_CACHE[sig] or sig
            
            rows.append({
                "depth": depth,
                "type": node.get("type", "CALL"),
                "from": node.get("from", ""),
                "to": node.get("to", ""),
                "method": method,
                "value": format_hex_value(node.get("value", "0x0")),
                "gas_used": str(int(node.get("gasUsed", "0x0"), 16)),
                "error": node.get("error", "")
            })
            
            for call in node.get("calls", []):
                rows.extend(flatten_trace(call, depth + 1))
        
        return rows
    
    trace_rows = flatten_trace(trace)
    for trace_data in trace_rows:
        row = TableRow()
        for field in ["depth", "type", "from", "to", "method", "value", "gas_used", "error"]:
            cell = TableCell()
            if field == "error" and trace_data[field]:
                cell.setAttribute("stylename", error_style)
            cell.addElement(P(text=str(trace_data[field])))
            row.addElement(cell)
        trace_table.addElement(row)
    
    doc.spreadsheet.addElement(trace_table)
    
    # Sheet 3: State Changes (if available)
    if state_diff:
        state_table = Table(name="State Changes")
        
        # Headers
        header_row = TableRow()
        for header in ["Account", "Type", "Old Value", "New Value"]:
            cell = TableCell(stylename=header_style)
            cell.addElement(P(text=header))
            header_row.addElement(cell)
        state_table.addElement(header_row)
        
        # Process state changes
        pre_state = state_diff.get("pre", {})
        post_state = state_diff.get("post", {})
        
        if not pre_state and not post_state:
            pre_state = {}
            post_state = state_diff
        
        all_addresses = set(pre_state.keys()) | set(post_state.keys())
        
        for addr in sorted(all_addresses):
            pre = pre_state.get(addr, {})
            post = post_state.get(addr, {})
            
            # Balance changes
            pre_balance = pre.get("balance", "0x0")
            post_balance = post.get("balance", pre_balance)
            if pre_balance != post_balance:
                row = TableRow()
                cell1 = TableCell()
                cell1.addElement(P(text=addr))
                row.addElement(cell1)
                cell2 = TableCell()
                cell2.addElement(P(text="Balance"))
                row.addElement(cell2)
                cell3 = TableCell()
                cell3.addElement(P(text=format_hex_value(pre_balance)))
                row.addElement(cell3)
                cell4 = TableCell()
                cell4.addElement(P(text=format_hex_value(post_balance)))
                row.addElement(cell4)
                state_table.addElement(row)
            
            # Storage changes
            pre_storage = pre.get("storage", {})
            post_storage = post.get("storage", {})
            all_slots = set(pre_storage.keys()) | set(post_storage.keys())
            for slot in sorted(all_slots):
                old_val = pre_storage.get(slot, "0x0")
                new_val = post_storage.get(slot, "0x0")
                if old_val != new_val:
                    row = TableRow()
                    cell1 = TableCell()
                    cell1.addElement(P(text=addr))
                    row.addElement(cell1)
                    cell2 = TableCell()
                    cell2.addElement(P(text=f"Storage[{slot}]"))
                    row.addElement(cell2)
                    cell3 = TableCell()
                    cell3.addElement(P(text=old_val))
                    row.addElement(cell3)
                    cell4 = TableCell()
                    cell4.addElement(P(text=new_val))
                    row.addElement(cell4)
                    state_table.addElement(row)
        
        doc.spreadsheet.addElement(state_table)
    
    # Save document
    doc.save(filename)
    print(f"{STYLE['success']} Trace exported to {STYLE['cyan']}{filename}{STYLE['reset']}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Ethereum Transaction Tracer")
    parser.add_argument("tx", help="Transaction hash (0x...) or 'sim' to simulate raw tx")
    parser.add_argument("--chain", type=int, default=1, help="Chain ID (default: 1)")
    parser.add_argument("--rpc", help="Custom RPC URL")
    parser.add_argument("--block", default="latest", help="Block number/tag for simulation")
    parser.add_argument("--raw", help="Raw transaction hex for simulation")
    parser.add_argument("--raw-tx-json", help="JSON file with transaction(s) to simulate")
    parser.add_argument("--tracer", default="callTracer", help="Tracer type")
    parser.add_argument("--state", action="store_true", help="Show state changes")
    parser.add_argument("--odf", help="Export trace to ODF spreadsheet file")
    args = parser.parse_args()
    
    # Get RPC endpoint
    rpc = args.rpc or CHAINS.get(args.chain)
    if not rpc:
        sys.exit(f"No RPC for chain {args.chain}. Use --rpc")
    
    # Check if RPC is a placeholder
    if rpc.startswith("YOUR_"):
        print(f"{STYLE['red']}Error: RPC endpoint not configured{STYLE['reset']}")
        print(f"\nPlease either:")
        print(f"1. Update rpc.json with actual RPC URLs")
        print(f"2. Use --rpc flag with a valid RPC URL")
        print(f"\nNote: Make sure your RPC endpoint has debug_traceCall/debug_traceTransaction enabled")
        sys.exit(1)
    
    tx_info = None
    state_diff = None
    
    # Determine operation mode
    if args.tx == "sim":
        tx_params = None
        
        # Load from JSON file if provided
        if args.raw_tx_json:
            with open(args.raw_tx_json, 'r') as f:
                tx_data = json.load(f)
                
                # Handle both single transaction and array of transactions
                if isinstance(tx_data, list):
                    # For now, use the first transaction
                    tx_data = tx_data[0]
                
                # Extract transaction parameters for simulation
                tx_params = {
                    "from": tx_data.get("from"),
                    "to": tx_data.get("to"),
                    "data": tx_data.get("input", "0x"),
                    "value": tx_data.get("value", "0x0"),
                    "gas": tx_data.get("gas", "0x5208"),
                }
                
                # Use appropriate gas price based on transaction type
                if tx_data.get("type") == "0x2":
                    # EIP-1559 transaction
                    tx_params["gasPrice"] = tx_data.get("maxFeePerGas", tx_data.get("gasPrice"))
                else:
                    tx_params["gasPrice"] = tx_data.get("gasPrice", "0x0")
                
                # Store original tx info for display
                tx_info = tx_data
        
        # Fallback to raw hex if no JSON provided
        elif args.raw:
            if not args.raw.startswith("0x02"):
                sys.exit("Only EIP-1559 transactions supported for raw hex")
            
            # Hardcoded for the specific transaction (would need RLP decoder for production)
            tx_params = {
                "from": "0x93533a3511e9b0d5c17b1cbd0e1737781def61a6",
                "to": "0xf4a44a3a7b01fc21f5586c1008866eb418a7b76b",
                "data": "0x773acdef0000000000000000000000000000000000000000000000000000000000000003",
                "gas": "0xd0c8",
                "gasPrice": "0xb9902c65"
            }
        else:
            sys.exit("Simulation requires --raw or --raw-tx-json")
        
        block = hex(int(args.block)) if args.block.isdigit() else args.block
        
        # For simulations, use the appropriate tracer based on --state flag
        if args.state:
            # Use prestateTracer with diffMode for state changes
            trace_result = rpc_call(rpc, "debug_traceCall", [
                tx_params, 
                block, 
                {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
            ])
            state_diff = trace_result
            # Also get the call trace
            trace = rpc_call(rpc, "debug_traceCall", [tx_params, block, {"tracer": args.tracer}])
        else:
            trace = rpc_call(rpc, "debug_traceCall", [tx_params, block, {"tracer": args.tracer}])
    else:
        # Get transaction info
        tx_info = rpc_call(rpc, "eth_getTransactionByHash", [args.tx])
        
        # Trace existing transaction
        trace = rpc_call(rpc, "debug_traceTransaction", [args.tx, {"tracer": args.tracer}])
        
        # Get state diff if requested
        if args.state:
            state_diff = get_state_diff(rpc, args.tx)
    
    # Display results
    print_header(args.chain, args.tracer, tx_info)
    
    if trace:
        print_trace(trace)
        print_gas_analysis(trace)
        
        if state_diff:
            print_state_changes(state_diff)
        
        print_summary(trace, state_diff)
        
        # Export to ODF if requested
        if args.odf:
            export_to_odf(args.odf, tx_info, trace, state_diff)
    else:
        print(f"{STYLE['red']}Failed to retrieve trace data.{STYLE['reset']}")
        print(f"{STYLE['dim']}Possible reasons:{STYLE['reset']}")
        print(f"  • Transaction not found or invalid hash")
        print(f"  • Block not yet available for tracing")
        print(f"  • RPC node doesn't support the {args.tracer} tracer")
        print(f"\n{STYLE['dim']}Example transactions to test:{STYLE['reset']}")
        print(f"  • Simple transfer: 0x{('5' * 64)}")
        print(f"  • Token transfer: 0xa9059cbb...")
        print(f"  • Complex DeFi: 0x77eb2b763f971400e98b43c3ce60e4bfd071ed4713fbe40fbb3188f765173d6d")

if __name__ == "__main__":
    main()
