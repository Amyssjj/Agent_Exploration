#!/usr/bin/env python3
"""Test script for link handling in markdown to Notion conversion."""

import sys
import json
import os

# Add parent directory to path to allow importing the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib.util
spec = importlib.util.spec_from_file_location("markdown_converter", 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "markdown_converter.py"))
markdown_converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(markdown_converter)

# Use the function directly from the module
clean_markdown_to_notion_blocks = markdown_converter.clean_markdown_to_notion_blocks

def test_markdown_with_links():
    """Test markdown conversion with links."""
    # Test markdown with different link formats, including a code block
    markdown = """
# Trip Planning Guide

## Destinations

* [Visit Amsterdam](https://www.amsterdam.com)
* [Explore Rotterdam](https://www.rotterdam.nl)

## Transportation

Check train schedules at https://www.ns.nl

## Accommodations

For hotels, visit [Booking.com](https://www.booking.com)

## Weather

Check the [weather forecast](https://www.weather.com) before your trip.

## Developer Notes

```
API endpoint: https://nodejs.org/api/
This URL should be preserved as text, not made into a link.
```

Plain URL outside code: https://github.com/example
"""
    
    print("Input markdown:")
    print(markdown)
    print("\n------------------------------------\n")
    
    # Convert using our enhanced approach
    blocks = clean_markdown_to_notion_blocks(markdown)
    
    # Extract all links from the result
    links_found = []
    
    def extract_links(obj):
        """Extract URLs from Notion blocks structure."""
        if isinstance(obj, dict):
            # Check if this is a text object with a link
            if "text" in obj and isinstance(obj["text"], dict):
                if "link" in obj["text"] and isinstance(obj["text"]["link"], dict):
                    if "url" in obj["text"]["link"]:
                        links_found.append(obj["text"]["link"]["url"])
            
            # Special case for rich_text arrays
            if "rich_text" in obj and isinstance(obj["rich_text"], list):
                for rt_item in obj["rich_text"]:
                    extract_links(rt_item)
            
            # Recursively process all other dict values
            for key, value in obj.items():
                if key != "rich_text" and isinstance(value, (dict, list)):  # Skip rich_text we already processed
                    extract_links(value)
        
        elif isinstance(obj, list):
            for item in obj:
                extract_links(item)
    
    # Extract links from blocks
    extract_links(blocks)
    
    # Print the first couple of blocks for debugging
    print("\nDEBUG - First blocks structure:")
    if blocks and len(blocks) > 0:
        json_output = json.dumps(blocks[0], indent=2)
        print(json_output[:1000] + "..." if len(json_output) > 1000 else json_output)
    
    print("Links found in converted blocks:")
    for link in links_found:
        print(f"- {link}")
    
    expected_links = [
        "https://www.amsterdam.com",
        "https://www.rotterdam.nl",
        "https://www.ns.nl",
        "https://www.booking.com",
        "https://www.weather.com",
        "https://github.com/example"
        # Note: https://nodejs.org/api/ should NOT be converted to a link since it's in a code block
    ]
    
    missing_links = [link for link in expected_links if link not in links_found]
    
    if missing_links:
        print("\nMISSING LINKS:")
        for link in missing_links:
            print(f"- {link}")
        print("\nTest FAILED: Not all links were preserved!")
    else:
        print("\nTest PASSED: All links were successfully preserved!")
    
    # Print sample block structure
    print("\nSample block structure (first block):")
    print(json.dumps(blocks[0], indent=2))

if __name__ == "__main__":
    test_markdown_with_links()