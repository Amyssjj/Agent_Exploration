# Notion Markdown Utilities

This package provides enhanced Markdown to Notion conversion capabilities using the [@tryfabric/martian](https://github.com/tryfabric/martian) Node.js package. It's designed to work with the NotionAction class in Langfun Agents, with special handling for URLs and links in all contexts (including tables).

## Features

Improved markdown support for:

- All inline elements (italics, bold, strikethrough, inline code, hyperlinks, equations)
- Lists (ordered, unordered, checkboxes) - to any level of depth
- All headers (header levels >= 3 are treated as header level 3)
- Code blocks, with language highlighting support
- Block quotes
- Tables (with proper URL handling)
- Equations
- Images (with URL validation)
- URLs in all contexts (including tables and plain text)

## Installation

1. Ensure Node.js and npm are installed on your system
2. Run the setup script in this directory:

```bash
./setup.sh
```

This will install the required Node.js packages and make the JavaScript bridge executable.

## Usage

### Standalone Usage

```python
from notion_markdown_utils import markdown_to_notion_blocks

markdown_content = """
# My heading

This is a paragraph with **bold text** and *italic text*.

## URL Examples
- Regular link: [Google](https://www.google.com)
- Plain URL: https://example.com

| Item | Link |
|------|------|
| Search | [Google](https://www.google.com) |
| Example | https://example.com |
"""

# Convert markdown to Notion blocks
blocks = markdown_to_notion_blocks(markdown_content)

# Now you can use these blocks with the Notion API
```

### Integration with NotionAction

The NotionAction class will automatically use this package if it's available in the Python path. 
Simply place the `notion_markdown_utils` directory alongside NotionAction.py, or ensure it's 
in your Python path.

```python
import langfun as lf
from langfun.core.agentic import action as action_lib
from NotionAction import NotionAction

# Create a session
session = action_lib.Session()

# Create a page with markdown content including URLs and tables
action = NotionAction(
    operation="create_page",
    url="https://www.notion.so/your-workspace-page-id",  # Your workspace URL
    parent_type="page",
    markdown_content="""
    # Trip Planner
    
    ## Key Information
    
    | Location | Website |
    |----------|---------|
    | Amsterdam | [Visit Amsterdam](https://www.amsterdam.com) |
    | Rotterdam | https://www.rotterdam.nl |
    
    Check more details at https://example.com/travel
    """
)

result = action(session=session)

# The action now returns useful information about the created page
if not result.get("error"):
    # Access the success message
    print(result.get("success_message"))
    # Outputs something like:
    # Successfully created Notion page: 'Trip Planner'
    # View your page at: https://www.notion.so/abcdef123456789...
    
    # You can also access individual components
    print(f"Page title: {result.get('page_title')}")
    print(f"Direct URL: {result.get('page_url')}")
else:
    print(f"Error: {result.get('error')}")
```

## How It Works

1. The package provides a Python interface to interact with the @tryfabric/martian Node.js package
2. When converting markdown, it uses a file-based approach to preserve all formatting, especially URLs
3. There are multiple fallback mechanisms to ensure reliability

## Advanced Usage

You can use the `MarkdownConverter` class directly for more control:

```python
from notion_markdown_utils import MarkdownConverter

converter = MarkdownConverter(use_martian=True)  # Set to False to force the fallback method
blocks = converter.convert(markdown_content)
```

### Debugging URL Issues

If you're having trouble with URLs in your markdown content, you can use the debug feature:

```python
# When using NotionAction
action = NotionAction(
    operation="create_page",
    url="https://www.notion.so/your-workspace-page-id",
    parent_type="page",
    markdown_content="Your markdown with [links](https://example.com)",
    debug_markdown=True  # Enable debugging output
)

# Or directly with the converter
from notion_markdown_utils import markdown_to_notion_blocks
blocks = markdown_to_notion_blocks(markdown_content, debug=True)
```

There's also a specialized test script to help diagnose URL issues in tables:

```bash
# Test URL handling in tables
./table_test.py
```

## Requirements

- Python: Requires `json`, `os`, `shlex`, `subprocess`, `tempfile` (standard library)  
- Node.js: Requires `@tryfabric/martian` (installed by setup.sh)
- Optional fallback: `markdown`, `beautifulsoup4` (only needed if Node.js bridge fails)