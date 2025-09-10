# 🏗️ Claude IPC MCP - Architecture Documentation

> Understanding the democratic, serverless design

## Table of Contents
1. [Core Design Principles](#core-design-principles)
2. [Component Overview](#component-overview)
3. [The Democratic Broker](#the-democratic-broker)
4. [Message Flow](#message-flow)
5. [Security Architecture](#security-architecture)
6. [Session Management](#session-management)
7. [Advanced Features](#advanced-features)
8. [Implementation Details](#implementation-details)

## Core Design Principles

### 1. Democratic Server Model
- **No dedicated server** - any AI can be the server
- **First come, first served** - first AI to start claims port 9876
- **Automatic failover** - if server dies, next AI can take over
- **Equal participants** - server AI can also send/receive messages

### 2. Simplicity First
- **Single file implementation** - one Python file does everything
- **No external dependencies** - just Python stdlib + MCP
- **TCP sockets** - universal, simple, reliable
- **JSON protocol** - human-readable, debuggable

### 3. AI-Friendly
- **Natural language** - Claude can use English commands
- **Script-based** - Gemini/others use simple Python scripts
- **Forgiving** - handles future messages, renames, large content

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Instance                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            claude_ipc_server.py (MCP)               │   │
│  │  ┌─────────────────┐  ┌──────────────────────┐     │   │
│  │  │   MCP Server    │  │   Message Broker     │     │   │
│  │  │  - Tools API    │  │  - TCP Server (:9876)│     │   │
│  │  │  - NLP parsing  │  │  - Message Queues   │     │   │
│  │  │  - Session mgmt │  │  - Session Validation│     │   │
│  │  └────────┬────────┘  └──────────┬───────────┘     │   │
│  │           │                      │                   │   │
│  │           └──────────┬───────────┘                  │   │
│  │                      │                              │   │
│  │              ┌───────▼────────┐                     │   │
│  │              │ BrokerClient   │                     │   │
│  │              │ - TCP Client   │                     │   │
│  │              └────────────────┘                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

                            │ TCP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gemini/Python AI                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Python Scripts                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ipc_register │  │  ipc_send   │  │ ipc_check  │  │   │
│  │  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## The Democratic Broker

### Startup Sequence

```python
# Every AI runs this code:
try:
    broker.start()  # Try to bind port 9876
    logger.info("Started message broker")
except:
    logger.info("Message broker already running")
    # Continue as client only
```

### Broker Responsibilities

1. **Message Queuing**
   - In-memory queues per instance
   - Messages survive recipient disconnection
   - 7-day retention for undelivered messages

2. **Session Management**
   - Generate secure session tokens
   - Validate sender identity
   - Prevent spoofing

3. **Name Resolution**
   - Handle instance renames
   - Forward old names for 2 hours
   - Broadcast rename notifications

### Broker Lifecycle

```
AI #1 starts → Binds port 9876 → Becomes broker
AI #2 starts → Port busy → Connects as client
AI #3 starts → Port busy → Connects as client
AI #1 stops → Broker keeps running (separate thread)
AI #4 starts → Port busy → Connects as client
Broker crashes → Port free → Next AI can claim it
```

## Message Flow

### 1. Registration Flow

```
Client                          Broker
  │                               │
  ├─ Register Request ───────────►│
  │  {action: "register",         │
  │   instance_id: "claude",      │
  │   auth_token: "hash"}         │
  │                               │
  │◄──────── Response ────────────┤
  │  {status: "ok",               │
  │   session_token: "abc...",    │
  │   message: "Registered"}       │
  │                               │
  │ Save session locally          │
  └───────────────────────────────┘
```

### 2. Message Send Flow

```
Sender                          Broker                      Recipient
  │                               │                           │
  ├─ Send Request ───────────────►│                           │
  │  {action: "send",             │                           │
  │   from_id: "claude",          │                           │
  │   to_id: "fred",              │                           │
  │   message: {...},             │                           │
  │   session_token: "abc..."}    │                           │
  │                               │                           │
  │                               ├─ Queue Message            │
  │                               │                           │
  │◄──────── Response ────────────┤                           │
  │  {status: "ok"}               │                           │
  │                               │                           │
  │                               │      ┌─ Check Request ───┤
  │                               │      │                   │
  │                               │◄─────┘                   │
  │                               │                           │
  │                               ├─ Deliver Messages ──────►│
  │                               │                           │
  └───────────────────────────────┴───────────────────────────┘
```

### 3. Future Message Flow

```
Sender → Broker: Send to "ghost"
Broker: Create queue for "ghost"
Broker → Sender: "Queued for future delivery"

... time passes ...

Ghost → Broker: Register as "ghost"  
Broker → Ghost: "3 messages waiting"
Ghost → Broker: Check messages
Broker → Ghost: Deliver queued messages
```

## Security Architecture

### Authentication Flow

```
1. Client calculates: SHA256(instance_id + ":" + shared_secret)
2. Client sends auth_token with registration
3. Broker validates: auth_token == expected_hash
4. Broker generates: session_token = random(256 bits)
5. Broker stores: session_token → instance_id mapping
6. Client saves: session_token for future requests
```

### Session Validation

```python
# Every request (except registration)
if action != "register":
    session = validate_session(request.session_token)
    if not session:
        return error("Invalid session")
    
    # Use verified identity, ignore claimed identity
    true_instance_id = session.instance_id
```

### Security Properties

| Property | Implementation |
|----------|----------------|
| Authentication | Shared secret validates registration |
| Authorization | Session token required for actions |
| Identity | Can't spoof another instance |
| Confidentiality | None (localhost only) |
| Integrity | None (trust localhost) |
| Availability | Resilient to instance failures |

## Session Management

### Session Lifecycle

```
Register → Generate Token → Store Mapping → Use Token → Rename? → Update Mapping
```

### Session Storage

**In Broker (Memory):**
```python
sessions = {
    "token123...": {
        "instance_id": "claude",
        "created_at": datetime.now()
    }
}
instance_sessions = {
    "claude": "token123..."
}
```

**In Client (File):**
```json
// ~/.ipc-session
{
    "instance_id": "fred",
    "session_token": "token456..."
}
```

### Session Persistence

- **MCP**: Stores in memory, lives for Claude session
- **Python**: Stores in `~/.ipc-session`, survives restarts
- **Broker**: Memory only, lost on broker restart

## Advanced Features

### 1. Large Message Handling

```python
if len(message) > 10KB:
    filepath = save_to_file(message)
    summary = create_summary(message, max=150)
    message = f"{summary}\nFull content: {filepath}"
```

**File Format:**
```
/mnt/c/Users/{username}/Documents/CODA/ipc-messages/large-messages/
└── 20240315-143022_claude_fred_message.md
    ├── Header (sender, recipient, timestamp, size)
    └── Full message content
```

### 2. Instance Renaming

```python
# Rate limited: 1 hour cooldown
if time_since_last_rename < 3600:
    return error("Rate limit")

# Update mappings
queues[new_id] = queues.pop(old_id)
instances[new_id] = instances.pop(old_id)

# Set up forwarding
name_history[old_id] = (new_id, now)  # 2 hour expiry

# Notify everyone
broadcast(f"{old_id} renamed to {new_id}")
```

### 3. Message Queuing

**Queue Properties:**
- Per-instance queues
- FIFO delivery
- Atomic check-and-clear
- 7-day retention for unregistered instances

**Queue Operations:**
```python
# Send (always succeeds)
queues[recipient].append(message)

# Check (atomic get-and-clear)
messages = queues[instance_id]
queues[instance_id] = []
return messages
```

## Implementation Details

### TCP Protocol

**Wire Format:**
```
[4 bytes length][JSON payload]
```

**Request Structure:**
```json
{
    "action": "register|send|check|list|rename|broadcast",
    "session_token": "optional",
    "instance_id": "required for some",
    "arguments": {}
}
```

**Response Structure:**
```json
{
    "status": "ok|error",
    "message": "human readable",
    "data": {}
}
```

### Threading Model

```
Main Thread
├── MCP Server (async)
│   └── Tool Handlers
└── Broker Thread (daemon)
    └── TCP Server
        └── Client Handler Threads (one per connection)
```

### Error Handling

1. **Connection Errors**: Retry with exponential backoff
2. **Protocol Errors**: Return error response
3. **Session Errors**: Force re-registration
4. **Queue Overflow**: Drop oldest messages (never implemented)

### Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Register | O(1) | O(1) |
| Send | O(1) | O(n) messages |
| Check | O(m) messages | O(1) |
| List | O(k) instances | O(1) |
| Rename | O(k) instances | O(1) |

### Scalability Limits

- **Instances**: Tested up to 10, theoretical 1000s
- **Messages**: 10,000 per queue tested
- **Message Size**: 10KB inline, unlimited via files
- **Connections**: OS TCP limit (~65k)
- **Throughput**: ~1000 msg/sec on modern hardware

## Design Decisions

### Why TCP Sockets?

✅ **Chosen**: Raw TCP sockets
- Universal support
- Simple protocol
- Direct control
- No dependencies

❌ **Rejected**: HTTP/REST
- Overkill for local IPC
- Additional complexity
- Framework dependencies

❌ **Rejected**: Unix sockets
- Windows compatibility issues
- WSL complications

### Why JSON?

✅ **Chosen**: JSON protocol
- Human readable
- Native Python support
- Easy debugging
- AI-friendly

❌ **Rejected**: Binary protocol
- Harder to debug
- No significant performance gain
- Complexity without benefit

### Why In-Memory?

✅ **Chosen**: Memory-only queues
- Simple implementation
- Fast performance
- Adequate for use case

❌ **Rejected**: Database persistence
- Overkill for ephemeral messages
- Additional dependencies
- Complexity without benefit

## Future Considerations

### Potential Enhancements

1. **Encryption**: TLS for network security
2. **Persistence**: Optional SQLite backend
3. **Clustering**: Multi-machine support
4. **Web UI**: Message history viewer
5. **Plugins**: Extensible message handlers

### Breaking Changes to Avoid

1. Changing TCP port (breaks all clients)
2. Modifying JSON structure (breaks compatibility)
3. Requiring new dependencies (breaks simplicity)
4. Changing session token format (breaks security)

---

*Architecture designed for simplicity, reliability, and AI-first usage* 🏛️