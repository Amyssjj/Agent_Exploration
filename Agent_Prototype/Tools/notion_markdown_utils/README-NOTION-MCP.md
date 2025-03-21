# Notion MCP - Model Context Protocol Server for Notion Integration

This MCP (Model Context Protocol) server provides integration with Notion workspaces, allowing Claude and other MCP-compatible LLM clients to interact with Notion pages and databases.

## Features

- Create, read, and update Notion pages with rich markdown formatting
- Query Notion databases with filtering and sorting
- Search across your Notion workspace
- Get database schemas and metadata
- Create new databases with custom properties
- List users in your workspace

## Requirements

- Python 3.9+
- NotionAction.py and associated files
- Notion API token (from a Notion integration)
- Required libraries:
  - notion-client
  - requests
  - markdown
  - beautifulsoup4
  - mcp

## Installation

### 1. Set up Environment

```bash
# Create and activate a virtual environment
python -m venv notion_mcp_env
source notion_mcp_env/bin/activate  # On Windows: notion_mcp_env\Scripts\activate

# Install dependencies
pip install mcp
pip install notion-client requests markdown beautifulsoup4
```

### 2. Set up Notion Integration

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Give your integration a name and select the capabilities it needs
3. Copy the token provided by Notion
4. Share the specific pages or databases with your integration in Notion

### 3. Set Environment Variable

```bash
# On Unix/Mac
export NOTION_API_TOKEN=your_integration_token_here

# On Windows (Command Prompt)
set NOTION_API_TOKEN=your_integration_token_here

# On Windows (PowerShell)
$env:NOTION_API_TOKEN = "your_integration_token_here"
```

## Usage

### Testing with MCP Developer Tools

You can test the Notion MCP server using the MCP developer tools:

```bash
# Run the server in development mode
mcp dev notion_mcp.py
```

This will launch the MCP Inspector interface where you can test tools and resources.

### Installing in Claude Desktop

To use the Notion MCP with Claude Desktop:

```bash
# Install the MCP server in Claude Desktop
mcp install notion_mcp.py --name "Notion Helper"

# With environment variables
mcp install notion_mcp.py --name "Notion Helper" -v NOTION_API_TOKEN=your_token_here
```

### Available Tools

The Notion MCP provides the following tools:

- `create_page`: Create a new Notion page with markdown content
- `update_page`: Update an existing Notion page
- `read_page`: Read a Notion page and its content
- `get_page_info`: Get basic information about a page
- `query_database`: Query a Notion database with filters and sorting
- `get_database_info`: Get information about a database's schema
- `create_database`: Create a new database with custom properties
- `search_notion`: Search across your Notion workspace
- `list_users`: List all users in your workspace

### Available Resources

The Notion MCP provides the following resources:

- `notion://markdown/examples`: Examples of markdown formatting supported by Notion
- `notion://api/examples`: Examples of Notion API filter and sort syntax
- `notion://help`: Help information about using the Notion MCP

## Example Interactions

Here are some example prompts you can use with Claude once the Notion MCP is installed:

**Creating a page:**
"Create a new Notion page with a todo list for my project"

**Querying a database:**
"Find all tasks in my Projects database with a status of 'In Progress'"

**Updating content:**
"Update my meeting notes page with the action items we discussed"

**Searching:**
"Find all Notion pages related to marketing strategy"

## Troubleshooting

If you encounter issues:

1. **API Token**: Ensure your Notion API token is correctly set and has the necessary permissions
2. **Page Access**: Make sure you've shared the pages/databases with your integration in Notion
3. **Logs**: Check the MCP server logs for detailed error messages
4. **Formatting**: If markdown isn't rendering correctly, check the formatting using the examples resource

## License

This project is licensed under the terms of the MIT license.