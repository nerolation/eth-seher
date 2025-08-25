#!/usr/bin/env python3
"""Monitor intercepted transactions and run simulations"""
import os
import json
import time
import subprocess
import sys
from datetime import datetime

class TransactionMonitor:
    def __init__(self):
        self.tx_dir = "intercepted_txs"
        self.processed = set()
        
        # Load already processed transactions
        if os.path.exists(self.tx_dir):
            for f in os.listdir(self.tx_dir):
                if f.endswith(".json"):
                    self.processed.add(f)
                    
    def watch(self):
        """Watch for new transactions"""
        print("=" * 80)
        print("TRANSACTION MONITOR ACTIVE")
        print("=" * 80)
        print(f"Watching directory: {self.tx_dir}/")
        print("Press Ctrl+C to stop\n")
        
        while True:
            try:
                if not os.path.exists(self.tx_dir):
                    os.makedirs(self.tx_dir)
                    
                # Check for new transaction files
                for filename in os.listdir(self.tx_dir):
                    if filename.endswith(".json") and filename not in self.processed:
                        # New transaction detected
                        self.processed.add(filename)
                        self.process_transaction(filename)
                        
                time.sleep(0.5)  # Check every 500ms
                
            except KeyboardInterrupt:
                print("\n\nMonitor stopped.")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
                
    def process_transaction(self, json_filename):
        """Process a new transaction"""
        tx_id = json_filename.replace("tx_", "").replace(".json", "")
        
        print("\n" + "=" * 80)
        print(f"NEW TRANSACTION INTERCEPTED: {tx_id}")
        print("=" * 80)
        
        # Load transaction data
        json_path = os.path.join(self.tx_dir, json_filename)
        raw_path = os.path.join(self.tx_dir, f"tx_{tx_id}.raw")
        meta_path = os.path.join(self.tx_dir, f"tx_{tx_id}.meta")
        
        with open(json_path, 'r') as f:
            tx_data = json.load(f)
            
        print("\n📋 Transaction Details:")
        print("-" * 40)
        for key, value in tx_data.items():
            if key != "note":
                print(f"  {key:20} {value}")
                
        # Check if raw transaction exists
        has_raw = os.path.exists(raw_path)
        if has_raw:
            with open(raw_path, 'r') as f:
                raw_tx = f.read().strip()
            print(f"\n📦 Raw Transaction Saved: {len(raw_tx)} chars")
            print(f"  {raw_tx[:66]}...")
            
        # Run simulation
        print("\n🔬 Running Transaction Simulation...")
        print("-" * 40)
        
        try:
            cmd = [sys.executable, "trace.py", "sim", "--raw-tx-json", json_path, "--state"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Show simulation output with clear formatting
            print("\n╔" + "═" * 78 + "╗")
            print("║" + " SIMULATION OUTPUT ".center(78) + "║")
            print("╚" + "═" * 78 + "╝")
            
            if result.stdout:
                print(result.stdout)
                        
            if result.returncode != 0 and result.stderr:
                print(f"\n⚠️  Simulation Warning: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⚠️  Simulation timed out")
        except Exception as e:
            print(f"⚠️  Simulation error: {e}")
            
        # Interactive options
        print("\n" + "=" * 80)
        print("OPTIONS:")
        print("=" * 80)
        print("1. Submit transaction to network")
        print("2. Export simulation to ODF")
        print("3. Continue monitoring (default)")
        print("4. Exit")
        
        try:
            choice = input("\nChoice [1-4, default=3]: ").strip() or "3"
            
            if choice == "1" and has_raw:
                self.submit_transaction(raw_path)
            elif choice == "2":
                self.export_simulation(json_path, tx_id)
            elif choice == "4":
                print("Exiting...")
                sys.exit(0)
            else:
                print("Continuing to monitor...")
                
        except KeyboardInterrupt:
            print("\nContinuing to monitor...")
            
    def submit_transaction(self, raw_path):
        """Submit transaction to network"""
        print("\n📤 Submitting Transaction...")
        print("-" * 40)
        
        try:
            cmd = [sys.executable, "submit_tx.py", raw_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}")
                
            if result.returncode == 0:
                print("✅ Transaction submitted successfully!")
            else:
                print("❌ Transaction submission failed")
                
        except Exception as e:
            print(f"❌ Submission error: {e}")
            
    def export_simulation(self, json_path, tx_id):
        """Export simulation to ODF"""
        output_file = f"simulation_{tx_id}.ods"
        print(f"\n📊 Exporting to {output_file}...")
        
        try:
            cmd = [sys.executable, "trace.py", "sim", "--raw-tx-json", json_path, "--odf", output_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Exported to {output_file}")
            else:
                print(f"❌ Export failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Export error: {e}")

def main():
    monitor = TransactionMonitor()
    
    # Check if interceptor is accessible
    import socket
    interceptor_running = False
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8545))
        sock.close()
        interceptor_running = (result == 0)
    except:
        pass
    
    if not interceptor_running:
        print("Starting transaction monitor...")
        print("⚠️  No RPC interceptor detected on port 8545")
        print("\nRun ./start.sh to start everything together")
        print("Or manually start the interceptor with: python3 interceptor.py\n")
    
    try:
        monitor.watch()
    except Exception as e:
        print(f"Monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()