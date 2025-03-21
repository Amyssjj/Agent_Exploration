#!/usr/bin/env python3
"""Test script for debugging URL handling in markdown conversion."""

import sys
import json
from markdown_converter import debug_markdown_conversion

def test_with_example():
    """Run a test with an example markdown string containing URLs."""
    markdown_with_urls = '''
# Test Markdown with URLs

This is a [link to Google](https://www.google.com)

Plain URL: https://example.com

* Bullet with URL: https://github.com
* [Another link](https://www.notion.so)

```
Code block with URL: https://nodejs.org
```

> Quote with URL: https://www.python.org
    '''
    
    result = debug_markdown_conversion(markdown_with_urls)
    print(json.dumps(result, indent=2))
    
    if result["missing_urls"]:
        print("FAILED: Some URLs are missing from the converted blocks!")
        for url in result["missing_urls"]:
            print(f"  Missing: {url}")
    else:
        print("SUCCESS: All URLs were preserved in the conversion!")

def test_with_custom_markdown(markdown_content=None):
    """Run a test with a custom markdown string."""
    if not markdown_content:
        print("Please provide markdown content as an argument.")
        return
    
    result = debug_markdown_conversion(markdown_content)
    print("URLs found in markdown:", result["urls_found_in_markdown"])
    print("URLs found in blocks:", result["urls_found_in_blocks"])
    print("Missing URLs:", result["missing_urls"])
    
    if result["missing_urls"]:
        print("FAILED: Some URLs are missing from the converted blocks!")
        for url in result["missing_urls"]:
            print(f"  Missing: {url}")
    else:
        print("SUCCESS: All URLs were preserved in the conversion!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Join all arguments in case the markdown was split
        markdown_content = ' '.join(sys.argv[1:])
        test_with_custom_markdown(markdown_content)
    else:
        test_with_example()