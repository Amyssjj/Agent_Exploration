#!/usr/bin/env python3
"""Debug script for troubleshooting pyglove List URL conversion issues."""

import os
import sys
import json
import traceback
from typing import List, Dict, Any

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a mock pyglove-like List class for testing
class MockPygloveList(list):
    def __init__(self, items):
        super().__init__(items)
    
    def to_json(self):
        return '\n'.join(self)
    
    def __str__(self):
        return '\n'.join([str(item) for item in self])

# Create a test list with table containing URLs
test_list = MockPygloveList([
    '# Test with pyglove List',
    '',
    '## Table with Links',
    '',
    '| Item | Link |',
    '|------|------|',
    '| Google | [Google](https://www.google.com) |',
    '| Example | https://example.com |',
    '| Direct | <https://direct.link> |',
    '',
    '## Other Links',
    '',
    '* Regular link: [GitHub](https://github.com)',
    '* Plain URL: https://python.org',
])

print("=== Input test content ===")
print(str(test_list))
print("\n=== End of input ===\n")

def print_json(obj, indent=2):
    """Print object as formatted JSON."""
    print(json.dumps(obj, indent=indent))

print("Step 1: Importing modules...")
try:
    # Import converter modules
    from notion_markdown_utils.markdown_converter import (
        markdown_to_notion_blocks,
        clean_markdown_to_notion_blocks,
        debug_markdown_conversion
    )
    print("✅ Modules imported successfully")
except Exception as e:
    print(f"❌ Error importing modules: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Testing str() conversion...")
try:
    str_content = str(test_list)
    print(f"✅ String conversion successful, length: {len(str_content)}")
except Exception as e:
    print(f"❌ Error converting to string: {e}")
    traceback.print_exc()

print("\nStep 3: Using debug_markdown_conversion...")
try:
    debug_info = debug_markdown_conversion(test_list)
    
    print("URLs found in markdown:")
    for url in debug_info["urls_found_in_markdown"]:
        print(f"  - {url}")
    
    print("\nURLs found in blocks:")
    for url in debug_info["urls_found_in_blocks"]:
        print(f"  - {url}")
    
    print("\nMissing URLs:")
    for url in debug_info["missing_urls"]:
        print(f"  - {url}")
    
    print("✅ Debug conversion successful")
except Exception as e:
    print(f"❌ Error in debug_markdown_conversion: {e}")
    traceback.print_exc()

print("\nStep 4: Using clean_markdown_to_notion_blocks...")
try:
    # Convert directly
    blocks = clean_markdown_to_notion_blocks(test_list)
    
    print(f"✅ Conversion successful, got {len(blocks)} blocks")
    
    # Extract and count links
    links_found = []
    
    def extract_links(obj):
        if isinstance(obj, dict):
            if "text" in obj and isinstance(obj["text"], dict) and "link" in obj["text"]:
                link_url = obj["text"]["link"].get("url", "")
                link_content = obj["text"].get("content", "")
                if link_url:
                    links_found.append((link_url, link_content))
            
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    extract_links(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_links(item)
    
    extract_links(blocks)
    
    print(f"\nFound {len(links_found)} links in converted blocks:")
    for url, text in links_found:
        print(f"  - {url} (text: '{text}')")
    
    # Print the first few blocks to see structure
    print("\nFirst block structure:")
    if blocks and len(blocks) > 0:
        print_json(blocks[0])
    
    # Print the table block if it exists
    print("\nLooking for table block...")
    table_block = None
    for block in blocks:
        if block.get("type") == "table":
            table_block = block
            break
    
    if table_block:
        print("✅ Found table block")
        # Print first table row to see how cells are structured
        if "children" in table_block.get("table", {}) and len(table_block["table"]["children"]) > 1:
            # Skip header row, show first data row
            print("\nFirst data row structure:")
            print_json(table_block["table"]["children"][1])
    else:
        print("❌ No table block found in output")
    
except Exception as e:
    print(f"❌ Error in clean_markdown_to_notion_blocks: {e}")
    traceback.print_exc()

print("\n=== CONVERSION COMPLETE ===")