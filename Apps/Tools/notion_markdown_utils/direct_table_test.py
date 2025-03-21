#!/usr/bin/env python3
"""Direct test for table links using NotionAction."""

import os
import sys
import json
import tempfile
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import NotionAction (this is just a check, we don't use it for conversion)
    try:
        from NotionAction import NotionAction
        print("NotionAction imported successfully.")
    except ImportError:
        print("Note: NotionAction not found in path.")

    # Import the conversion function
    from notion_markdown_utils.markdown_converter import clean_markdown_to_notion_blocks

    # Test markdown with a table containing links
    test_markdown = """
# Table Test

| Item | Link |
|------|------|
| Google | [Google](https://www.google.com) |
| Example | https://example.com |
"""

    print("Converting markdown table with links...")
    # Convert the markdown
    blocks = clean_markdown_to_notion_blocks(test_markdown)

    # Extract links
    links = []
    def extract_links(obj):
        if isinstance(obj, dict):
            # Check for text with link
            if "text" in obj and isinstance(obj["text"], dict) and "link" in obj["text"]:
                link_url = obj["text"]["link"].get("url", "")
                if link_url:
                    links.append(link_url)
            
            # Check all dictionary values
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    extract_links(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_links(item)

    # Find links in blocks
    extract_links(blocks)
    
    # Print the results
    print("\nMarkdown:")
    print(test_markdown)
    
    print("\nConverted blocks (excerpt):")
    if blocks:
        print(json.dumps(blocks[0], indent=2))
        
    print("\nAll links found:")
    for link in links:
        print(f"- {link}")
        
    # Check if expected links are present
    expected_links = ["https://www.google.com", "https://example.com"]
    missing = [link for link in expected_links if link not in links]
    
    if missing:
        print("\nMISSING LINKS:")
        for link in missing:
            print(f"- {link}")
        print("\nTest FAILED")
    else:
        print("\nTest PASSED - All expected links were found!")

except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()