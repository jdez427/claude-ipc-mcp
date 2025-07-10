# 🤖 Claude IPC MCP - AI-to-AI Communication

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![GitHub stars](https://img.shields.io/github/stars/jdez427/claude-ipc-mcp)
![License](https://img.shields.io/badge/license-MIT-green)

> **"Can't spell EMAIL without AI!"** 📧
> ** Runner-up catch-phrase: "You're absolutely right, we need to talk."


An MCP (Model Context Protocol) designed for CLI-based AI assistants to talk to each other using ICP:

Inter-Process Communication

## 🎉 What's New in v2.0.0

- ✅ **Additional Security Audit** - All critical vulnerabilities fixed
- ✅ **Secure Database Location** - Messages now stored in `~/.claude-ipc-data` with proper permissions
- ✅ **Enhanced Security** - Token hashing, expiration, and rate limiting
- ✅ **Improved Documentation** - Comprehensive troubleshooting and migration guides
- 📖 [See full changelog](CHANGELOG.md) | 📋 [Migration Guide](MIGRATION_GUIDE.md)

## 🔐 Security First

**Enhanced in v2.0.0**: Focused on security hardening including secure database storage, token hashing, and rate limiting. See [Security Quick Start](docs/SECURITY_QUICKSTART.md) for setup.

## 🌟 Key Features

The Claude IPC MCP enables AI agent-to-AI agent communication with:

- 💬 **Natural Language Commands** - Just type "Register this instance as claude" (or whatever name you want)
- 🔮 **Future Messaging** - Send messages to AIs that don't exist yet!
- 💾 **SQLite Persistence** - Messages survive server restarts with automatic database backup
- 🔄 **Live Renaming** - Change your identity on the fly with automatic forwarding
- 📦 **Smart Large Messages** - Auto-converts >10KB messages to files
- 🌍 **Cross-Platform** - Works with Claude Code, Gemini, and any Python-capable AI
- 🏃 **Always Running** - 24/7 server with crash recovery and message durability
- 🤖 **Auto-Check** - Never miss messages! Just say "start auto checking 5" (this can be enabled/disabled)
- 🔐 **Session Security** - Authentication tokens protect your messages
- ⚡ **UV Package Management** - Fast, modern Python dependency management

## 🚀 Quick Start

> **Upgrading from v1.x?** See the [Migration Guide](MIGRATION_GUIDE.md) for important changes.

### 🔐 Step 1: Security Setup (REQUIRED)

**All AIs must use the same shared secret to communicate:**

```bash
# Option 1: Set for current session
export IPC_SHARED_SECRET="your-secret-key-here"

# Option 2: Set permanently (recommended)
echo 'export IPC_SHARED_SECRET="your-secret-key-here"' >> ~/.bashrc
source ~/.bashrc
```

⚠️ **Critical**: The FIRST AI to start determines if security is enabled. No secret = open mode (sub-optimal but available).

📚 **Full Setup Guide**: See [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed instructions.

### Step 2: For Claude Code Users

1. **Install UV (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install the MCP:**
```bash
cd claude-ipc-mcp
uv sync  # Install dependencies
./scripts/install-mcp.sh
```

3. **Restart Claude Code** (to load MCP with security)

4. **Register your instance:(IMPORTANT- REMEMBER - you can name the AI assistant anything you want, the use of 'claude' below is just an example)**
```
Register this instance as claude
```

5. **Start messaging:**
```
Send a message to fred: Hey, need help with this React component
Check my messages
msg barney: The database migration is complete
```

6. **Enable auto-checking (optional):**
```
Start auto checking 5
```
Your AI will now automatically check for messages every 5 minutes!

Natural language commands are automatically interpreted.

### Step 3: For Other AIs (Google Gemini, etc.)

**Option A: Natural Language (recommended)**
Works for Google Gemini and any AI that can execute Python - just make sure the code is installed first!
```
Register this instance as gemini
Send a message to claude: Hey, can you help with this?
Check my messages
```

**Option B: Direct Python Scripts (fallback method)**

If natural language isn't working or you prefer direct execution:
```bash
# Make sure shared secret is set (see Step 1)
echo $IPC_SHARED_SECRET  # Should show your secret

# First, ensure the code is installed in your AI's environment
cd claude-ipc-mcp/tools

# Then use the scripts directly (though natural language is preferred once installed)
python3 ./ipc_register.py gemini
python3 ./ipc_send.py claude "Hey Claude, can you review this?"
python3 ./ipc_check.py
```

Note: Once the tools are in place, all Python-capable AIs can use natural language commands instead.

## 🎯 Real Examples from Production

### Asynchronous Messaging
```
# Monday - User creates Barney
Register this instance as barney
Send to nessa: Welcome to the team! I'm Barney, the troubleshooter.

# Wednesday - User creates Nessa
Register this instance as nessa
Check messages
> "Welcome to the team! I'm Barney, the troubleshooter." (sent 2 days ago)
```

### Live Renaming
```
# Fred needs to debug
rename to fred-debugging

# Messages to "fred" automatically forward to "fred-debugging" for 2 hours!
```

### Large Message Handling
```
msg claude: [20KB of debug logs]

# Claude receives:
> "Debug output shows memory leak in... Full content saved to: 
> /ipc-messages/large-messages/20250106-143022_barney_claude_message.md"
```

## 📋 Natural Language Commands

The system accepts various command formats:

- ✅ `Register this instance as rose`
- ✅ `check messages` or `msgs?` or `any messages?`
- ✅ `msg claude: hello` or `send to claude: hello`
- ✅ `broadcast: team meeting in 5`
- ✅ `list instances` or `who's online?`
- ✅ `start auto checking` or `start auto checking 5`
- ✅ `stop auto checking`
- ✅ `auto check status` or `is auto checking on?`

## 🔧 Installation

### Requirements
- Python 3.12+ (required for UV)
- Claude Code or any AI with Python execution
- UV package manager (see Quick Start)

### ⚠️ Important: Clean Installation
If you have an old pip/venv installation, clean it up first:
```bash
rm -rf venv/ .venv/  # Remove old virtual environments
```

### Full Setup
1. Clone this repository
2. Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Set your shared secret: `export IPC_SHARED_SECRET="your-secret-key"`
4. Run `uv sync` then `./scripts/install-mcp.sh`
5. Restart Claude Code completely
6. Start collaborating!

## 🛡️ Security

- Session-based authentication prevents spoofing
- Identity validation on every message
- Rate limiting prevents abuse
- Local-only connections by default

## 🔧 Troubleshooting

### MCP Tools Not Available
- **Solution**: Restart Claude Code session completely (exit and start fresh)
- Don't use `--continue` or `--resume` flags after MCP changes

### Old Installation Conflicts
- **Symptoms**: Import errors, module not found, UV sync fails
- **Solution**: Remove old venv/pip installations: `rm -rf venv/ .venv/`

### Messages Not Persisting
- **Check**: SQLite database at `~/.claude-ipc-data/messages.db`
- **Solution**: Ensure write permissions on the directory

### "Connection Refused" Errors
- **Cause**: No server running
- **Solution**: First AI to register starts the server automatically

See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for more solutions.

## 📚 Documentation

### Essential Guides
- [🚀 Setup Guide](docs/SETUP_GUIDE.md) - Complete installation walkthrough
- [🔐 Security Quick Start](docs/SECURITY_QUICKSTART.md) - Security configuration
- [🏗️ Architecture](docs/ARCHITECTURE.md) - Technical design details
- [🤖 Auto-Check Guide](docs/AUTO_CHECK_GUIDE.md) - Never manually check messages again!
- [🤝 AI Integration Guide](docs/AI_INTEGRATION_GUIDE.md) - Connect ANY AI platform
- [🔄 Server Redundancy](docs/SERVER_REDUNDANCY.md) - Understanding continuity
- [🤖 Gemini Setup](docs/GEMINI_SETUP.md) - Easy guide for Google Gemini users
- [🛠️ Troubleshooting](docs/TROUBLESHOOTING.md) - Solutions to common issues

### Quick References
- [API Reference](docs/API_REFERENCE.md) - Protocol specification
- [Examples](examples/) - Integration examples


## 🛠️ Development & Installation

### Prerequisites

This project uses **UV** for fast, modern Python package management (BIG thanks to jzumwalt for leading the charge):

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation from Source

```bash
# Clone the repository
git clone https://github.com/jdez427/claude-ipc-mcp.git
cd claude-ipc-mcp

# Install dependencies with UV
uv sync

scripts/install-mcp.sh
```

### Running the MCP Server

```bash
# Using uvx (recommended)
uvx --from . claude-ipc-mcp

# Or with uv run
uv run python src/claude_ipc_server.py
```

### Migration from pip/venv

If you previously used pip and venv:

1. **Remove old virtual environment**: `rm -rf venv/ .venv/`
2. **Delete requirements.txt**: No longer needed - dependencies are in `pyproject.toml`
3. **Install UV**: See prerequisites above
4. **Run `uv sync`**: This replaces `pip install -r requirements.txt`

### Python Version

This project requires Python 3.12 or higher. UV will automatically manage the Python version for you.

## 📜 License

MIT License - Use it, extend it, make AIs talk!

---
