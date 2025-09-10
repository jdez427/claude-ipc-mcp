# Installing UV Package Manager

UV is a modern Python package manager that's faster and more reliable than pip. It's required for installing Claude IPC MCP.

## What is UV?

UV is a Python package and project manager written in Rust. It's:
- **10-100x faster** than pip
- **Automatic** virtual environment handling
- **Reliable** dependency resolution
- **Simple** to install and use

## Installation Methods

### Linux/Mac/WSL (Recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc on Mac
```

### Windows PowerShell

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart PowerShell.

### Windows with winget

```cmd
winget install --id=astral.uv -e
```

### Alternative: Using pip (if curl doesn't work)

```bash
pip install uv
```

### Using Homebrew (Mac)

```bash
brew install uv
```

## Verify Installation

After installing, verify UV is working:

```bash
uv --version
```

You should see something like: `uv 0.2.0 (1234abcd 2024-01-01)`

## Troubleshooting UV Installation

### "curl: command not found"

**On Windows:** Use PowerShell instead of Command Prompt, or install Git Bash

**On Linux:** Install curl first:
```bash
sudo apt-get install curl  # Debian/Ubuntu
sudo yum install curl      # RHEL/CentOS
```

### "Permission denied"

The installer needs to write to your home directory. Make sure you're not using `sudo` with the curl command.

### UV command not found after installation

The installer adds UV to your PATH, but you need to reload your shell:

**Linux/Mac/WSL:**
```bash
# Option 1: Restart terminal
# Option 2: Reload config
source ~/.bashrc  # or ~/.zshrc
# Option 3: Use full path
~/.cargo/bin/uv --version
```

**Windows:**
- Close and reopen PowerShell/Command Prompt
- Or use full path: `%USERPROFILE%\.cargo\bin\uv.exe`

### Behind a Corporate Proxy

Set proxy environment variables first:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation Failed

If the automatic installer doesn't work, you can:

1. **Use pip instead:**
   ```bash
   pip install uv
   ```

2. **Download directly from GitHub:**
   Visit https://github.com/astral-sh/uv/releases
   Download the appropriate binary for your system

3. **Use a package manager:**
   - Mac: `brew install uv`
   - Windows: `winget install astral.uv`
   - Linux: Check your distribution's package manager

## Why UV Instead of pip?

| Feature | UV | pip |
|---------|-----|-----|
| Speed | 10-100x faster | Baseline |
| Lock files | Built-in | Requires pip-tools |
| Python management | Built-in | Requires pyenv |
| Virtual envs | Automatic | Manual activation |
| Dependency resolution | Fast & reliable | Can be slow |

## Next Steps

Once UV is installed, return to the [main installation guide](../INSTALL.md) and continue with Step 2.

## More Information

- UV Documentation: https://github.com/astral-sh/uv
- UV Blog Post: https://astral.sh/blog/uv

---
*If you still can't install UV after trying these methods, you can use traditional pip installation, though it will be slower and less reliable.*