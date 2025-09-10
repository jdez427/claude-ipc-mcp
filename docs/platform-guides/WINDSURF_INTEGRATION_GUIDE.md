# 🪟 Windsurf Integration Guide for Claude IPC MCP

> **✅ This procedure was verified on Windows 10**
> 
> This guide will help you set up Claude IPC MCP to work with Windsurf IDE, enabling your AI assistant (Cascade) to communicate with other AI assistants like Claude Code and Google Gemini.

## 📋 Table of Contents
1. [What This Guide Does](#what-this-guide-does)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Testing Your Setup](#testing-your-setup)
5. [Using IPC in Windsurf](#using-ipc-in-windsurf)
6. [Troubleshooting](#troubleshooting)
7. [After a Reboot](#after-a-reboot)
8. [FAQ](#faq)

## 🎯 What This Guide Does

This guide will enable your Windsurf AI assistant (Cascade) to:
- 💬 Send messages to other AI assistants (Claude Code, Gemini, etc.)
- 📨 Receive messages from other AIs
- 🤝 Collaborate with multiple AIs on the same project
- 🖥️ Work across Windows and WSL (Windows Subsystem for Linux)

**Time Required**: About 15-20 minutes

## ✅ Prerequisites

### 1. Windsurf IDE
You need Windsurf installed on Windows. If you don't have it:
- Download from: https://windsurf.com/editor
- Install with default settings

### 2. Python (Check First!)

Open PowerShell and type:
```powershell
python --version
```

**If you see** `Python 3.12.x` or higher ➡️ Skip to step 3!

**If you get an error**:
1. Go to https://www.python.org/downloads/
2. Download Python 3.12 or newer
3. **IMPORTANT**: During installation, ✅ CHECK "Add Python to PATH"
4. After installation, close and reopen PowerShell
5. Verify with `python --version`

### 3. A Way to Get the Code

You need ONE of these:
- **GitHub Desktop** (easiest) - Download from https://desktop.github.com/
- **Git for Windows** - From https://git-scm.com/download/win
- **Web browser** (to download a ZIP file)

## 🚀 Step-by-Step Installation

### Step 1: Get the Claude IPC MCP Code

#### Option A: Using GitHub Desktop (Recommended for Beginners)
1. Open GitHub Desktop
2. Click `File` → `Clone Repository`
3. Click the `URL` tab
4. Paste: `https://github.com/jdez427/claude-ipc-mcp.git`
5. For "Local Path", browse to: `C:\Users\[YourUsername]\Documents`
6. Click `Clone`

#### Option B: Using Git Command Line
Open PowerShell and run:
```powershell
cd C:\Users\$env:USERNAME\Documents
git clone https://github.com/jdez427/claude-ipc-mcp.git
```

#### Option C: Download ZIP (No Git Needed)
1. Go to https://github.com/jdez427/claude-ipc-mcp
2. Click the green `Code` button
3. Click `Download ZIP`
4. Extract to `C:\Users\[YourUsername]\Documents\`
5. Rename the folder from `claude-ipc-mcp-main` to `claude-ipc-mcp`

### Step 2: Install UV (Python Package Manager)

In PowerShell, run this command:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You should see:
```
everything's installed!
```

**If you get a security error**, run PowerShell as Administrator and try:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then run the UV install command again.

### Step 3: Add UV to Your Current Session

Run this command exactly as shown:
```powershell
$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
```

This makes UV available for the next steps.

### Step 4: Install IPC Dependencies

Navigate to the IPC folder:
```powershell
cd C:\Users\$env:USERNAME\Documents\claude-ipc-mcp
```

Install dependencies:
```powershell
uv sync
```

This will download and install all required packages. You'll see progress messages.

### Step 5: Configure Windsurf

First, create the configuration directory:
```powershell
mkdir C:\Users\$env:USERNAME\.codeium\windsurf -Force
```

Now create the configuration file:
```powershell
notepad C:\Users\$env:USERNAME\.codeium\windsurf\mcp_config.json
```

Notepad will open. Choose ONE of these configurations:

#### Option A: Open Mode (No Authentication - Recommended for Personal Use)
```json
{
  "mcpServers": {
    "claude-ipc": {
      "command": "uvx",
      "args": ["--from", "C:\\Users\\YOUR_USERNAME\\Documents\\claude-ipc-mcp", "claude-ipc-mcp"]
    }
  }
}
```

#### Option B: Secure Mode (With Shared Secret)
```json
{
  "mcpServers": {
    "claude-ipc": {
      "command": "uvx",
      "args": ["--from", "C:\\Users\\YOUR_USERNAME\\Documents\\claude-ipc-mcp", "claude-ipc-mcp"],
      "env": {
        "IPC_SHARED_SECRET": "your-secret-key-here"
      }
    }
  }
}
```

**IMPORTANT**: 
- Replace `YOUR_USERNAME` with your actual Windows username!
- If using Secure Mode, replace `your-secret-key-here` with your chosen secret
- All AIs must use the same secret to communicate

For example, if your username is "john" and using Open Mode:
```json
"args": ["--from", "C:\\Users\\john\\Documents\\claude-ipc-mcp", "claude-ipc-mcp"]
```

Save the file (Ctrl+S) and close Notepad.

### Step 6: Test the Installation (Optional but Recommended)

Let's verify everything works before connecting to Windsurf:

```powershell
cd C:\Users\$env:USERNAME\Documents\claude-ipc-mcp
C:\Users\$env:USERNAME\.local\bin\uvx.exe --from . claude-ipc-mcp
```

You should see:
```
INFO:claude_ipc_server:SQLite database initialized...
INFO:claude_ipc_server:Message broker listening on 127.0.0.1:9876
```

Press `Ctrl+C` to stop the test.

### Step 7: Restart Windsurf

1. **Completely close Windsurf**:
   - Look in your system tray (bottom-right near the clock)
   - Right-click any Windsurf icon and choose Exit
2. Wait 10 seconds
3. Open Windsurf again

## 🧪 Testing Your Setup

### In Windsurf's Cascade Panel:

1. Find the Cascade panel (usually on the right side)
2. In the chat area, type:
   ```
   Register this instance as windsurf
   ```
3. You should see a confirmation message

### Test Commands:
Try these commands in Cascade:
- `List all IPC instances` - Should show "windsurf"
- `Check my messages` - Should show "No new messages"

## 💬 Using IPC in Windsurf

### Basic Commands

**Register your AI:**
```
Register this instance as [name]
```
Example: `Register this instance as windsurf`

**Send a message:**
```
Send message to [recipient]: [your message]
```
Example: `Send message to claude: Can you help with this React component?`

**Check messages:**
```
Check my messages
```

**List all AIs:**
```
List all instances
```

### Communication Example

If you have Claude Code running in WSL:
1. In Windsurf: `Send message to claude: Hello from Windows!`
2. In Claude Code: Claude types `Check my messages`
3. Claude sees your message and can reply back

## 🔧 Troubleshooting

### "uvx is not recognized"
- Run: `$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"`
- This adds UV to your current PowerShell session

### "No such file or directory"
- Check that you used double backslashes `\\` in the JSON config
- Verify the path exists: `dir C:\Users\$env:USERNAME\Documents\claude-ipc-mcp`

### Cascade doesn't recognize IPC commands
1. Check Windsurf Settings → Cascade → Plugins
2. Look for "claude-ipc" in the list
3. If not there, verify your `mcp_config.json` file
4. Make sure you fully restarted Windsurf

### "Connection refused" error
- This is normal if no AI has registered yet
- The first AI to register starts the server

### Windows Defender / Firewall Alert
- If prompted, allow the connection
- IPC only uses localhost (127.0.0.1), not internet

### "Invalid auth token" error
- This means you're trying to connect with different security modes
- Solution: All AIs must either use Open Mode OR all use the same shared secret
- Check your `mcp_config.json` configuration

## 🔄 After a Reboot

The good news: **Almost everything persists!**

What stays configured:
- ✅ Windsurf MCP configuration
- ✅ Your IPC installation
- ✅ All messages in the database

What you might need to do:
- If UV commands don't work in PowerShell, run:
  ```powershell
  $env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
  ```

To make UV permanent (optional):
1. Press `Win + X` → System
2. Advanced system settings → Environment Variables
3. Under User variables, edit Path
4. Add: `C:\Users\[YourUsername]\.local\bin`

## ❓ FAQ

**Q: Do I need to keep PowerShell open?**
A: No! Once configured, Windsurf handles everything automatically.

**Q: Where are messages stored?**
A: In `C:\Users\[YourUsername]\.claude-ipc-data\messages.db`

**Q: Can I use this with WSL?**
A: Yes! Windows Windsurf can communicate with Claude Code running in WSL.

**Q: What is "open mode"?**
A: It means no password/authentication is required. Good for personal use.

**Q: Should I use Open Mode or Secure Mode?**
A: 
- **Open Mode**: Perfect for personal use on your own computer
- **Secure Mode**: Better if multiple people use your computer or for production environments

**Q: How do I switch between Open and Secure mode?**
A: Edit your `mcp_config.json` file and either add or remove the `env` section with the shared secret.

**Q: How do I know it's working?**
A: If "Register this instance" works in Cascade, everything is set up correctly!

**Q: Can multiple AIs run at once?**
A: Yes! The first one becomes the server, others connect as clients.

---

**Need more help?** Check the main [README](../README.md) or create an issue on GitHub!