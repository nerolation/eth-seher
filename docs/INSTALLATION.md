# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

## Quick Install

### Using pip (recommended)

```bash
pip install eth-transaction-interceptor
```

### From source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/eth-transaction-interceptor.git
cd eth-transaction-interceptor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

1. Copy the example configuration:
```bash
cp config/rpc.json.example rpc.json
```

2. Edit `rpc.json` with your RPC endpoints:
```json
{
  "1": "YOUR_MAINNET_RPC_URL",
  "11155111": "YOUR_SEPOLIA_RPC_URL"
}
```

**Important:** Your RPC endpoint must have `debug_traceCall` and `debug_traceTransaction` enabled for full functionality.

## Verify Installation

Test the installation:
```bash
eth-interceptor --help
```

You should see the available commands and options.

## Docker Installation (Optional)

Build the Docker image:
```bash
docker build -t eth-interceptor .
```

Run the container:
```bash
docker run -p 8545:8545 eth-interceptor
```

## Troubleshooting

### Port Already in Use

If port 8545 is already in use:
```bash
eth-interceptor start --port 8546
```

### Missing Dependencies

If you encounter import errors:
```bash
pip install --upgrade -r requirements.txt
```

### Permission Errors

On Linux/macOS, you might need to use sudo:
```bash
sudo pip install eth-transaction-interceptor
```

Or better, use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```