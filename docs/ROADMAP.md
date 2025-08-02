# Claude IPC MCP Roadmap

## Current Architecture Status

### Full MCP Support for Multiple Platforms

**Current Situation:**
- Google Gemini CLI now has native MCP support and can be the server/broker
- Claude Code, Gemini CLI, and any MCP-enabled AI can participate equally
- First AI to start becomes the broker - purely democratic election
- Python client scripts in `tools/` remain available as a fallback option

**Capabilities:**
- Gemini CLI with MCP can become the server/broker
- All MCP-enabled AIs participate in the democratic server model
- Non-MCP AIs can still connect using Python client scripts
- Full platform equality - no AI has special privileges

**Compatibility Note:**
- The v2.0.0 security updates work with all connection methods
- Both MCP and Python script approaches are supported
- All clients benefit from server-side security improvements

## Future Enhancements

### 1. Standalone Server Mode for Non-MCP Environments (v2.1.0)
- Create a standalone server script for environments without MCP support
- `tools/ipc_server.py` - dedicated broker for legacy systems
- Enable IPC in restricted environments or older AI platforms
- Estimated release: Q2 2025

### 2. Universal AI Adapter (v3.0.0)
- Plugin system for different AI platforms
- Native support for:
  - Google Gemini
  - OpenAI GPTs
  - Anthropic Claude (non-MCP)
  - Local LLMs (Ollama, etc.)
- Each AI type can become a server
- Estimated release: Q3 2025

### 3. Multi-Network Support (v3.1.0)
- Run multiple IPC networks on different ports
- Network isolation for security
- Bridge between networks
- Estimated release: Q4 2025

## Recently Completed

### v2.0.0 - Security & Persistence ✅
- SQLite message persistence
- Comprehensive security hardening
- Professional security audit passed
- UV package manager support

### v1.1.0 - Core Features ✅
- Session-based authentication
- Natural language commands
- Auto-check functionality
- Large message support

## Contributing

Want to help implement these features? 
- Check our [GitHub Issues](https://github.com/jdez427/claude-ipc-mcp/issues)
- Read the [Architecture Guide](ARCHITECTURE.md)
- Submit PRs with tests

## Priority Order

1. **High Priority**: Enhanced MCP integration features for all platforms
2. **Medium Priority**: Plugin system for universal support
3. **Low Priority**: Standalone server for legacy environments
4. **Low Priority**: Multi-network features

---

*Last updated: 2025-08-01*