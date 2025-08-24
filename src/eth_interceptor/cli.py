#!/usr/bin/env python3
"""
Command-line interface for Ethereum Transaction Interceptor
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Ethereum Transaction Interceptor & Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  eth-interceptor start           Start interceptor and monitor
  eth-interceptor intercept       Start interceptor only  
  eth-interceptor monitor         Start monitor only
  eth-interceptor trace TX_HASH   Trace a transaction
  eth-interceptor submit --latest Submit latest intercepted transaction
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command (default - runs both interceptor and monitor)
    start_parser = subparsers.add_parser('start', help='Start interceptor and monitor')
    start_parser.add_argument('--port', type=int, default=8545, help='Port for interceptor')
    
    # Intercept command (interceptor only)
    intercept_parser = subparsers.add_parser('intercept', help='Start interceptor only')
    intercept_parser.add_argument('--port', type=int, default=8545, help='Port for interceptor')
    
    # Monitor command (monitor only)
    monitor_parser = subparsers.add_parser('monitor', help='Start transaction monitor')
    
    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Trace a transaction')
    trace_parser.add_argument('tx_hash', nargs='?', help='Transaction hash to trace')
    trace_parser.add_argument('--raw', help='Raw transaction hex')
    trace_parser.add_argument('--raw-tx-json', help='Path to transaction JSON file')
    trace_parser.add_argument('--state', action='store_true', help='Show state changes')
    trace_parser.add_argument('--odf', help='Export to ODF file')
    trace_parser.add_argument('--chain', type=int, default=1, help='Chain ID')
    trace_parser.add_argument('--block', help='Block number for simulation')
    
    # Submit command
    submit_parser = subparsers.add_parser('submit', help='Submit a transaction')
    submit_parser.add_argument('file', nargs='?', help='Transaction file to submit')
    submit_parser.add_argument('--latest', action='store_true', help='Submit latest intercepted transaction')
    submit_parser.add_argument('--chain', type=int, default=1, help='Chain ID')
    
    args = parser.parse_args()
    
    # Default to 'start' if no command given
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Route to appropriate module
    if args.command == 'start':
        # Find the scripts directory
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'start.sh'
        if script_path.exists():
            subprocess.run(['bash', str(script_path)])
        else:
            # Fallback to running both services
            print("Starting interceptor and monitor...")
            from . import interceptor, monitor
            import threading
            
            # Start interceptor in thread
            thread = threading.Thread(
                target=interceptor.app.run, 
                kwargs={'host': '0.0.0.0', 'port': args.port, 'debug': False, 'use_reloader': False}
            )
            thread.daemon = True
            thread.start()
            
            # Run monitor in main thread
            mon = monitor.TransactionMonitor()
            mon.watch()
        
    elif args.command == 'intercept':
        from . import interceptor
        print(f"Starting interceptor on port {args.port}...")
        interceptor.app.run(host="0.0.0.0", port=args.port, debug=False, use_reloader=False)
        
    elif args.command == 'monitor':
        from . import monitor
        mon = monitor.TransactionMonitor()
        mon.watch()
        
    elif args.command == 'trace':
        from . import trace
        # Build argv for trace module
        sys.argv = ['trace']
        
        if args.tx_hash:
            sys.argv.append(args.tx_hash)
        elif args.raw or args.raw_tx_json:
            sys.argv.append('sim')
            
        if args.raw:
            sys.argv.extend(['--raw', args.raw])
        if args.raw_tx_json:
            sys.argv.extend(['--raw-tx-json', args.raw_tx_json])
        if args.state:
            sys.argv.append('--state')
        if args.odf:
            sys.argv.extend(['--odf', args.odf])
        if args.chain != 1:
            sys.argv.extend(['--chain', str(args.chain)])
        if args.block:
            sys.argv.extend(['--block', args.block])
            
        trace.main()
        
    elif args.command == 'submit':
        from . import submit_tx
        # Build argv for submit module
        sys.argv = ['submit_tx']
        
        if args.latest:
            sys.argv.append('--latest')
        elif args.file:
            sys.argv.append(args.file)
        if args.chain != 1:
            sys.argv.extend(['--chain', str(args.chain)])
            
        submit_tx.main()

if __name__ == '__main__':
    main()