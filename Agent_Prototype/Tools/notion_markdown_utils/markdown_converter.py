"""Markdown to Notion Blocks Converter.

This module provides functionality to convert Markdown content to Notion API
blocks with rich formatting, using either the @tryfabric/martian Node.js package
or a fallback BeautifulSoup-based approach.
"""

import os
import json
import shlex
import subprocess
import re
import tempfile
from typing import Any, Dict, List, Optional, Tuple

# Import the link handler
try:
    from .link_handler import preprocess_markdown_links, postprocess_notion_blocks
    LINK_HANDLER_AVAILABLE = True
except ImportError:
    LINK_HANDLER_AVAILABLE = False

try:
    import markdown
    from bs4 import BeautifulSoup
    MARKDOWN_LIBS_AVAILABLE = True
except ImportError:
    MARKDOWN_LIBS_AVAILABLE = False


class MarkdownConverter:
    """Converter for Markdown to Notion blocks.
    
    This class provides methods to convert Markdown content to Notion API blocks,
    prioritizing the use of @tryfabric/martian when available, with a fallback
    to a BeautifulSoup-based approach.
    """
    
    def __init__(self, use_martian: bool = True):
        """Initialize the converter.
        
        Args:
            use_martian: Whether to attempt to use @tryfabric/martian (default: True)
        """
        self.use_martian = use_martian
        
    def convert(self, md_content) -> List[Dict[str, Any]]:
        """Convert markdown content to Notion blocks with rich formatting.
        
        Args:
            md_content: Markdown content (can be str or pyglove.List)
            
        Returns:
            List of Notion block objects
        """
        # Handle pyglove List objects
        if hasattr(md_content, '__class__') and md_content.__class__.__name__ == 'List':
            try:
                # Try to convert to string
                md_content = str(md_content)
            except Exception as e:
                print(f"Error converting pyglove List to string: {e}")
                # Try using the to_json method if available
                if hasattr(md_content, 'to_json'):
                    md_content = md_content.to_json()
                else:
                    # Try a different approach
                    md_content = '\n'.join([str(item) for item in md_content])
        
        if not md_content:
            return []
            
        # Try to use @tryfabric/martian if enabled
        if self.use_martian:
            try:
                blocks = self._convert_with_martian(md_content)
                if blocks:
                    return blocks
            except Exception as e:
                print(f"Error using @tryfabric/martian: {str(e)}")
                print("Falling back to BeautifulSoup markdown conversion")
        
        # Fallback to BeautifulSoup approach
        return self._convert_with_bs4(md_content)
    
    def _convert_with_martian(self, md_content) -> List[Dict[str, Any]]:
        """Convert markdown using @tryfabric/martian Node.js package.
        
        Args:
            md_content: Markdown content (can be str or pyglove.List)
            
        Returns:
            List of Notion blocks, or empty list if conversion failed
        """
        # Ensure we have a string to work with
        if not isinstance(md_content, str):
            try:
                # Try to convert to string
                md_content_str = str(md_content)
                
                # Special handling for list-like objects (including pyglove.List)
                if hasattr(md_content, '__iter__') and not md_content_str.strip():
                    # If str() didn't produce useful content, try joining the items
                    md_content = '\n'.join([str(item) for item in md_content])
                else:
                    md_content = md_content_str
            except Exception as e:
                print(f"Error converting object to string in _convert_with_martian: {e}")
                # Try using the to_json method if available
                if hasattr(md_content, 'to_json'):
                    try:
                        md_content = md_content.to_json()
                    except Exception as json_err:
                        print(f"Error in to_json conversion: {json_err}")
                        # Last resort
                        if hasattr(md_content, '__iter__'):
                            md_content = '\n'.join([str(item) for item in md_content])
                        else:
                            print("Unable to convert input to string format")
                            return []
        
        if not md_content:
            return []
        
        # Path to the Node.js bridge script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, 'markdown_to_notion.js')
        
        # Check if script exists
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"markdown_to_notion.js not found at {script_path}")
        
        # Write markdown content to a temporary file to preserve all characters, including URLs
        import tempfile
        
        temp_file = None
        try:
            # Create a temporary file with the markdown content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp:
                temp.write(md_content)
                temp_file = temp.name
            
            # File path argument for the Node.js script
            file_arg = f"--file={temp_file}"
            
            # Try using npx first in case @tryfabric/martian isn't globally installed
            try:
                cmd = f"npx -y @tryfabric/martian node {script_path} {shlex.quote(file_arg)}"
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30  # 30 seconds timeout
                )
                
                if result.returncode == 0:
                    # Parse the JSON output
                    return json.loads(result.stdout)
            except Exception as e:
                print(f"Failed to run with npx: {str(e)}")
            
            # Try direct node execution if npx failed
            try:
                cmd = f"node {script_path} {shlex.quote(file_arg)}"
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Parse the JSON output
                    return json.loads(result.stdout)
                else:
                    print(f"Node.js script failed: {result.stderr}")
            except Exception as e:
                print(f"Failed to run with node: {str(e)}")
            
            # If we got here, both attempts failed
            return []
            
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass  # Ignore errors when cleaning up
    
    def _convert_with_bs4(self, md_content) -> List[Dict[str, Any]]:
        """Convert markdown using BeautifulSoup.
        
        Args:
            md_content: Markdown content (can be str or pyglove.List)
            
        Returns:
            List of Notion blocks
        """
        # Ensure we have a string to work with
        if not isinstance(md_content, str):
            try:
                # Try to convert to string
                md_content_str = str(md_content)
                
                # Special handling for list-like objects (including pyglove.List)
                if hasattr(md_content, '__iter__') and not md_content_str.strip():
                    # If str() didn't produce useful content, try joining the items
                    md_content = '\n'.join([str(item) for item in md_content])
                else:
                    md_content = md_content_str
            except Exception as e:
                print(f"Error converting object to string in _convert_with_bs4: {e}")
                # Try using the to_json method if available
                if hasattr(md_content, 'to_json'):
                    try:
                        md_content = md_content.to_json()
                    except Exception as json_err:
                        print(f"Error in to_json conversion: {json_err}")
                        # Last resort
                        if hasattr(md_content, '__iter__'):
                            md_content = '\n'.join([str(item) for item in md_content])
                        else:
                            print("Unable to convert input to string format")
                            return []
        
        if not md_content or not MARKDOWN_LIBS_AVAILABLE:
            return []
            
        # Convert markdown to HTML with extensions for tables and code highlighting
        html = markdown.markdown(
            md_content,
            extensions=[
                'tables',
                'fenced_code',
                'codehilite',
                'nl2br',  # Convert newlines to <br>
                'sane_lists'  # Better list handling
            ]
        )
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Convert to Notion blocks
        blocks = []
        
        def process_rich_text_element(element) -> List[Dict[str, Any]]:
            """Process an element to extract rich text with formatting."""
            if element is None:
                return []
                
            # If it's just a string
            if isinstance(element, str):
                return [{"type": "text", "text": {"content": element}}]
                
            rich_text = []
            
            # Check if the element itself is a link
            if element.name == 'a' and element.has_attr('href'):
                # Handle the entire element as a link
                href = element['href']
                text_content = element.get_text()
                if text_content:
                    rich_text.append({
                        "type": "text",
                        "text": {
                            "content": text_content,
                            "link": {"url": href}
                        }
                    })
                return rich_text
            
            # Process the children of this element
            for child in element.children:
                # If it's a string
                if isinstance(child, str):
                    if child.strip():  # Only add non-empty strings
                        rich_text.append({
                            "type": "text",
                            "text": {"content": child}
                        })
                    continue
                    
                # Skip if not a tag
                if not hasattr(child, 'name'):
                    continue
                    
                # Skip if tag is None
                if child.name is None:
                    continue
                    
                # Special handling for links
                if child.name == 'a' and child.has_attr('href'):
                    href = child['href']
                    link_text = child.get_text()
                    if link_text:
                        # Links need special handling to ensure the URL is included
                        rich_text.append({
                            "type": "text",
                            "text": {
                                "content": link_text,
                                "link": {"url": href}
                            }
                        })
                    continue
                
                # Get the text content
                text_content = child.get_text()
                if not text_content:
                    continue
                    
                # Create appropriate text object based on tag
                text_obj = {
                    "type": "text",
                    "text": {"content": text_content}
                }
                
                # Check if this element contains a link
                link = child.find('a')
                if link and link.has_attr('href'):
                    # Add the link property to the text object
                    text_obj["text"]["link"] = {"url": link['href']}
                
                # Add annotations based on tag
                if child.name == 'strong' or child.name == 'b':
                    text_obj["annotations"] = {"bold": True}
                elif child.name == 'em' or child.name == 'i':
                    text_obj["annotations"] = {"italic": True}
                elif child.name == 'u':
                    text_obj["annotations"] = {"underline": True}
                elif child.name == 'code':
                    text_obj["annotations"] = {"code": True}
                elif child.name == 'del' or child.name == 's':
                    text_obj["annotations"] = {"strikethrough": True}
                
                rich_text.append(text_obj)
                
            return rich_text
        
        # Process elements
        for element in soup.children:
            if element.name is None:
                continue
                
            if element.name == 'h1':
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": process_rich_text_element(element)
                    }
                })
            elif element.name == 'h2':
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": process_rich_text_element(element)
                    }
                })
            elif element.name == 'h3':
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": process_rich_text_element(element)
                    }
                })
            elif element.name == 'p':
                # Skip empty paragraphs
                if not element.get_text().strip():
                    continue
                    
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": process_rich_text_element(element)
                    }
                })
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": process_rich_text_element(li)
                        }
                    })
            elif element.name == 'ol':
                for li in element.find_all('li', recursive=False):
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": process_rich_text_element(li)
                        }
                    })
            elif element.name == 'blockquote':
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": process_rich_text_element(element)
                    }
                })
            elif element.name == 'pre':
                # Extract code language if available
                language = "plain text"
                code_element = element.find('code')
                if code_element and code_element.has_attr('class'):
                    for cls in code_element['class']:
                        if cls.startswith('language-'):
                            language = cls[9:]  # Remove 'language-' prefix
                            break
                
                code_text = element.get_text()
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": code_text}
                        }],
                        "language": language
                    }
                })
            elif element.name == 'hr':
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            elif element.name == 'table':
                try:
                    # Process table
                    rows = element.find_all('tr')
                    if not rows:
                        continue
                        
                    # Determine table width from first row
                    first_row = rows[0]
                    header_cells = first_row.find_all(['th', 'td'])
                    table_width = len(header_cells)
                    
                    if table_width == 0:
                        continue  # Skip empty tables
                    
                    # First, create all table rows as individual blocks
                    table_rows = []
                    
                    # Check if first row is header
                    has_header = first_row.find('th') is not None
                    
                    # Process all rows
                    for row in rows:
                        cells = row.find_all(['th', 'td'])
                        
                        # Prepare cells for this row
                        row_cells = []
                        
                        # Each cell needs to be an array of rich_text objects
                        for cell in cells:
                            # Process cell with rich text handler instead of just text extraction
                            # This preserves links and formatting within table cells
                            rich_text = process_rich_text_element(cell)
                            row_cells.append(rich_text)
                        
                        # Make sure we have exactly table_width cells (pad with empty if needed)
                        while len(row_cells) < table_width:
                            row_cells.append([{"type": "text", "text": {"content": ""}}])
                        
                        # If we have too many cells, trim to match table_width
                        if len(row_cells) > table_width:
                            row_cells = row_cells[:table_width]
                        
                        # Add row to collection
                        table_rows.append({
                            "type": "table_row",
                            "table_row": {
                                "cells": row_cells
                            }
                        })
                    
                    # Now create the table block with all rows included
                    table_block = {
                        "object": "block",
                        "type": "table",
                        "table": {
                            "table_width": table_width,
                            "has_column_header": has_header,
                            "has_row_header": False,
                            "children": table_rows
                        }
                    }
                    
                    # Add complete table to blocks
                    blocks.append(table_block)
                    
                except Exception as e:
                    # If table processing fails, add a paragraph explaining the error
                    print(f"Error processing table: {str(e)}")
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": f"[Table could not be processed: {str(e)}]"}
                            }]
                        }
                    })
                    
                    # Also add the table content as plain text
                    text_content = element.get_text().strip()
                    if text_content:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{
                                    "type": "text",
                                    "text": {"content": text_content}
                                }]
                            }
                        })
            elif element.name == 'img' and element.has_attr('src'):
                # Try to add image
                src = element['src']
                if src.startswith(('http://', 'https://')):
                    blocks.append({
                        "object": "block",
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {
                                "url": src
                            }
                        }
                    })
            elif element.name == 'div' or element.name == 'span':
                # Recursively process div and span elements
                div_blocks = []
                for child in element.children:
                    if hasattr(child, 'name') and child.name:
                        # Add appropriate block based on child type
                        if child.name == 'p':
                            div_blocks.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": process_rich_text_element(child)
                                }
                            })
                        # Add more child types as needed
                
                blocks.extend(div_blocks if div_blocks else [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": process_rich_text_element(element)
                    }
                }])
            else:
                # Fallback to paragraph for unsupported elements
                text_content = element.get_text().strip()
                if text_content:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": text_content}
                            }]
                        }
                    }
                )
                
        return blocks


