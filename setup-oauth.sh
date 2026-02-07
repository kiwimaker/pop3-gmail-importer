#!/bin/bash
# ==============================================================
# Setup OAuth tokens locally before deploying to Docker/Synology
# Run this on your Mac ONCE per Gmail account
# ==============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
DATA_DIR="$SCRIPT_DIR/data"

echo ""
echo "=========================================="
echo " POP3 Gmail Importer - OAuth Setup"
echo "=========================================="
echo ""

# Create directory structure
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR/tokens"
mkdir -p "$DATA_DIR/state"
mkdir -p "$DATA_DIR/backup"
mkdir -p "$DATA_DIR/logs"

# Check for credentials.json
if [ ! -f "$CONFIG_DIR/credentials.json" ]; then
    echo "ERROR: credentials.json not found in config/"
    echo ""
    echo "Steps to get it:"
    echo "  1. Go to https://console.cloud.google.com"
    echo "  2. Create a project (or select existing)"
    echo "  3. Enable Gmail API"
    echo "  4. Go to Credentials > Create Credentials > OAuth client ID"
    echo "  5. Type: Desktop application"
    echo "  6. Download the JSON file"
    echo "  7. Save it as: $CONFIG_DIR/credentials.json"
    echo ""
    exit 1
fi

echo "Found credentials.json"

# Check for .env
if [ ! -f "$CONFIG_DIR/.env" ]; then
    echo "Creating .env from template..."
    cp "$SCRIPT_DIR/.env.example" "$CONFIG_DIR/.env"
    echo ""
    echo "IMPORTANT: Edit $CONFIG_DIR/.env with your POP3 and Gmail details"
    echo "Then run this script again."
    echo ""
    exit 1
fi

echo "Found .env"

# Create virtual env if needed
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate and install deps
source "$SCRIPT_DIR/venv/bin/activate"
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Symlink config files so test_connection.py finds them
ln -sf "$CONFIG_DIR/credentials.json" "$SCRIPT_DIR/credentials.json" 2>/dev/null || true
ln -sf "$CONFIG_DIR/.env" "$SCRIPT_DIR/.env" 2>/dev/null || true

# Point token paths to data dir
export ACCOUNT1_GMAIL_TOKEN_FILE="$DATA_DIR/tokens/token_account1.json"

echo ""
echo "Running connection test (browser will open for OAuth)..."
echo ""

cd "$SCRIPT_DIR"
python test_connection.py

# Copy generated tokens to data dir (in case they went to default location)
if [ -d "$SCRIPT_DIR/tokens" ]; then
    cp -r "$SCRIPT_DIR/tokens/"* "$DATA_DIR/tokens/" 2>/dev/null || true
fi

# Cleanup symlinks
rm -f "$SCRIPT_DIR/credentials.json" 2>/dev/null || true
rm -f "$SCRIPT_DIR/.env" 2>/dev/null || true

echo ""
echo "=========================================="
echo " Setup complete!"
echo "=========================================="
echo ""
echo "Your files are ready in:"
echo "  Config:  $CONFIG_DIR/"
echo "  Data:    $DATA_DIR/"
echo ""
echo "Next steps:"
echo "  1. Copy this entire folder to your Synology"
echo "  2. In Portainer, create a stack with docker-compose.yml"
echo "  3. Or run: docker compose up -d"
echo ""
