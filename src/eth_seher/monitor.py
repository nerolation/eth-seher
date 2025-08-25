#!/usr/bin/env python3
"""Monitor intercepted transactions and run simulations"""
import os
import json
import time
import subprocess
import sys
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class TransactionMonitor:
    def __init__(self, chain_id=1):
        self.tx_dir = "intercepted_txs"
        self.processed = set()
        self.chain_id = chain_id
        
        # Load already processed transactions
        if os.path.exists(self.tx_dir):
            for f in os.listdir(self.tx_dir):
                if f.endswith(".json"):
                    self.processed.add(f)
                    
    def watch(self):
        """Watch for new transactions"""
        print(Fore.GREEN + "=" * 80)
        print(Fore.GREEN + "TRANSACTION MONITOR ACTIVE")
        print(Fore.GREEN + "=" * 80)
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
        
        print("\n" + Fore.RED + "=" * 80)
        print(Fore.RED + f"NEW TRANSACTION INTERCEPTED: {tx_id}")
        print(Fore.RED + "=" * 80)
        
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
            cmd = [sys.executable, "-m", "eth_seher.trace", "sim", "--raw-tx-json", json_path, "--state", "--chain", str(self.chain_id)]
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
            
        # Interactive options with colored border
        print("\n")
        border_width = 78
        print(Fore.CYAN + "╔" + "═" * border_width + "╗")
        print(Fore.CYAN + "║" + Fore.YELLOW + Back.BLUE + " OPTIONS MENU ".center(border_width) + Back.RESET + Fore.CYAN + "║")
        print(Fore.CYAN + "╠" + "═" * border_width + "╣")
        
        # Format menu options with proper padding
        options = [
            ("1", "Submit transaction to network"),
            ("2", "Export simulation to ODF"),
            ("3", "Continue monitoring (default)"),
            ("4", "Exit")
        ]
        
        for num, text in options:
            # Calculate the visible text length (without color codes)
            option_text = f"  {num}. {text}"
            padding_needed = border_width - len(option_text)
            print(Fore.CYAN + "║" + Fore.GREEN + f"  {num}. " + Fore.WHITE + text + " " * padding_needed + Fore.CYAN + "║")
        
        print(Fore.CYAN + "╚" + "═" * border_width + "╝")
        
        try:
            choice = input(Fore.YELLOW + "\n➤ Choice [1-4, default=3]: " + Style.RESET_ALL).strip() or "3"
            
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
            cmd = [sys.executable, "-m", "eth_seher.submit_tx", raw_path, "--chain", str(self.chain_id)]
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
            cmd = [sys.executable, "-m", "eth_seher.trace", "sim", "--raw-tx-json", json_path, "--odf", output_file, "--chain", str(self.chain_id)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Exported to {output_file}")
            else:
                print(f"❌ Export failed")
                if result.stdout:
                    print(f"Output: {result.stdout}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                
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