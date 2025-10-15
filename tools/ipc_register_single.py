#!/usr/bin/env python3
"""Register an instance with the IPC server"""
import socket
import json
import sys
import os
import hashlib

if len(sys.argv) != 2:
    print("Usage: ipc_register.py <instance_id>")
    sys.exit(1)

instance_id = sys.argv[1]

try:
    # Calculate auth token if shared secret is set
    shared_secret = os.environ.get("IPC_SHARED_SECRET", "")
    auth_token = ""
    if shared_secret:
        auth_token = hashlib.sha256(f"{instance_id}:{shared_secret}".encode()).hexdigest()
    
    # Connect to IPC server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 9876))
    
    # Send registration request
    request = {
        "action": "register",
        "instance_id": instance_id,
        "auth_token": auth_token
    }
    s.send(json.dumps(request).encode("utf-8"))
    
    # Get response
    response_data = s.recv(65536).decode("utf-8")
    response = json.loads(response_data)
    
    # Save session token if successful
    if response.get("status") == "ok" and response.get("session_token"):
        session_file = os.path.expanduser("~/.ipc-session")
        with open(session_file, "w") as f:
            json.dump({
                "instance_id": instance_id,
                "session_token": response["session_token"]
            }, f)
        os.chmod(session_file, 0o600)  # Make it readable only by owner
        print(f"Registered as {instance_id}")
        if "message" in response:
            print(response["message"])
    else:
        print(json.dumps(response, indent=2))
    
    s.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)