# Create a function interface for convenience
def debug_markdown_conversion(md_content) -> Dict[str, Any]:
    """Debug helper to see how URLs are handled in markdown content.
    
    Args:
        md_content: Markdown content to debug (can be str or pyglove.List)
        
    Returns:
        Debug information dictionary
    """
    import re
    
    # Ensure we have a string to work with
    if not isinstance(md_content, str):
        try:
            # Try to convert to string
            md_content_str = str(md_content)
            
            # Special handling for list-like objects (including pyglove.List)
            if hasattr(md_content, '__iter__') and not md_content_str.strip():
                # If str() didn't produce useful content, try joining the items
                md_content_str = '\n'.join([str(item) for item in md_content])
                # Also update the original content for converter
                md_content = md_content_str
            else:
                md_content = md_content_str
        except Exception as e:
            print(f"Error converting object to string in debug_markdown_conversion: {e}")
            # Try using the to_json method if available
            if hasattr(md_content, 'to_json'):
                try:
                    md_content_str = md_content.to_json()
                    md_content = md_content_str
                except Exception as json_err:
                    print(f"Error in to_json conversion: {json_err}")
                    # Last resort
                    if hasattr(md_content, '__iter__'):
                        md_content_str = '\n'.join([str(item) for item in md_content])
                        md_content = md_content_str
                    else:
                        print("Unable to convert input to string format")
                        return {"markdown": "", "urls_found_in_markdown": [], "urls_found_in_blocks": [], "missing_urls": [], "blocks": []}
    else:
        md_content_str = md_content
    
    # Extract URLs from the markdown content
    url_pattern = r'https?://[^\s)"]+'
    urls_in_content = re.findall(url_pattern, md_content_str)
    
    # Get the converted blocks
    converter = MarkdownConverter(use_martian=True)
    blocks = converter.convert(md_content)
    
    # Find URLs in the converted blocks
    urls_in_blocks = []
    def extract_urls_from_blocks(blocks):
        for block in blocks:
            if isinstance(block, dict):
                for key, value in block.items():
                    if key == "url" and isinstance(value, str) and value.startswith("http"):
                        urls_in_blocks.append(value)
                    elif key == "link" and isinstance(value, dict) and "url" in value:
                        urls_in_blocks.append(value["url"])
                    elif key == "text" and isinstance(value, dict) and "link" in value and isinstance(value["link"], dict):
                        urls_in_blocks.append(value["link"].get("url", ""))
                    elif key == "rich_text" and isinstance(value, list):
                        for text_item in value:
                            if isinstance(text_item, dict):
                                if "text" in text_item and isinstance(text_item["text"], dict):
                                    if "link" in text_item["text"] and isinstance(text_item["text"]["link"], dict):
                                        urls_in_blocks.append(text_item["text"]["link"].get("url", ""))
                    elif isinstance(value, dict):
                        extract_urls_from_blocks([value])
                    elif isinstance(value, list):
                        extract_urls_from_blocks(value)
    
    extract_urls_from_blocks(blocks)
    
    return {
        "markdown": md_content,
        "urls_found_in_markdown": urls_in_content,
        "urls_found_in_blocks": urls_in_blocks,
        "missing_urls": [url for url in urls_in_content if url not in urls_in_blocks],
        "blocks": blocks
    }

