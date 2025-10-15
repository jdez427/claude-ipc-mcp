# Save this as tools/stop_auto_check.py
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python stop_auto_check.py <agent_name>")
    sys.exit(1)

agent_name = sys.argv[1]
config_path = os.path.expanduser(f"~/.ipc-auto-check-{agent_name}.json")

if os.path.exists(config_path):
    os.remove(config_path)
    print(f"⏹️ Auto-check disabled for '{agent_name}'.")
else:
    print(f"Auto-check was not active for '{agent_name}'.")