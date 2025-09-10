# IPC Auto-Check Technical Documentation

## Architecture Overview

The auto-check feature adds automated message processing to the IPC MCP without modifying core functionality.

```
User Input → AI interprets → Manager script → Config file → Hook → Flag → AI processes
```

## Components

### 1. Auto-Process Tool (`claude_ipc_server.py`)
- New MCP tool: `auto_process`
- Uses existing session token from MCP memory
- Calls internal check/send functions
- Updates last check timestamp

### 2. Configuration Management
- **File**: `/tmp/claude-ipc-mcp/auto_check_config.json`
- **Format**:
```json
{
  "enabled": true,
  "interval_minutes": 5,
  "started_at": "2024-01-07T15:30:00",
  "last_check": "2024-01-07T15:35:00"
}
```

### 3. Hook Script (`hooks/ipc_auto_check_hook.py`)
- Runs after every tool use via Claude Hooks
- Checks if auto-processing should trigger
- Creates flag file when interval elapsed
- Updates config to prevent double-triggering

### 4. Manager Script (`tools/ipc_auto_check_manager.py`)
- CLI tool for config management
- Commands: start, stop, status
- Validates intervals (1-60 minutes)
- Used by AI when processing natural language

### 5. Trigger Mechanism
- **Flag file**: `/tmp/claude-ipc-mcp/auto_check_trigger`
- Created by hook when check needed
- AI detects and processes
- Deleted after processing

## Data Flow

1. User enables auto-check via natural language
2. AI runs manager script to create config
3. On each tool use, hook checks elapsed time
4. If interval passed, hook creates trigger file
5. AI sees trigger, runs auto_process tool
6. Tool checks messages, processes, updates timestamp
7. AI reports results to user

## Security Considerations

- Uses existing MCP session authentication
- No credentials stored on disk
- Config file contains no sensitive data
- Hooks run with user permissions only
- Messages processed within secure MCP context

## Extension Points

### Custom Processing Logic
In `auto_process` tool, extend the message processing:
```python
# Example: Smart action detection
if "read" in content.lower() and ".md" in content:
    # Extract filename and read it
    filename = extract_filename(content)
    read_file_content(filename)
elif "urgent" in content.lower():
    # Priority handling
    send_immediate_response(sender)
```

### Additional Triggers
Beyond time-based checking:
```python
# After errors
if tool_name == "Bash" and exit_code != 0:
    trigger_check()
    
# After file writes  
if tool_name in ["Write", "Edit"]:
    trigger_check()
```

### Integration with Other MCPs
The auto-check system is MCP-agnostic and could work with any message system that provides check/send capabilities.

## Performance Impact

- Hook execution: <50ms
- Config file I/O: <10ms  
- No background processes
- No polling loops
- Scales with tool usage, not time

## Debugging

### Check Configuration
```bash
cat /tmp/claude-ipc-mcp/auto_check_config.json
```

### Monitor Triggers
```bash
ls -la /tmp/claude-ipc-mcp/auto_check_trigger
```

### View Hook Logs
Hooks run silently, but you can add debug logging:
```python
# In hook script
with open('/tmp/claude-ipc-mcp/auto_check_debug.log', 'a') as f:
    f.write(f"Check at {time.time()}: {should_trigger}\n")
```

## File Structure
```
claude-ipc-mcp/
├── src/
│   └── claude_ipc_server.py      # Added auto_process tool
├── hooks/
│   └── ipc_auto_check_hook.py    # Trigger logic
├── tools/
│   └── ipc_auto_check_manager.py # Config management
└── docs/
    ├── AUTO_CHECK_GUIDE.md       # User guide
    └── AUTO_CHECK_TECHNICAL.md   # This file
```

## Design Principles

1. **No Core Changes**: MCP server logic untouched
2. **Session Security**: Reuses existing auth
3. **User Control**: Opt-in with natural language
4. **Fail Safe**: Errors don't break manual checking
5. **Transparent**: Users see what was processed

## Current Limitations

### The "Awareness Gap"
The current implementation has an intentional limitation:

1. **Hook creates trigger file** → This works perfectly
2. **AI needs to notice trigger** → This requires the AI to be active
3. **AI runs auto_process** → This works when triggered

**Why this limitation exists:**
- Hooks can't force the AI to take action
- The AI doesn't have a background process checking for triggers
- This keeps the architecture simple and secure

**In practice:**
- During active conversations, auto-check works seamlessly
- During idle periods, messages wait until next interaction
- This is often acceptable since messages typically arrive during active work

**Potential solutions (not implemented):**
- Background polling (adds complexity)
- Push notifications (requires architecture changes)
- Scheduled tasks (platform-specific)

---
