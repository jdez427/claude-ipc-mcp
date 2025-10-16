# Save this as hooks/ipc_intelligent_hook.py
import os
import sys
import json
import time
import subprocess

def main():
    
    # At the start of main() in ipc_intelligent_hook.py
    with open("C:\\OFA\\hook_debug.txt", "a") as f:
        f.write(f"Hook triggered, agent: {os.environ.get('IPC_AGENT_NAME')}\n")
    
    agent_name = os.environ.get('IPC_AGENT_NAME')
    if not agent_name:
        return

    config_path = os.path.expanduser(f"~/.ipc-auto-check-{agent_name}.json")
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        last_check = config.get("last_check_timestamp", 0)
        interval = config.get("interval_seconds", 300)
        current_time = time.time()

        if (current_time - last_check) >= interval:
            # Get the directory where THIS script lives (hooks/)
            hook_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Go up one level to src/, then into tools/
            src_dir = os.path.dirname(hook_dir)
            check_script = os.path.join(src_dir, "tools", "ipc_check.py")
            
            # Verify the script exists before running
            if not os.path.exists(check_script):
                return
            
            subprocess.run([sys.executable, check_script, agent_name])

            config["last_check_timestamp"] = current_time
            with open(config_path, 'w') as f:
                json.dump(config, f)

    except Exception:
        pass

if __name__ == "__main__":
    main()