def process_table_with_links(block):
    """Process a table block to ensure links in cells are properly handled.
    
    Args:
        block: A table block to process
        
    Returns:
        Updated table block with links properly preserved
    """
    if not isinstance(block, dict) or block.get("type") != "table" or "table" not in block:
        return block
        
    # Process each row
    if "children" in block["table"] and isinstance(block["table"]["children"], list):
        for row in block["table"]["children"]:
            if isinstance(row, dict) and "table_row" in row:
                # Process cells in the row
                if "cells" in row["table_row"] and isinstance(row["table_row"]["cells"], list):
                    for i, cell in enumerate(row["table_row"]["cells"]):
                        # Make sure each cell is processed for links
                        # Each cell is a list of rich_text objects
                        for j, text_obj in enumerate(cell):
                            if isinstance(text_obj, dict) and "text" in text_obj:
                                # Check text content for URLs that aren't already linked
                                content = text_obj.get("text", {}).get("content", "")
                                if content and "link" not in text_obj.get("text", {}):
                                    # Simple URL detection
                                    url_match = re.search(r'https?://[^\s]+', content)
                                    if url_match:
                                        url = url_match.group(0)
                                        # Add link if found
                                        text_obj["text"]["link"] = {"url": url}
    
    return block

def clean_markdown_to_notion_blocks(md_content) -> List[Dict[str, Any]]:
    """Convert markdown to Notion blocks with direct file-based approach.
    
    This function uses a direct file-based approach to convert markdown to Notion blocks,
    which ensures links are properly preserved in the output.
    
    Args:
        md_content: Markdown content (can be str or pyglove.List)
        
    Returns:
        List of Notion blocks with properly formatted links
    """
    # Convert pyglove objects or other list-like objects to string if needed
    if not isinstance(md_content, str):
        try:
            # Try to convert to string
            md_content_str = str(md_content)
            
            # Special handling for list-like objects (including pyglove.List)
            if hasattr(md_content, '__iter__') and not md_content_str.strip():
                # If str() didn't produce useful content, try joining the items
                md_content = '\n'.join([str(item) for item in md_content])
            else:
                md_content = md_content_str
                
        except Exception as e:
            print(f"Error converting object to string: {e}")
            # Try using the to_json method if available
            if hasattr(md_content, 'to_json'):
                try:
                    md_content = md_content.to_json()
                except Exception as json_err:
                    print(f"Error in to_json conversion: {json_err}")
                    # Last resort
                    if hasattr(md_content, '__iter__'):
                        md_content = '\n'.join([str(item) for item in md_content])
                    else:
                        print("Unable to convert input to string format")
                        return []
    
    if not md_content:
        return []
    
    # Path to the Node.js bridge script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'markdown_to_notion.js')
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}, falling back to standard conversion")
        converter = MarkdownConverter(use_martian=True)
        return converter.convert(md_content)
    
    try:
        # Create a temporary file with the markdown content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp:
            temp.write(md_content)
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
                converter = MarkdownConverter(use_martian=True)
                return converter.convert(md_content)
            
            # Parse the output
            blocks = json.loads(result.stdout)
            
            # Process tables specifically to ensure links are properly handled
            for i, block in enumerate(blocks):
                if isinstance(block, dict) and block.get("type") == "table":
                    blocks[i] = process_table_with_links(block)
                    
            return blocks
            
        except Exception as e:
            print(f"Error using direct file approach: {str(e)}")
            converter = MarkdownConverter(use_martian=True)
            return converter.convert(md_content)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    except Exception as e:
        print(f"Error setting up direct file approach: {str(e)}")
        converter = MarkdownConverter(use_martian=True)
        return converter.convert(md_content)

