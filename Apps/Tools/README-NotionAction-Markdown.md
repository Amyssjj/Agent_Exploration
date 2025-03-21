# NotionAction Enhanced Markdown Support

The NotionAction class now includes improved markdown support using the [@tryfabric/martian](https://github.com/tryfabric/martian) package. This enhancement provides better conversion of Markdown content to Notion blocks, supporting a wide range of markdown elements including:

- All inline elements (italics, bold, strikethrough, inline code, hyperlinks, equations)
- Lists (ordered, unordered, checkboxes) - to any level of depth
- All headers (header levels >= 3 are treated as header level 3)
- Code blocks, with language highlighting support
- Block quotes
- Tables
- Equations
- Images (with URL validation)

## Setup Instructions

1. Make sure you have Node.js installed on your system
2. Install the required package:

```bash
npm install @tryfabric/martian
```

3. The NotionAction class now automatically attempts to use the @tryfabric/martian package when converting markdown content to Notion blocks.

## Usage Example

```python
import langfun as lf
from langfun.core.agentic import action as action_lib
from NotionAction import NotionAction

# Create a session
session = action_lib.Session()

# Example: Create a page with markdown content
markdown_content = """
# My New Page

This is a paragraph with **bold** and *italic* text.

## A Section

- Bullet point 1
- Bullet point 2
  - Nested bullet point

1. Numbered item 1
2. Numbered item 2

```python
# This is a code block
def hello_world():
    print("Hello, world!")
```

> This is a block quote

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

"""

create_page_action = NotionAction(
    operation="create_page",
    url="https://www.notion.so/your-workspace-page-id",  # Replace with your workspace URL
    parent_type="page",
    markdown_content=markdown_content
)

result = create_page_action(session=session)
print(f"Created page: {result.get('url')}")
```

## How It Works

1. When markdown content is provided, the NotionAction first attempts to convert it using the @tryfabric/martian Node.js package.
2. If the Node.js bridge is not available or fails, it automatically falls back to the original BeautifulSoup-based conversion method.
3. The converted markdown becomes Notion API blocks that preserve rich formatting.

## Benefits Over Previous Implementation

- More complete support for markdown elements
- Better handling of nested structures like lists
- Improved support for tables and code blocks
- Proper handling of checkbox lists
- Better alignment with Notion's native formatting

## Requirements

- Python requirements: `notion-client`, `requests`, `markdown`, `beautifulsoup4`
- Node.js requirements: `@tryfabric/martian`