#!/usr/bin/env python3
"""
Check for messages for a specific instance from the IPC server.
This version requires the instance_id as a command-line argument
to avoid ambiguity in multi-session environments.
"""
import socket
import json
import sys
import os

# --- MODIFICATION START ---
# Require instance_id as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python ipc_check.py <instance_id>")
    print("Error: This script requires the instance ID to know who is checking.")
    sys.exit(1)

instance_id = sys.argv[1]
# --- MODIFICATION END ---

try:
    # --- MODIFICATION START ---
    # Directly look for the specific session file for the given instance_id
    session_file = os.path.expanduser(f"~/.ipc-session-{instance_id}")
    
    if not os.path.exists(session_file):
        print(f"Error: Not registered. No session file found for '{instance_id}'.")
        print("Please register first using 'Register this instance as <instance_id>'.")
        sys.exit(1)
        
    with open(session_file, "r") as f:
        session_data = json.load(f)
    # --- MODIFICATION END ---
    
    # We already have the correct instance_id from the argument
    session_token = session_data["session_token"]
    
    print(f"Using session file: {os.path.basename(session_file)}")
    print(f"Checking messages for: {instance_id}")
    
    # Connect to IPC server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))
    
    # Send check request
    request = {
        "action": "check",
        "instance_id": instance_id,
        "session_token": session_token
    }
    s.send(json.dumps(request).encode("utf-8"))
    
    # Get response
    response_data = s.recv(65536).decode("utf-8")
    response = json.loads(response_data)
    
    s.close()
    
    # Format output nicely
    if response.get("status") == "ok":
        messages = response.get("messages", [])
        if messages:
            print("New messages:")
            print("-" * 50)
            for msg in messages:
                print(f"From: {msg['from']}")
                print(f"Time: {msg['timestamp']}")
                print(f"Content: {msg['message']['content']}")
                if msg['message'].get('data'):
                    print(f"Data: {json.dumps(msg['message']['data'], indent=2)}")
                print("-" * 50)
        else:
            print("No new messages")
    else:
        print(f"Error: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)