def markdown_to_notion_blocks(
    md_content,  # Can be str or pyglove.List
    use_martian: bool = True,
    debug: bool = False,
    fix_links: bool = True
) -> List[Dict[str, Any]]:
    """Convert markdown content to Notion blocks.
    
    Args:
        md_content: Markdown content as string
        use_martian: Whether to attempt to use @tryfabric/martian (default: True)
        debug: Whether to print debug information about URL handling
        fix_links: Whether to use special handling for links (default: True)
        
    Returns:
        List of Notion block objects
    """
    # Make a copy of md_content for debugging to avoid issues with pyglove objects
    # being consumed by the conversion process
    debug_content = md_content
    
    if fix_links and LINK_HANDLER_AVAILABLE:
        # Use the special link handling approach
        result = clean_markdown_to_notion_blocks(md_content)
        
        if debug:
            # Still generate debug info for reference
            debug_info = debug_markdown_conversion(debug_content)
            print("DEBUG - URLs in markdown:", debug_info["urls_found_in_markdown"])
            print("DEBUG - URLs in blocks:", debug_info["urls_found_in_blocks"])
            print("DEBUG - Missing URLs:", debug_info["missing_urls"])
        
        return result
    
    # Regular approach
    if debug:
        debug_info = debug_markdown_conversion(debug_content)
        print("DEBUG - URLs in markdown:", debug_info["urls_found_in_markdown"])
        print("DEBUG - URLs in blocks:", debug_info["urls_found_in_blocks"])
        print("DEBUG - Missing URLs:", debug_info["missing_urls"])
    
    converter = MarkdownConverter(use_martian=use_martian)
    return converter.convert(md_content)