#!/usr/bin/env python3
"""Special handling for links in markdown content."""

import re
from typing import List, Dict, Any, Tuple

def preprocess_markdown_links(markdown_content: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Preprocess markdown to extract and replace links with placeholders.
    
    Args:
        markdown_content: The original markdown content
        
    Returns:
        Tuple of (processed_markdown, extracted_links)
    """
    extracted_links = []
    
    # Function to replace markdown link with placeholder
    def replace_markdown_link(match):
        link_text = match.group(1)
        link_url = match.group(2)
        
        # Generate a unique placeholder
        placeholder = f"LINKPLACEHOLDER_{len(extracted_links)}"
        
        # Store the link info
        extracted_links.append({
            "placeholder": placeholder,
            "text": link_text,
            "url": link_url
        })
        
        # Return the placeholder text with brackets to keep it recognizable
        return f"[{placeholder}]"
    
    # Function to replace bare URL with placeholder
    def replace_bare_url(match):
        url = match.group(0)
        
        # Skip URLs that are part of markdown links (already handled)
        prev_chars = markdown_content[max(0, match.start() - 2):match.start()]
        if prev_chars.endswith("]("):
            return url
            
        # Generate a unique placeholder
        placeholder = f"URLLINKPLACEHOLDER_{len(extracted_links)}"
        
        # Store the link info
        extracted_links.append({
            "placeholder": placeholder,
            "text": url,
            "url": url
        })
        
        return placeholder
    
    # First, handle markdown-style links: [text](url)
    processed_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_markdown_link, markdown_content)
    
    # Next, handle bare URLs (but not inside code blocks)
    lines = processed_content.split('\n')
    in_code_block = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
            
        if not in_code_block:
            # Only process lines not in code blocks
            lines[i] = re.sub(r'https?://[^\s)"\'\]\}]+', replace_bare_url, line)
    
    processed_content = '\n'.join(lines)
    
    return processed_content, extracted_links

def postprocess_notion_blocks(blocks: List[Dict[str, Any]], extracted_links: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Post-process Notion blocks to restore links from placeholders.
    
    Args:
        blocks: The Notion blocks with placeholder text
        extracted_links: The extracted links from preprocessing
        
    Returns:
        Updated Notion blocks with proper links
    """
    if not extracted_links:
        return blocks  # No links to process
    
    # Create a lookup of placeholders to link data
    link_lookup = {link["placeholder"]: link for link in extracted_links}
    
    # Helper function to recursively process blocks
    def process_block(block):
        if isinstance(block, dict):
            # Check for table structures first
            if block.get("type") == "table" and "table" in block:
                # Process table children
                if "children" in block["table"] and isinstance(block["table"]["children"], list):
                    for i, row in enumerate(block["table"]["children"]):
                        if isinstance(row, dict) and "table_row" in row:
                            # Process cells in the row
                            if "cells" in row["table_row"] and isinstance(row["table_row"]["cells"], list):
                                for j, cell in enumerate(row["table_row"]["cells"]):
                                    if isinstance(cell, list):
                                        row["table_row"]["cells"][j] = [process_block(text_item) for text_item in cell]
            
            # Check all text content fields
            if "text" in block and isinstance(block["text"], dict) and "content" in block["text"]:
                content = block["text"]["content"]
                
                # Check if content contains any of our placeholders
                for placeholder, link_data in link_lookup.items():
                    if placeholder in content:
                        # Replace the content with the actual text
                        block["text"]["content"] = link_data["text"]
                        # Add the link
                        block["text"]["link"] = {"url": link_data["url"]}
                        # Early return since we've processed this block
                        return block
                
                # Also check for bracketed placeholders
                for placeholder, link_data in link_lookup.items():
                    bracketed = f"[{placeholder}]"
                    if bracketed in content:
                        block["text"]["content"] = link_data["text"]
                        block["text"]["link"] = {"url": link_data["url"]}
                        return block
            
            # Recursively process all dict values
            for key, value in list(block.items()):
                if isinstance(value, (dict, list)):
                    block[key] = process_block(value)
        
        elif isinstance(block, list):
            # Process each item in the list
            for i, item in enumerate(block):
                block[i] = process_block(item)
        
        return block
    
    # Process all blocks
    updated_blocks = process_block(blocks)
    
    return updated_blocks

def fix_markdown_links(markdown_content: str, converter_func) -> List[Dict[str, Any]]:
    """
    Process markdown with special handling for links.
    
    Args:
        markdown_content: Original markdown content
        converter_func: Function to convert markdown to Notion blocks
        
    Returns:
        Notion blocks with properly formatted links
    """
    # First, preprocess to extract links
    processed_content, extracted_links = preprocess_markdown_links(markdown_content)
    
    # Convert processed content to Notion blocks
    blocks = converter_func(processed_content)
    
    # Post-process to restore links
    if extracted_links:
        blocks = postprocess_notion_blocks(blocks, extracted_links)
    
    return blocks