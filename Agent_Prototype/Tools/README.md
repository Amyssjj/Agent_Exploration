# Langfun Custom Actions Library

This repository contains custom Actions for the Langfun framework that enable various capabilities for LLM-powered agents.

## Available Actions

### 1. FileSystemAction

A unified action for file system operations that allows your agents to:
- Read and write files
- List directory contents
- Delete files/directories
- Copy and move files/directories
- Create directories
- Get file/directory information

### 2. SearchAction

A unified action for web search and browsing operations that enables:
- Google search results retrieval
- Web page content retrieval
- Text extraction from web pages
- Link extraction from web pages

## Installation

Ensure you have the required dependencies:

```bash
pip install langfun beautifulsoup4 requests pyglove
```

## Usage Examples

### FileSystemAction Example

```python
import langfun as lf
from FileSystem import FileSystemAction

# Create a model
model = lf.llms.OpenAI(model="gpt-4")

# Read a file
read_action = FileSystemAction(
    operation="read",
    source_path="/path/to/file.txt"
)
file_content = read_action(lm=model)

# Write to a file
write_action = FileSystemAction(
    operation="write",
    source_path="/path/to/output.txt",
    content="Hello, world!"
)
success = write_action(lm=model)
```

### SearchAction Example

```python
import langfun as lf
from SearchAction import SearchAction

# Create a model
model = lf.llms.OpenAI(model="gpt-4")

# Perform a Google search
search_action = SearchAction(
    operation="google_search",
    query="langfun python framework",
    num_results=5
)
search_results = search_action(lm=model)

# Extract text from a webpage
extract_action = SearchAction(
    operation="extract_text",
    url="https://example.com"
)
text_content = extract_action(lm=model)
```

## Testing

Run the unit tests to verify functionality:

```bash
python -m unittest test_search.py
```

## Development

To create your own custom Langfun Action, follow the guidelines in the `FileSystemAction_Guide.md` file for best practices and implementation details.

## License

Apache License 2.0