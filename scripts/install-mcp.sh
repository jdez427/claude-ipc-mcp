#!/bin/bash
# Install Claude IPC MCP

echo "==========================================="
echo "Claude IPC MCP Installation"
echo "==========================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv ~/.claude-ipc-env

# Activate and install mcp
echo "Installing MCP package..."
source ~/.claude-ipc-env/bin/activate
pip install mcp

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Add MCP to Claude Code
echo ""
echo "Adding IPC MCP to Claude Code..."
echo "Run this command:"
echo ""
echo "claude mcp add claude-ipc -s user -- ~/.claude-ipc-env/bin/python $REPO_DIR/src/claude_ipc_server.py"
echo ""
echo "Then restart Claude Code for the MCP to load!"
echo "==========================================="