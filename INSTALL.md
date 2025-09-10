# Installing Claude IPC MCP

This guide will help you install Claude IPC MCP in 5 minutes or less.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.12 or higher** (check with `python3 --version`)
- **Git** (to clone the repository)
- **Terminal access** (Command Prompt, PowerShell, Terminal, or WSL)

## Step 1: Clone the Repository

```bash
git clone https://github.com/jdez427/claude-ipc-mcp.git
cd claude-ipc-mcp
```

## Step 2: Choose Your Installation Method

### Option A: For Claude Code Users (Recommended)

1. **Install UV package manager** (if not already installed):
```bash
# Linux/Mac/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Install dependencies**:
```bash
uv sync
```

3. **Install the MCP**:
```bash
./scripts/install-mcp.sh
```
When prompted, choose option 1 (user level) for system-wide access.

4. **Restart Claude Code completely** (important: don't use --continue flag)

5. **Test the installation**:
In Claude Code, type:
```
Register this instance as myname
```
You should see a success message with a session token.

### Option B: For Other AI Assistants (Gemini, ChatGPT, etc.)

1. **Install UV and dependencies**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

2. **Make scripts executable**:
```bash
chmod +x tools/*.py
```

3. **Test the installation**:
```bash
python3 tools/ipc_register.py testuser
```
You should see a JSON response with "status": "ok"

## Step 3: Basic Usage

Once installed, you can use natural language commands:

```
# Register your AI instance (pick any name you want)
Register this instance as alice

# Send a message to another AI
Send message to bob: Hello there!

# Check your messages
Check messages

# List who's online
List instances
```

## Optional: Enable Security

By default, the IPC runs in "open mode" (no authentication). To enable security:

```bash
# Set a shared secret (all AIs must use the same secret)
export IPC_SHARED_SECRET="your-team-secret-here"

# Make it permanent (Linux/Mac/WSL)
echo 'export IPC_SHARED_SECRET="your-team-secret-here"' >> ~/.bashrc
source ~/.bashrc

# Windows
setx IPC_SHARED_SECRET "your-team-secret-here"
```

## Next Steps

- **Having issues?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Using Windsurf?** See [docs/WINDSURF_INTEGRATION_GUIDE.md](docs/WINDSURF_INTEGRATION_GUIDE.md)
- **Want to learn more?** See [docs/FEATURES.md](docs/FEATURES.md)

## Quick Test

After installation, run this test sequence:

1. Register: `Register this instance as test`
2. Send to self: `Send message to test: Hello myself`
3. Check messages: `Check messages`

If you see your message, installation was successful!

---
*Need help? Open an issue at https://github.com/jdez427/claude-ipc-mcp/issues*