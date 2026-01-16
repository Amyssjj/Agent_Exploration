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

---
name: manim-mcp

description: Create mathematical animations using Manim via MCP server. Use when the user asks to create animations, visualizations, or videos involving mathematics, geometry, graphs, transformations, data visualizations, charts, or any animated educational content. Triggers include requests for animated circles, squares, graphs, equations, geometric transformations, pie charts, bar charts, or any "Manim animation".

---

# Manim MCP

Create mathematical animations using the Manim MCP server.

## MCP Tools Available

The Manim MCP server provides tools for creating and rendering animations. Use the MCP tools directly rather than writing Python scripts manually.

## Workflow

1. Use the Manim MCP tools to create scenes and animations
2. The MCP server handles rendering with the configured Manim executable
3. Output videos are generated in the configured output directory

---

## CRITICAL: Animation Quality Guidelines

Follow these rules to ensure high-quality animations on the first attempt.

### 1. Animation Timing (Prevent Mid-Animation Captures)

**ALWAYS add `self.wait()` after every animation to ensure completion:**

```python
# ✅ CORRECT - Wait after each animation
self.play(Write(title), run_time=1)
self.wait(0.5)  # CRITICAL: Let animation fully complete
self.play(FadeIn(subtitle), run_time=0.5)
self.wait(0.5)  # CRITICAL: Pause before next animation

# ❌ WRONG - No wait between animations
self.play(Write(title), run_time=1)
self.play(FadeIn(subtitle), run_time=0.5)  # May capture mid-transition
```

**Recommended wait times:**
- After title/header animations: `self.wait(0.5)`
- After main content appears: `self.wait(1)` to `self.wait(2)`
- Between scene transitions: `self.wait(0.3)`
- At end of scene before FadeOut: `self.wait(2)` (let viewer read)

### 2. Positioning (Prevent Overlapping Elements)

**ALWAYS use `.next_to()` with explicit `buff` parameter:**

```python
# ✅ CORRECT - Explicit positioning with buffers
title.to_edge(UP, buff=0.6)  # Title at top with padding
value_label.next_to(bar, UP, buff=0.15)  # Label above bar
country_label.next_to(bar, DOWN, buff=0.15)  # Label below bar

# ❌ WRONG - Overlapping risk
title.to_edge(UP)  # May overlap with content
value_label.move_to(bar.get_top())  # Will overlap with bar
```

**Minimum buffer values:**
- Title to content: `buff=0.5` minimum
- Labels to shapes: `buff=0.15` minimum
- Between text lines: `buff=0.3` minimum
- Edge padding: `buff=0.4` minimum

### 3. Data Visualization Rules

#### Pie Charts - MUST Sum to 100%

```python
# ✅ CORRECT - Verify data integrity
data = [45, 35, 15, 5]  # US, APAC, Europe, Other
assert sum(data) == 100, f"Pie chart must sum to 100%, got {sum(data)}"

# Create sectors using AnnularSector (NOT Sector)
sectors = VGroup()
start_angle = 90  # Start from top
radius = 2

for value, color in zip(data, colors):
    angle = value * 3.6  # 360/100 = 3.6 degrees per percent
    sector = AnnularSector(
        inner_radius=0,
        outer_radius=radius,
        angle=angle * DEGREES,
        start_angle=start_angle * DEGREES,
        fill_color=color,
        fill_opacity=1,
        stroke_color=WHITE,
        stroke_width=2
    )
    sectors.add(sector)
    start_angle += angle

# ALWAYS add a legend for pie charts
legend = VGroup()
for label, color in zip(labels, colors):
    dot = Dot(color=color, radius=0.12)
    text = Text(label, font_size=24)
    item = VGroup(dot, text).arrange(RIGHT, buff=0.2)
    legend.add(item)
legend.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
legend.move_to(RIGHT * 3.5)  # Position away from pie
```

#### Bar Charts - Proper Label Positioning

```python
# ✅ CORRECT - Labels never overlap with bars
def create_bar_with_labels(value, label, color, x_pos, max_val, max_height):
    height = (value / max_val) * max_height
    if height < 0.3:
        height = 0.3  # Minimum visible height
    
    bar = Rectangle(
        width=1.2,
        height=height,
        fill_color=color,
        fill_opacity=1,
        stroke_color=WHITE,
        stroke_width=1
    )
    bar.move_to([x_pos, -2.5 + height/2, 0])  # Anchor at bottom
    
    # Value ABOVE bar
    value_text = Text(str(value), font_size=28, weight=BOLD)
    value_text.next_to(bar, UP, buff=0.15)
    
    # Label BELOW bar
    label_text = Text(label, font_size=22)
    label_text.next_to(bar, DOWN, buff=0.15)
    
    return VGroup(bar, value_text, label_text)
```

#### Horizontal Bar Charts - Proportional Widths

