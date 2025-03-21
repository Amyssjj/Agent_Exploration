"""Test script for NotionAction with bold links."""

import langfun as lf
from langfun.core.agentic import action as action_lib
from NotionAction import NotionAction

def main():
    """Run a simple test of NotionAction with bold links."""
    # Create a model
    model = lf.llms.OpenAI(model="gpt-4")
    
    # Create a session
    session = action_lib.Session()
    
    # Test markdown with bold links and normal links
    markdown_content = """# Testing Bold Links in Notion

This is a paragraph with a [normal link](https://example.com).

This is a paragraph with a **[bold link](https://example.com/bold)**.

This is a paragraph with *[italic link](https://example.com/italic)*.

This is a paragraph with ***[bold italic link](https://example.com/bold-italic)***.

## Links in Lists

* [Normal list link](https://example.com/list)
* **[Bold list link](https://example.com/bold-list)**
* *[Italic list link](https://example.com/italic-list)*

## Links in Table

| Type | Link |
|------|------|
| Normal | [Table link](https://example.com/table) |
| Bold | **[Bold table link](https://example.com/bold-table)** |
| Italic | *[Italic table link](https://example.com/italic-table)* |
"""

    # Create NotionAction with markdown content
    action = NotionAction(
        operation="create_page",
        parent_type="page",  # Set this to match your Notion environment
        parent_id="your_parent_page_id",  # Replace with an actual page ID when testing
        markdown_content=markdown_content,
        debug_markdown=True  # Enable debugging output
    )
    
    # Instead of actually creating the page, just get the blocks for testing
    blocks = action._markdown_to_notion_blocks(markdown_content)
    
    # Print the blocks
    print("\n--- NOTION BLOCKS ---\n")
    
    # Helper function to inspect blocks for links
    def inspect_blocks_for_links(blocks, indent=0):
        for block in blocks:
            if isinstance(block, dict):
                block_type = block.get("type", "unknown")
                print(f"{' ' * indent}Block type: {block_type}")
                
                # Check if this block has rich_text
                rich_text = None
                if block_type in block:
                    rich_text = block[block_type].get("rich_text", [])
                
                if rich_text:
                    print(f"{' ' * (indent + 2)}Rich text:")
                    for text in rich_text:
                        content = text.get("text", {}).get("content", "")
                        link = text.get("text", {}).get("link", {})
                        annotations = text.get("annotations", {})
                        
                        print(f"{' ' * (indent + 4)}Content: {content}")
                        if link:
                            print(f"{' ' * (indent + 4)}Link: {link.get('url', '')}")
                        
                        if annotations:
                            print(f"{' ' * (indent + 4)}Annotations: {annotations}")
                            
                # Check for table
                if block_type == "table" and "table" in block:
                    print(f"{' ' * (indent + 2)}Table with {len(block['table'].get('children', []))} rows")
                    for row in block['table'].get('children', []):
                        if "table_row" in row:
                            for i, cell in enumerate(row["table_row"].get("cells", [])):
                                print(f"{' ' * (indent + 4)}Cell {i+1}:")
                                for text in cell:
                                    content = text.get("text", {}).get("content", "")
                                    link = text.get("text", {}).get("link", {})
                                    annotations = text.get("annotations", {})
                                    
                                    print(f"{' ' * (indent + 6)}Content: {content}")
                                    if link:
                                        print(f"{' ' * (indent + 6)}Link: {link.get('url', '')}")
                                    
                                    if annotations:
                                        print(f"{' ' * (indent + 6)}Annotations: {annotations}")
    
    # Inspect the blocks
    inspect_blocks_for_links(blocks)
    
    print("\nTest completed. Check the output above to verify bold links are preserved.")

if __name__ == "__main__":
    main()