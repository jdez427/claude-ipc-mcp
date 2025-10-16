#!/bin/bash
# Install Claude IPC MCP with uv

echo "==========================================="
echo "Claude IPC MCP Installation (using uv)"
echo "==========================================="
 
# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required but not found"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Change to repo directory
cd "$REPO_DIR"

# Check for old installations
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "⚠️  Warning: Old virtual environment detected!"
    echo "This may interfere with UV installation."
    echo ""
    read -p "Would you like to clean up old installations? (y/n): " cleanup
    if [ "$cleanup" = "y" ] || [ "$cleanup" = "Y" ]; then
        echo "Removing old virtual environments..."
        rm -rf venv/ .venv/
        echo "✅ Old installations cleaned up"
    else
        echo "⚠️  Proceeding with old installations present - this may cause issues"
    fi
    echo ""
fi

# Install dependencies with uv
echo "Installing dependencies with uv sync..."
uv sync

# Ask user for installation scope
echo ""
echo "Where would you like to install the MCP?"
echo "1) User level (available in all projects)"
echo "2) Project level (only in current project)"
echo ""
read -p "Enter your choice (1 or 2): " choice

# Determine the scope flag
case $choice in
    1)
        SCOPE="user"
        SCOPE_DESC="user level (all projects)"
        ;;
    2)
        SCOPE="project"
        SCOPE_DESC="project level (current project only)"
        ;;
    *)
        echo "Invalid choice. Defaulting to user level."
        SCOPE="user"
        SCOPE_DESC="user level (all projects)"
        ;;
esac

# Add MCP to Claude Code using uvx
echo ""
echo "Adding IPC MCP to Claude Code at $SCOPE_DESC..."

# Run the claude mcp add command
COMMAND="claude mcp add claude-ipc -s $SCOPE -- uvx --from $REPO_DIR claude-ipc-mcp"
echo "Running: $COMMAND"
echo ""

if $COMMAND; then
    echo "✅ Successfully added Claude IPC MCP!"
    echo ""
    
    # Verify installation
    echo "Verifying installation..."
    if claude mcp list | grep -q "claude-ipc"; then
        echo "✅ MCP 'claude-ipc' is now installed at $SCOPE_DESC"
        echo ""
        echo "🎉 Installation complete!"
        echo ""
        echo "⚠️  IMPORTANT: Complete restart required!"
        echo "1. Exit Claude Code completely (type 'exit')"
        echo "2. Start a fresh session with 'claude'"
        echo "3. Do NOT use --continue or --resume flags"
    else
        echo "⚠️  MCP was added but not showing in list yet."
        echo "This is normal - please restart Claude Code for it to appear."
    fi
else
    echo "❌ Failed to add MCP. Please check the error message above."
    echo ""
    echo "You can try running this command manually:"
    echo "$COMMAND"
    exit 1
fi

echo "==========================================="