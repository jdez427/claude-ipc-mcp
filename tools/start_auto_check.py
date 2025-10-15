# Save this as tools/start_auto_check.py
import sys
import os
import json
import time

if len(sys.argv) != 3:
    print("Usage: python start_auto_check.py <agent_name> <interval_minutes>")
    sys.exit(1)

agent_name = sys.argv[1]
try:
    interval_minutes = float(sys.argv[2])
    if interval_minutes <= 0:
        raise ValueError("Interval must be positive.")
except ValueError as e:
    print(f"Error: Invalid interval. {e}")
    sys.exit(1)

config_path = os.path.expanduser(f"~/.ipc-auto-check-{agent_name}.json")
config = {
    "agent_name": agent_name,
    "interval_seconds": interval_minutes * 60,
    "last_check_timestamp": 0  # Set to 0 to trigger an immediate first check
}

with open(config_path, "w") as f:
    json.dump(config, f)

os.chmod(config_path, 0o600)
print(f"✅ Auto-check enabled for '{agent_name}'. Will check every {interval_minutes} minute(s).")