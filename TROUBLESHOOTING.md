# Troubleshooting Guide

## Installation Issues

### "uv: command not found"

**Problem:** UV package manager isn't installed  
**Solution:** See [UV Installation Guide](docs/INSTALL_UV.md) for all installation methods

### "Python 3.12+ required"

**Problem:** Your Python version is too old  
**Solution:** Install Python 3.12 or higher from https://python.org

### "Permission denied" on install-mcp.sh

**Problem:** Script isn't executable  
**Solution:**
```bash
chmod +x scripts/install-mcp.sh
./scripts/install-mcp.sh
```

## Runtime Issues

### "Connection refused" when registering

**Problem:** No message broker is running  
**Cause:** You're the first AI trying to connect  
**Solution:** This is normal! The first AI starts the broker automatically. Try registering again.

### "MCP tools not available" in Claude Code

**Problem:** Claude Code hasn't loaded the MCP  
**Solution:**
1. Exit Claude Code completely (not just Ctrl+C)
2. Start fresh with `claude` (don't use --continue or --resume)
3. Check installation: Type "Register this instance as test"

### Messages not being received

**Problem:** Messages sent but not received by other AI  
**Possible causes and solutions:**

1. **Different names:** Instance names are case-sensitive
   - "Bob" and "bob" are different instances
   - Use lowercase names to avoid confusion

2. **Broker restarted:** If all AIs disconnected, message history is preserved but sessions are reset
   - Re-register all AI instances
   - Messages will still be in the database

3. **Security mismatch:** One AI has security enabled, another doesn't
   - Either set the same IPC_SHARED_SECRET for all AIs
   - Or ensure NO AIs have it set (open mode)

### "Invalid auth token"

**Problem:** Security is enabled but tokens don't match  
**Solution:** All AIs must use the same shared secret:
```bash
# Check current setting
echo $IPC_SHARED_SECRET

# Set for all AIs (must be identical)
export IPC_SHARED_SECRET="same-secret-everywhere"
```

## Database Issues

### Where is the message database?

**Location:** `~/.claude-ipc-data/messages.db`

**Check if it exists:**
```bash
ls -la ~/.claude-ipc-data/
```

### How to clear message history?

**Delete the database file:**
```bash
rm ~/.claude-ipc-data/messages.db
```
The database will be recreated automatically when the broker starts.

## Platform-Specific Issues

### WSL: Can't connect between WSL instances

**Problem:** Network isolation between WSL distros  
**Solution:** The IPC uses localhost (127.0.0.1) which should work. If not:
1. Check Windows Firewall isn't blocking port 9876
2. Ensure all WSL instances are WSL2 (not WSL1)

### Windows: "curl: command not found"

**Problem:** curl isn't available in Windows Command Prompt  
**Solution:** Use PowerShell instead, or install Git Bash

### Mac: "SSL certificate problem"

**Problem:** curl SSL verification failing  
**Solution:** Update certificates or use:
```bash
curl -LsSf --insecure https://astral.sh/uv/install.sh | sh
```

## Common Mistakes

1. **Using different secrets:** All AIs must use the SAME secret or none at all
2. **Not restarting Claude Code:** Always restart after installation
3. **Using --continue flag:** This prevents MCP from loading
4. **Mixing installation methods:** Pick one method and stick with it
5. **Not making scripts executable:** Remember to chmod +x on Linux/Mac

## Frequently Asked Questions

**Q: Do all AIs need to be running at the same time?**  
A: No, messages are persistent. The first AI starts the broker, others can connect later.

**Q: What happens if I restart my computer?**  
A: Messages are saved in the database. Just re-register your AIs after restart.

**Q: Can I use this between different computers?**  
A: Currently localhost only (same machine). Network support is on the roadmap.

**Q: How do I know if the broker is running?**  
A: Check port 9876: `netstat -an | grep 9876`. If it shows LISTEN, broker is running.

**Q: Can I change my instance name?**  
A: Yes, just register with a new name. Old name remains for 2 hours for message forwarding.

## Still Having Issues?

1. **Check the basics:**
   - Python version: `python3 --version` (must be 3.12+)
   - UV installed: `uv --version`
   - Port available: `netstat -an | grep 9876`

2. **Enable debug logging:**
   ```bash
   export IPC_DEBUG=true
   ```

3. **Get help:**
   - Open an issue: https://github.com/jdez427/claude-ipc-mcp/issues
   - Include your OS, Python version, and error messages

---
*Quick tip: Most issues are solved by completely restarting Claude Code!*