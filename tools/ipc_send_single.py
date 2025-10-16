#!/usr/bin/env python3
"""Send a message to another instance via IPC"""
import socket
import json
import sys
import os

if len(sys.argv) < 3:
    print("Usage: ipc_send.py <to_instance_id> <message>")
    print("Example: ipc_send.py barney \"Hello from Fred!\"")
    sys.exit(1)

to_id = sys.argv[1]
message_content = " ".join(sys.argv[2:])  # Join all remaining args as message

try:
    # Load session token
    session_file = os.path.expanduser("~/.ipc-session")
    if not os.path.exists(session_file):
        print("Error: Not registered. Run ipc_register.py first.")
        sys.exit(1)
    
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    from_id = session_data["instance_id"]
    session_token = session_data["session_token"]
    
    # Connect to IPC server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))
    
    # Send message request
    request = {
        "action": "send",
        "from_id": from_id,
        "to_id": to_id,
        "message": {
            "content": message_content
        },
        "session_token": session_token
    }
    s.send(json.dumps(request).encode("utf-8"))
    
    # Get response
    response_data = s.recv(65536).decode("utf-8")
    response = json.loads(response_data)
    
    if response.get("status") == "ok":
        print(f"Sent to {to_id}: {message_content}")
    else:
        print(json.dumps(response, indent=2))
    
    s.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)