```python
# ✅ CORRECT - Bar width proportional to value
max_bar_width = 8
for country, pct, color in data:
    bar_width = (pct / 100) * max_bar_width  # Proportional
    bar = Rectangle(width=bar_width, height=0.6, fill_color=color)
    bar.move_to([-3 + bar_width/2, y_pos, 0])  # Left-aligned
    
    # Fixed-position labels (won't overlap)
    country_label.move_to([-6, y_pos, 0])  # Fixed left column
    pct_label.next_to(bar, RIGHT, buff=0.2)  # Right of bar
```

### 4. Color Consistency

**Define colors once and reuse throughout:**

```python
# ✅ CORRECT - Consistent color scheme
GOLD_COLOR = "#FFD700"    # Titles, highlights
CORAL = "#E57373"         # Negative trends, warnings
TEAL_BLUE = "#4A90D9"     # Primary data
FOREST_GREEN = "#34A853"  # Positive trends
AMBER = "#F4B400"         # Secondary data

# Use same color for same data type across all charts
# e.g., South Korea = TEAL_BLUE in pie chart AND bar chart
```

### 5. Scene Structure Template

```python
class MyScene(Scene):
    def construct(self):
        # SCENE 1: Title
        title = Text("Title", font_size=48, color=GOLD)
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1)
        self.wait(0.5)  # ← CRITICAL
        
        # SCENE 1: Content
        content = Text("Content", font_size=32)
        content.move_to(ORIGIN)
        self.play(FadeIn(content), run_time=0.8)
        self.wait(1.5)  # ← Let viewer read
        
        # SCENE 1: Transition out
        self.play(FadeOut(VGroup(title, content)), run_time=0.8)
        self.wait(0.3)  # ← Clean gap before next scene
        
        # SCENE 2: Next section...
```

### 6. Common Mistakes to Avoid

| Mistake | Problem | Solution |
|---------|---------|----------|
| No `self.wait()` | Text appears cut off mid-animation | Add `self.wait(0.5)` after every `self.play()` |
| Using `Sector()` | May cause parameter conflicts | Use `AnnularSector(inner_radius=0, ...)` |
| Pie data ≠ 100% | Chart looks incomplete | Always `assert sum(data) == 100` |
| No legend on pie | Viewers can't understand colors | Always add color-coded legend |
| Labels overlap bars | Unreadable text | Use `.next_to(bar, UP/DOWN, buff=0.15)` |
| Inconsistent colors | Confusing visualization | Define color scheme upfront |
| No minimum bar height | Small values invisible | Set `height = max(height, 0.3)` |

---

## Common Animation Patterns

### Basic Shapes
- `Circle`, `Square`, `Triangle`, `Rectangle`, `Polygon`
- Set color with `color=BLUE`, fill with `fill_opacity=1`

### Transformations
- `Transform(obj1, obj2)` - morph one object into another
- `ReplacementTransform` - replace one object with another
- `FadeIn`, `FadeOut`, `GrowFromCenter`, `GrowFromEdge`

### Text and Math
- `Text("Hello")` - plain text
- `Text("Bold", weight=BOLD)` - bold text
- `MathTex(r"\int_0^1 x^2 dx")` - LaTeX math
- `Tex(r"$E = mc^2$")` - inline LaTeX

### Animation Timing
- `run_time=2` - duration in seconds
- `self.wait(1)` - pause for 1 second
- `self.play(anim1, anim2)` - play simultaneously
- `LaggedStart(*anims, lag_ratio=0.2)` - staggered animations

### Positioning
- `.to_edge(UP/DOWN/LEFT/RIGHT, buff=0.5)` - edge positioning
- `.next_to(obj, UP/DOWN/LEFT/RIGHT, buff=0.3)` - relative positioning
- `.move_to(ORIGIN)` or `.move_to([x, y, 0])` - absolute positioning
- `.align_to(obj, UP/DOWN/LEFT/RIGHT)` - alignment

### Grouping
- `VGroup(obj1, obj2, obj3)` - group objects
- `group.arrange(DOWN, buff=0.3)` - arrange vertically
- `group.arrange(RIGHT, buff=0.3)` - arrange horizontally

## Colors

Available: `RED`, `BLUE`, `GREEN`, `YELLOW`, `ORANGE`, `PURPLE`, `WHITE`, `BLACK`, `PINK`, `TEAL`, `GOLD`, `GRAY`

Hex colors: `color="#FFD700"` for custom colors

## Data Visualization Checklist

Before rendering any data visualization:

- [ ] Pie chart data sums to exactly 100%
- [ ] All charts have legends or labels
- [ ] No text overlaps with shapes
- [ ] `self.wait()` after every animation
- [ ] Consistent color scheme throughout
- [ ] Bar widths/heights proportional to values
- [ ] Minimum visible size for small values
- [ ] Title has `buff=0.5+` from content

## Example Requests

- "Create an animation of a circle transforming into a square"
- "Animate the Pythagorean theorem"
- "Show a sine wave being drawn"
- "Visualize matrix multiplication"
- "Create a pie chart showing market share"
- "Animate a bar chart comparison"
- "Create a data visualization video with multiple scenes"

### Step 2: Upload the SKILL.md file in the Claude desktop app "settings --> capabilities" and save.
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
