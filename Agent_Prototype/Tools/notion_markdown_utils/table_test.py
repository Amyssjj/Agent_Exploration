#!/usr/bin/env python3
"""Test script specifically for handling URLs in tables."""

import os
import json
import sys
import subprocess
import tempfile
import shlex

def convert_markdown_to_notion(markdown_content):
    """
    Convert markdown to Notion blocks with direct method.
    """
    # Path to the Node.js bridge script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'markdown_to_notion.js')
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return []
    
    # Create a temporary file with the markdown content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp:
        temp.write(markdown_content)
        temp_file = temp.name
    
    try:
        # Create the command with file argument
        file_arg = f"--file={temp_file}"
        cmd = f"node {script_path} {shlex.quote(file_arg)}"
        
        # Run the command
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Error executing Node.js script: {result.stderr}")
            return []
        
        # Parse the output
        return json.loads(result.stdout)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def extract_links_from_blocks(blocks):
    """Extract all links from Notion blocks."""
    links = []
    
    def extract_recursively(obj):
        if isinstance(obj, dict):
            # Check if it's a text object with a link
            if "text" in obj and isinstance(obj["text"], dict) and "link" in obj["text"]:
                link_url = obj["text"]["link"].get("url", "")
                if link_url:
                    links.append(link_url)
            
            # Process all values
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    extract_recursively(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_recursively(item)
    
    extract_recursively(blocks)
    return links

def main():
    # Example markdown with table containing links
    markdown = """
# Table with Links

| Destination | Website |
|-------------|---------|
| Amsterdam | [Visit Amsterdam](https://www.amsterdam.com) |
| Rotterdam | https://www.rotterdam.nl |
| Booking | [Booking.com](https://www.booking.com) |
"""
    
    print("Input markdown:")
    print(markdown)
    
    # Convert to Notion blocks
    blocks = convert_markdown_to_notion(markdown)
    
    # Print the result structure (first few blocks)
    print("\nConverted structure (excerpt):")
    if blocks:
        if len(json.dumps(blocks)) > 1000:
            print(json.dumps(blocks[:2], indent=2))
        else:
            print(json.dumps(blocks, indent=2))
    
    # Extract and print links
    links = extract_links_from_blocks(blocks)
    
    print("\nLinks found:")
    for link in links:
        print(f"- {link}")
    
    expected_links = [
        "https://www.amsterdam.com",
        "https://www.rotterdam.nl",
        "https://www.booking.com"
    ]
    
    # Check if all expected links were found
    missing = [link for link in expected_links if link not in links]
    if missing:
        print("\nMissing links:")
        for link in missing:
            print(f"- {link}")
        print("\nTest FAILED: Some links are missing!")
    else:
        print("\nTest PASSED: All links were preserved!")

if __name__ == "__main__":
    main()