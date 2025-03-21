#!/usr/bin/env python3
import json
import re
import sys

def clean_notebook(file_path):
    # Read the notebook file
    with open(file_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Define patterns to search for API keys
    api_key_patterns = [
        r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
        r'sk-ant-api[a-zA-Z0-9_-]{70,}',  # Anthropic API keys
        r'AIza[a-zA-Z0-9_-]{35}',  # Google API keys
        r'secret_[a-zA-Z0-9]{24}',  # Notion API keys
    ]
    
    # Function to replace API keys with placeholders
    def replace_api_keys(text):
        if not isinstance(text, str):
            return text
        
        for pattern in api_key_patterns:
            text = re.sub(pattern, '[API_KEY_REMOVED]', text)
        return text
    
    # Process all cells
    for cell in notebook['cells']:
        # Clean source code
        if 'source' in cell:
            cell['source'] = [replace_api_keys(line) for line in cell['source']]
        
        # Clean outputs
        if 'outputs' in cell:
            for output in cell['outputs']:
                if 'text' in output:
                    output['text'] = [replace_api_keys(line) for line in output['text']]
                if 'data' in output:
                    for mime_type, content in output['data'].items():
                        if isinstance(content, str):
                            output['data'][mime_type] = replace_api_keys(content)
                        elif isinstance(content, list):
                            output['data'][mime_type] = [replace_api_keys(item) if isinstance(item, str) else item for item in content]
    
    # Write the cleaned notebook
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)
    
    print(f"Cleaned {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        clean_notebook(sys.argv[1])
    else:
        clean_notebook("Agents/MultiAgent_TripPlanner.ipynb")