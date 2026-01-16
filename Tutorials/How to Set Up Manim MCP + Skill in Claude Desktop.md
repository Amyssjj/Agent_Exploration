# How to Set Up Manim MCP + Skill in Claude Desktop

This tutorial will guide you through configuring the Manim MCP server and creating a Skill, enabling Claude to generate mathematical animations directly.

---

## 📋 Table of Contents

1. [What are MCP and Skill?](#1-what-are-mcp-and-skill)
2. [Prerequisites](#2-prerequisites)
3. [Install Manim MCP Server](#3-install-manim-mcp-server)
4. [Configure Claude Desktop to Connect MCP](#4-configure-claude-desktop-to-connect-mcp)
5. [Create Manim Skill](#5-create-manim-skill)
6. [Test and Verify](#6-test-and-verify)
7. [Usage Examples](#7-usage-examples)

---

## 1. What are MCP and Skill?

### MCP (Model Context Protocol)
MCP is a protocol developed by Anthropic that allows Claude to interact with external tools and services. Through MCP, Claude can:
- Execute code
- Access file systems
- Call external APIs
- Run local programs (like Manim)

### Skill
A Skill is a guidance file (SKILL.md) that tells Claude:
- When to use this tool
- How to use this tool correctly
- Best practices and common mistakes to avoid

**The relationship**: MCP provides capability, Skill provides wisdom.

---

## 2. Prerequisites

Before starting, make sure you have installed:

### Required Software
```bash
# Python 3.8+
python --version

# pip
pip --version
```

### Install Manim
```bash
# Install Manim using pip
pip install manim

# Verify installation
manim --version
```

### Claude Desktop
Make sure you have installed [Claude Desktop](https://claude.ai/download).

---

## 3. Install Manim MCP Server

We'll use the open-source project [manim-mcp-server](https://github.com/abhiemj/manim-mcp-server) by **abhiemj** (featured in Awesome MCP Servers).

### Step 1: Install MCP

```bash
pip install mcp
```

### Step 2: Clone the Repository

```bash
# Choose a directory to store the project
cd ~/Documents  # or any directory you prefer

# Clone the repository
git clone https://github.com/abhiemj/manim-mcp-server.git

cd manim-mcp-server
```

### Step 3: (Optional) Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Install dependencies
pip install manim mcp
```

### Step 4: Find the Required Paths

After installation, you need to gather the following information:

#### 🔍 Find your Python path

```bash
# macOS / Linux
which python

# Windows (PowerShell)
(Get-Command python).Source

# Windows (Command Prompt)
where python
```

**Common paths:**
| OS | Typical Path |
|---------|---------|
| macOS | `/usr/bin/python3` or `/Users/username/.pyenv/shims/python` |
| Linux | `/usr/bin/python3` or `/home/username/.local/bin/python` |
| Windows | `C:\Users\username\AppData\Local\Programs\Python\Python3x\python.exe` |

If using a virtual environment, use the Python inside venv:
- macOS/Linux: `/path/to/manim-mcp-server/venv/bin/python`
- Windows: `C:\path\to\manim-mcp-server\venv\Scripts\python.exe`

#### 🔍 Find the server script path

The main script is located at:
```
/path/to/manim-mcp-server/src/manim_server.py
```

#### 🔍 Find the Manim executable path (if needed)

```bash
# macOS / Linux
which manim

# Windows
where manim
```

#### 📋 Record your configuration info

After running the commands above, record the following:

```
✅ Python path: _________________
   (e.g., /Users/john/Documents/manim-mcp-server/venv/bin/python)

✅ Server script path: _________________
   (e.g., /Users/john/Documents/manim-mcp-server/src/manim_server.py)

✅ Manim executable (optional): _________________
   (e.g., /Users/john/Documents/manim-mcp-server/venv/bin/manim)
```

---

## 4. Configure Claude Desktop to Connect MCP

### Step 1: Locate the config file

Claude Desktop's MCP configuration file location:

| OS | Config File Path |
|---------|-------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

### Step 2: Edit the config file

Open the config file and fill in the paths you found in Step 3:

**macOS / Linux example:**
```json
{
  "mcpServers": {
    "manim-server": {
      "command": "/Users/your_username/Documents/manim-mcp-server/venv/bin/python",
      "args": [
        "/Users/your_username/Documents/manim-mcp-server/src/manim_server.py"
      ]
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "manim-server": {
      "command": "C:\\Users\\your_username\\Documents\\manim-mcp-server\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\your_username\\Documents\\manim-mcp-server\\src\\manim_server.py"
      ]
    }
  }
}
```

**If Manim is not in your PATH, add the MANIM_EXECUTABLE environment variable:**
```json
{
  "mcpServers": {
    "manim-server": {
      "command": "/Users/your_username/Documents/manim-mcp-server/venv/bin/python",
      "args": [
        "/Users/your_username/Documents/manim-mcp-server/src/manim_server.py"
      ],
      "env": {
        "MANIM_EXECUTABLE": "/Users/your_username/Documents/manim-mcp-server/venv/bin/manim"
      }
    }
  }
}
```

> ⚠️ **Important Notes:**
> - Replace `your_username` with your actual username
> - Use the actual paths you found in Step 3
> - Windows paths need double backslashes `\\` or single forward slashes `/`
> - Make sure all paths are absolute paths (starting from root)

### Step 3: Restart Claude Desktop

After saving the config file, completely quit and reopen Claude Desktop.

### Step 4: Verify connection

In Claude Desktop, you should see the MCP tool connected. Verify by asking Claude:

> "What MCP tools do you have available?"

---

## 5. Create Manim Skill (Teaching Claude How to Use It)

A Skill file tells Claude **when** to use Manim and **how to use it well**.

### Step 1: Create the SKILL.md file

Create a file anywhere on your computer named `manim-skill.md` with the following content:

```markdown
# Manim Animation Guide

Use the Manim MCP tool when users request animations, visualizations, or math demonstrations.

## When to Use Manim
- Mathematical animations (geometry, formula derivations)
- Data visualizations (pie charts, bar charts)
- Educational demonstration videos
- Any request involving "animation" or "Manim"

## Key Rules

### 1. Always add wait() after each animation
```python
self.play(Write(title), run_time=1)
self.wait(0.5)  # ← Required! Prevents frame cutoff
```

### 2. Use buff parameter for element positioning
```python
title.to_edge(UP, buff=0.6)  # Title with margin
label.next_to(bar, UP, buff=0.15)  # Labels don't overlap
```

### 3. Pie chart data must equal 100%
```python
data = [45, 35, 15, 5]  # Must sum to 100
```

### 4. Common Animations
- FadeIn / FadeOut - fade effects
- Write - writing effect
- Transform - morphing
- GrowFromCenter - grow from center

### 5. Colors
RED, BLUE, GREEN, YELLOW, WHITE, GOLD, TEAL, PURPLE
Or use hex: color="#FFD700"
```

### Step 2: Add to Project in Claude Desktop

1. Open **Claude Desktop**
2. Click **"Projects"** in the left sidebar
3. Click **"Create Project"** to create a new project, e.g., **"Manim Animations"**
4. Enter the project, click the **settings icon ⚙️** in the top right
5. Find the **"Project Knowledge"** section
6. Click **"Add Content"** → **"Upload Files"**
7. Upload the `manim-skill.md` file you just created

### Step 3: Verify the Skill is active

Start a new conversation in this project and ask Claude:

> "Do you know how to use Manim? What should I be careful about?"

Claude should mention `wait()`, `buff` spacing, and other tips from your Skill file.

---

> 💡 **Tip**: Keep all your Manim-related conversations in this project, and Claude will automatically reference the Skill file.

---

## 6. Test and Verify

### Test 1: Check MCP connection
```
Can you see the Manim MCP tool? Please list the available tools.
```

### Test 2: Simple animation
```
Create a simple Manim animation: a blue circle moving from left to right.
```

### Test 3: Math formula
```
Create a Manim animation demonstrating the Pythagorean theorem a² + b² = c²
```

### Expected Results
- Claude should automatically recognize this as a Manim task
- Call the `execute_manim_code` tool
- Generate and return a video file

---

## 7. Usage Examples

### Example 1: Basic geometry animation
```
Create a Manim animation showing a square transforming into a circle
```

### Example 2: Data visualization
```
Create a Manim pie chart animation showing:
- Apple 45%
- Banana 30%
- Orange 25%
```

### Example 3: Math education
```
Create a Manim animation demonstrating the integral ∫x² dx from 0 to 1
```

---

## 📝 Troubleshooting

### Problem: MCP not connected
- Check if the JSON format in config file is correct
- Verify all paths are correct and absolute
- Restart Claude Desktop
- Check Claude Desktop logs for errors

### Problem: Manim execution fails
- Verify Manim is installed correctly: `manim --version`
- Check Python environment
- Make sure you're using the Python from your virtual environment
- Check error logs

### Problem: Claude doesn't know to use Manim
- Verify SKILL.md is properly configured
- Make sure you're in the correct project
- Explicitly tell Claude "use Manim to create..."

### Problem: "command not found" errors
- Use absolute paths instead of relative paths
- If using venv, point to the Python inside venv folder
- Check file permissions

---

## 🎯 Summary

Complete workflow for setting up Manim MCP + Skill:

1. ✅ Install Manim and dependencies
2. ✅ Clone and set up manim-mcp-server
3. ✅ Configure Claude Desktop's `claude_desktop_config.json`
4. ✅ Create SKILL.md guidance file
5. ✅ Add Skill to Project Knowledge
6. ✅ Test and verify

After completing these steps, you can directly ask Claude to generate mathematical animations!

---

## 📚 References

- [Manim MCP Server (GitHub)](https://github.com/abhiemj/manim-mcp-server)
- [Manim Documentation](https://docs.manim.community/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop Download](https://claude.ai/download)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)
