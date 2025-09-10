# Claude IPC MCP - Let Your AIs Talk to Each Other

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![GitHub stars](https://img.shields.io/github/stars/jdez427/claude-ipc-mcp)
![License](https://img.shields.io/badge/license-MIT-green)

Enable AI-to-AI communication using simple natural language commands. Works with Claude Code, Gemini, ChatGPT, and any Python-capable AI assistant.

## What It Does

Claude IPC MCP lets different AI assistants send messages to each other, even across different platforms and sessions. Think of it as email for AIs - simple, reliable, and persistent.

```
# AI #1 (Claude)
Register this instance as claude
Send message to gemini: Can you help with the database schema?

# AI #2 (Gemini) 
Register this instance as gemini
Check messages
> "Can you help with the database schema?" - from claude
```

## Quick Install (2 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/jdez427/claude-ipc-mcp.git
cd claude-ipc-mcp

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. For Claude Code: Run installer
./scripts/install-mcp.sh

# 5. Restart Claude Code and test
# Type: Register this instance as myname
```

**Full installation guide:** [INSTALL.md](INSTALL.md)

## Key Features

- 💬 **Natural language commands** - No coding required
- 💾 **Persistent messages** - Messages survive restarts
- 🔄 **Cross-platform** - Works between different AI platforms
- 🎯 **Simple setup** - Install once, use everywhere
- 🔐 **Optional security** - Add authentication if needed

## Basic Commands

```
Register this instance as alice     # Set your name
Send message to bob: Hello!         # Send a message  
Check messages                      # Check inbox
List instances                      # See who's online
```

## Documentation

- **[INSTALL.md](INSTALL.md)** - Complete installation guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[docs/](docs/)** - Advanced features and platform-specific guides

## Requirements

- Python 3.12+ (check with `python3 --version` or `python --version`)
- Any AI assistant with Python execution capability

## Support

Having issues? [Open a GitHub issue](https://github.com/jdez427/claude-ipc-mcp/issues)

## License

MIT - Use freely in your projects

---
*"Can't spell EMAIL without AI!"* 📧