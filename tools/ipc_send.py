#!/usr/bin/env python3
"""
Send a message to another instance via IPC.
This version requires the from_id (sender) as a command-line argument
to avoid ambiguity in multi-session environments.
"""
import socket
import json
import sys
import os

# --- MODIFICATION START ---
# Require from_id, to_id, and a message
if len(sys.argv) < 4:
    print("Usage: python ipc_send.py <from_instance_id> <to_instance_id> <message>")
    print("Example: python ipc_send.py alice bob \"Hello from Alice!\"")
    sys.exit(1)

from_id = sys.argv[1]
to_id = sys.argv[2]
message_content = " ".join(sys.argv[3:])  # Join all remaining args as message
# --- MODIFICATION END ---

try:
    # --- MODIFICATION START ---
    # Directly look for the specific session file for the sender (from_id)
    session_file = os.path.expanduser(f"~/.ipc-session-{from_id}")

    if not os.path.exists(session_file):
        print(f"Error: Not registered. No session file found for sender '{from_id}'.")
        print(f"Please ensure '{from_id}' is registered first.")
        sys.exit(1)

    with open(session_file, "r") as f:
        session_data = json.load(f)
    # --- MODIFICATION END ---
    
    # We already have the correct from_id from the argument
    session_token = session_data["session_token"]
    
    print(f"Using session file: {os.path.basename(session_file)}")
    print(f"Sending from: {from_id} To: {to_id}")
    
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
        print(f"Message successfully sent to {to_id}.")
    else:
        print(json.dumps(response, indent=2))
    
    s.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)