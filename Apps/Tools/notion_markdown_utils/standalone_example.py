#!/usr/bin/env python3
"""
Standalone example of converting markdown to Notion blocks with proper URL handling.
"""

import os
import sys
import json
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

def main():
    # Example markdown with links
    markdown = """
# Test Document

## Links

This is a [link to Google](https://www.google.com)

Plain URL: https://example.com
    """
    
    print("Input markdown:")
    print(markdown)
    
    # Convert to Notion blocks
    blocks = convert_markdown_to_notion(markdown)
    
    # Print the result
    print("\nConverted to Notion blocks:")
    print(json.dumps(blocks, indent=2))
    
    # Extract and print links
    links = []
    
    def extract_links(obj):
        if isinstance(obj, dict):
            if "text" in obj and isinstance(obj["text"], dict) and "link" in obj["text"]:
                links.append(obj["text"]["link"].get("url", ""))
            
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    extract_links(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_links(item)
    
    extract_links(blocks)
    
    print("\nLinks found:")
    for link in links:
        print(f"- {link}")

if __name__ == "__main__":
    main()