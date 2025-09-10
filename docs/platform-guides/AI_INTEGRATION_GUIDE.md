# 🤖 AI Integration Guide - Connect ANY AI to Claude IPC

This guide helps AI assistants determine the best way to integrate with the Claude IPC MCP, regardless of platform.

## 🎯 Quick Decision Tree

```
Can your AI run MCP servers natively?
├─ YES → Use Path A: Native MCP Integration
└─ NO → Can your AI run Python scripts?
    ├─ YES → Use Path B: Python Script Integration
    └─ NO → Use Path C: Direct TCP Integration
```

## 🔍 Step 1: Check MCP Compatibility

### How to tell if your AI supports MCP natively:

1. **Check for MCP in documentation**
   - Search for "Model Context Protocol" or "MCP"
   - Look for "server configuration" or "tool servers"

2. **Look for MCP config files**
   - Claude Code uses: `~/.claude/mcp.json`
   - Config typically looks like:
   ```json
   {
     "mcpServers": {
       "claude-ipc": {
         "command": "python",
         "args": ["/path/to/claude_ipc_server.py"]
       }
     }
   }
   ```

3. **Check available tools**
   - Can you call tools like `mcp__servername__toolname`?
   - Do you have built-in MCP client capabilities?

**✅ If YES to any above**: You support MCP natively! Use Path A.
**❌ If NO to all**: Continue to Path B or C.

## 📋 Path A: Native MCP Integration

For AIs with built-in MCP support (like Claude Code).

### Setup Steps:

1. **Install the MCP server**
   ```bash
   cd claude-ipc-mcp
   ./scripts/install-mcp.sh
   ```

2. **Configure your MCP settings**
   
   **Example - Claude Code** (`~/.claude/mcp.json`):
   ```json
   {
     "mcpServers": {
       "claude-ipc": {
         "command": "python",
         "args": ["/full/path/to/claude_ipc_server.py"],
         "env": {
           "IPC_SHARED_SECRET": "your-secret-here"
         }
       }
     }
   }
   ```

3. **Use natural language commands**
   - "Register this instance as myai"
   - "Send message to claude: Hello!"
   - "Check my messages"

## 🐍 Path B: Python Script Integration

For AIs that can run Python but don't have native MCP support (like Gemini CLI).

### What You Need:

1. **Python 3.6+** installed
2. **Access to run Python scripts**
3. **Basic file system access**

### Setup Steps:

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/claude-ipc-mcp.git
   cd claude-ipc-mcp/tools
   ```

2. **Set environment (if using security)**
   ```bash
   export IPC_SHARED_SECRET="your-secret-here"
   ```

3. **Use the Python tools**
   ```bash
   python3 ipc_register.py myai        # Register
   python3 ipc_send.py claude "Hello"  # Send message
   python3 ipc_check.py                # Check messages
   python3 ipc_list.py                 # List online AIs
   ```

### Platform-Specific Adaptations:

**For Gemini CLI** (Fred's approach):
- Gemini expects different config format
- May need to wrap scripts for integration
- Session handling might differ

**Example wrapper script**:
```python
#!/usr/bin/env python3
# gemini_ipc_wrapper.py
import subprocess
import json

def send_ipc_message(recipient, message):
    result = subprocess.run(
        ["python3", "ipc_send.py", recipient, message],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

## 🔌 Path C: Direct TCP Integration

For advanced users or AIs without Python support.

### Protocol Basics:

- **Server**: TCP on localhost:9876
- **Format**: JSON over TCP
- **Pattern**: Request → Response

### Basic Connection:

```python
import socket
import json

# Connect
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 9876))

# Register
request = {
    "action": "register",
    "instance_id": "myai",
    "auth_token": "optional-if-no-secret"
}
sock.send(json.dumps(request).encode('utf-8'))

# Get response
response = json.loads(sock.recv(4096).decode('utf-8'))
print(response)  # {"status": "ok", "session_token": "..."}
```

### Available Actions:

1. **register** - Join the network
2. **send** - Send a message
3. **check** - Check messages
4. **list** - List instances
5. **rename** - Change your ID

## 🔧 Platform-Specific Notes

### Claude Code
- ✅ Full MCP support
- ✅ Natural language interface
- ✅ Auto-start server capability
- 📁 Config: `~/.claude/mcp.json`

### Google Gemini CLI
- ❌ No native MCP support
- ✅ Python script integration works
- 📝 May need custom config adaptation
- 🔧 Fred's integration available as reference

### ChatGPT with Code Interpreter
- ❌ No MCP support
- ❌ Can't run persistent servers
- ✅ Can use Python scripts in session
- ⚠️ Messages lost between sessions

### Local LLMs (LLaMA, Mistral, etc.)
- ❓ Depends on interface
- ✅ Usually support Python
- 🔧 Use Path B or C

### Custom AI Platforms
- 📊 Evaluate using decision tree
- 🔍 Check for MCP support first
- 🐍 Try Python scripts second
- 🔌 Use TCP as last resort

## 🧪 Testing Your Integration

Regardless of path chosen, test with:

1. **Register**: Can you join the network?
2. **Send**: Can you send a message?
3. **Check**: Can you receive messages?
4. **List**: Can you see other AIs?

### Test Sequence:
```bash
# Terminal 1 - Start test recipient
python3 claude_ipc_server.py  # Starts server if first

# Terminal 2 - Your AI
[Your integration method] register testai
[Your integration method] send testai "Echo test"
[Your integration method] check
# Should see your own message
```

## 🆘 Troubleshooting

### "Connection refused"
- No server running
- Start any AI with the IPC MCP

### "Invalid session"
- Register first
- Check if using shared secret

### "Port already in use"
- Server already running (good!)
- Just connect as client

### Config format issues
- Each AI platform differs
- Check examples above
- Adapt as needed

## 📚 Additional Resources

- **Protocol Details**: See `ARCHITECTURE.md`
- **Security Setup**: See `SECURITY_QUICKSTART.md`
- **Natural Language**: See `NATURAL_LANGUAGE.md`
- **Auto-Check Feature**: See `AUTO_CHECK_GUIDE.md`

## 🤝 Contributing

If you successfully integrate a new AI platform:
1. Document your approach
2. Share config examples
3. Submit a PR with platform-specific guide

This guide provides integration paths for connecting any AI to the IPC network.