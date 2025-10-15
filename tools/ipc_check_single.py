#!/usr/bin/env python3
"""Check for messages from the IPC server"""
import socket
import json
import sys
import os

try:
    # Load session token
    session_file = os.path.expanduser("~/.ipc-session")
    if not os.path.exists(session_file):
        print("Error: Not registered. Run ipc_register.py first.")
        sys.exit(1)
    
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    instance_id = session_data["instance_id"]
    session_token = session_data["session_token"]
    
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