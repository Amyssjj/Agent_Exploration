"""Notion integration for Langfun agents."""

from typing import Any, Optional, List, Dict, Union, Literal, ClassVar, Tuple
import os
import traceback
import json
import re
import urllib.parse
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg

try:
    from notion_client import Client
    import requests
    
    # Try to import the specialized markdown converter
    try:
        from notion_markdown_utils import markdown_to_notion_blocks, clean_markdown_to_notion_blocks
        NOTION_MARKDOWN_UTILS_AVAILABLE = True
    except ImportError:
        NOTION_MARKDOWN_UTILS_AVAILABLE = False
        # Fall back to basic imports
        import markdown
        from bs4 import BeautifulSoup
        
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    NOTION_MARKDOWN_UTILS_AVAILABLE = False

class NotionAction(action_lib.Action):
    """Notion API action for database, page, and block operations.
    
    This action allows agents to interact with Notion workspaces, including
    reading, creating, updating, searching, and listing Notion resources.
    Requires the notion-client package and a Notion integration token.
    """
    
    # Allow attribute modifications at runtime
    allow_symbolic_assignment = True
    
    # Define operations
    operation: Literal[
        "read_page", 
        "create_page", 
        "update_page", 
        "search",
        "query_database",
        "create_database",
        "update_database",
        "list_users",
        "get_page_info",
        "get_database_info"
    ] = "read_page"
    
    # Define parameters
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    parent_id: Optional[str] = None
    parent_type: Optional[Literal["page", "database", "workspace"]] = None
    query_filter: Optional[Dict[str, Any]] = None
    query_sorts: Optional[List[Dict[str, Any]]] = None
    properties: Optional[Dict[str, Any]] = None
    content: Optional[List[Dict[str, Any]]] = None
    token: Optional[str] = None
    limit: Optional[int] = 100
    search_query: Optional[str] = None
    search_filter: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    markdown_content: Optional[str] = None
    markdown_title: Optional[str] = None
    debug_markdown: bool = False
    
    # Class variables
    notion_api_version: ClassVar[str] = "2022-06-28"
    
    def _on_bound(self):
        """Initialize and validate parameters."""
        super()._on_bound()  # Always call parent first
        
        # These variables track if we've already processed URL and parameters
        # to prevent infinite recursion
        self._url_processed = False
        self._params_validated = False
        self._extraction_failed = False
        self._markdown_processed = False
        
        # Process markdown if provided
        if self.markdown_content and not self._markdown_processed:
            self._markdown_processed = True
            self._process_markdown()
        
        # Extract IDs from URL if provided
        if self.url and not self._url_processed:
            self._url_processed = True
            self._extract_ids_from_url()
        
        # Validate parameters
        if not self._params_validated:
            self._params_validated = True
            self._validate_parameters()
        
        # Set up client if Notion is available
        if NOTION_AVAILABLE:
            # Get token from parameter or environment
            self._token = self.token or os.environ.get('NOTION_API_TOKEN')
            
            if self._token:
                try:
                    # Try newer API format (if api_version is not accepted)
                    self._client = Client(auth=self._token)
                except TypeError:
                    # Fall back to older API format with api_version
                    try:
                        self._client = Client(auth=self._token, api_version=self.notion_api_version)
                    except Exception as e:
                        print(f"Error initializing Notion client: {str(e)}")
                        self._client = None
            else:
                self._client = None
    
    def _extract_ids_from_url(self):
        """Extract page ID, database ID, or block ID from Notion URL."""
        if not self.url:
            return
            
        # Guard against recursion - don't extract if already set
        if self.page_id or self.database_id:
            return
        
        # Regular expression patterns for Notion URLs
        page_pattern = r"notion\.so/(?:[^/]+/)?([a-f0-9]{32})(?:-[a-zA-Z0-9]+)?$"
        database_pattern = r"notion\.so/(?:[^/]+/)?([a-f0-9]{32})(?:-[a-zA-Z0-9]+)?\?v=([a-zA-Z0-9]+)$"
        
        # Try to extract database ID first (more specific pattern)
        database_match = re.search(database_pattern, self.url)
        if database_match:
            self.database_id = database_match.group(1)
            return
        
        # Try to extract page ID
        page_match = re.search(page_pattern, self.url)
        if page_match:
            self.page_id = page_match.group(1)
            return
        
        # If no specific pattern matched, try to extract any ID-like string from the URL
        # This is a fallback for newer Notion URL formats
        id_pattern = r"([a-f0-9]{32})"
        id_match = re.search(id_pattern, self.url)
        if id_match:
            # Try to determine if it's a page or database by checking URL keywords
            if "database" in self.url.lower():
                self.database_id = id_match.group(1)
            else:
                self.page_id = id_match.group(1)
            return
        
        # If we still can't determine, extract from path components
        # But don't recurse or make circular references
        parts = self.url.split("/")
        if parts and len(parts) > 0:
            last_part = parts[-1].split("?")[0]
            if "-" in last_part:
                path_segments = last_part.split("-")
                if path_segments and len(path_segments[0]) == 32:
                    self.page_id = path_segments[0]
    
    def _process_markdown(self):
        """Process markdown content into Notion blocks and properties."""
        if not self.markdown_content:
            return
            
        # If properties not already set, create them
        if not self.properties:
            # Extract title from markdown if not provided separately
            title = self.markdown_title or self._extract_title_from_markdown()
            
            # Create properties with the title
            self.properties = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        
        # If content not already set, convert markdown to blocks
        if not self.content:
            self.content = self._markdown_to_notion_blocks(self.markdown_content)
    
    def _extract_title_from_markdown(self) -> str:
        """Extract title from markdown content."""
        if not self.markdown_content:
            return "Untitled"
            
        # Look for the first heading in the markdown
        lines = self.markdown_content.split('\n')
        for line in lines:
            # Check for a heading (# Title)
            if line.strip().startswith('#'):
                # Remove the # symbols and return the trimmed text
                return line.strip().lstrip('#').strip()
                
        # If no heading is found, use the first non-empty line or a default
        for line in lines:
            if line.strip():
                return line.strip()
                
        return "Untitled"
    
    def _markdown_to_notion_blocks(self, md_content: str) -> List[Dict[str, Any]]:
        """Convert markdown content to Notion blocks with rich formatting.
        
        This method uses the notion_markdown_utils module for conversion if available,
        or falls back to the built-in approach if not.
        
        Args:
            md_content: Markdown content as string
            
        Returns:
            List of Notion block objects
        """
        if not md_content:
            return []
        
        # Import the fallback libraries if needed
        markdown_module = None
        bs4_module = None
        
        # First, try to import the necessary fallback libraries
        if 'markdown' not in globals() or 'BeautifulSoup' not in globals():
            try:
                import markdown as markdown_module
                from bs4 import BeautifulSoup as bs4_module
            except ImportError:
                # If we can't import them, we'll rely solely on the specialized utility
                markdown_module = None
                bs4_module = None
        else:
            # If they're already in globals, use them
            markdown_module = markdown
            bs4_module = BeautifulSoup
            
        # Use the specialized utility if available
        if 'NOTION_MARKDOWN_UTILS_AVAILABLE' in globals() and NOTION_MARKDOWN_UTILS_AVAILABLE:
            try:
                # For best URL handling, always use the special converter
                try:
                    return clean_markdown_to_notion_blocks(md_content)
                except Exception as e:
                    # Fall back to regular converter if special one fails
                    print(f"Special markdown converter failed: {e}")
                    return markdown_to_notion_blocks(md_content, debug=self.debug_markdown)
            except Exception as e:
                print(f"Error using clean_markdown_to_notion_blocks: {str(e)}")
                print("Falling back to built-in markdown conversion")
                
                # If the specialized utility failed, check if we have fallback libraries
                if markdown_module is None or bs4_module is None:
                    print("Cannot convert markdown: required fallback libraries not available")
                    return []
        elif markdown_module is None or bs4_module is None:
            print("Cannot convert markdown: required libraries not available")
            return []
        
        # Fallback to built-in BeautifulSoup approach
        # Convert markdown to HTML with extensions for tables and code highlighting
        html = markdown_module.markdown(
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
        soup = bs4_module(html, 'html.parser')
        
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
    
    def _validate_parameters(self):
        """Validate parameters are consistent."""
        if not NOTION_AVAILABLE:
            raise ImportError(
                "Notion client library not available. "
                "Install with: pip install notion-client requests markdown beautifulsoup4\n"
                "For improved markdown support, install the notion_markdown_utils package:\n"
                "1. Add the 'notion_markdown_utils' directory to your Python path\n"
                "2. Install Node.js and run: cd notion_markdown_utils && npm install"
            )
        
        # Validate operation-specific required parameters
        if self.operation == "read_page":
            if not self.page_id and not self.url:
                raise ValueError("Either page_id or url is required for read_page operation")
        
        if self.operation == "create_page":
            if not self.parent_id and not self.url:
                raise ValueError("Either parent_id or url (pointing to parent) is required for create_page operation")
            if not self.parent_type and not self.url:
                raise ValueError("parent_type is required for create_page operation if url is not provided")
            if not self.properties and not self.markdown_content:
                raise ValueError("Either properties or markdown_content is required for create_page operation")
        
        if self.operation == "update_page":
            if not self.page_id and not self.url:
                raise ValueError("Either page_id or url is required for update_page operation")
        
        if self.operation == "query_database":
            if not self.database_id and not self.url:
                raise ValueError("Either database_id or url is required for query_database operation")
            
        if self.operation == "create_database":
            if not self.parent_id and not self.url:
                raise ValueError("Either parent_id or url (pointing to parent) is required for create_database operation")
            if not self.properties:
                raise ValueError("properties is required for create_database operation")
        
        if self.operation == "update_database":
            if not self.database_id and not self.url:
                raise ValueError("Either database_id or url is required for update_database operation")
                
        if self.operation == "get_page_info":
            if not self.page_id and not self.url:
                raise ValueError("Either page_id or url is required for get_page_info operation")
                
        if self.operation == "get_database_info":
            if not self.database_id and not self.url:
                raise ValueError("Either database_id or url is required for get_database_info operation")
                
        # Warning if URL is provided but we couldn't extract IDs
        # We don't raise here to avoid breaking initialization - we'll handle it in call()
        if self.url and not (self.page_id or self.database_id or self.parent_id):
            # Set a flag for the extraction failure
            # We use an instance variable since we need it later in call()
            self._extraction_failed = True
    
    def call(self, session, *, lm=None, **kwargs):
        """Execute the Notion operation.
        
        Args:
            session: The current session context
            lm: Language model (required by interface)
            **kwargs: Additional keyword arguments
            
        Returns:
            Operation results based on the type of operation performed
        """
        try:
            session.info(f"Starting Notion {self.operation} operation")
            
            # Check if we had URL extraction issues
            if hasattr(self, '_extraction_failed') and self._extraction_failed:
                error_msg = f"Could not extract a valid Notion ID from the provided URL: {self.url}"
                session.error(error_msg)
                return {"error": error_msg}
            
            # Check if token is available
            if not self._token:
                error_msg = "Notion API token not provided. Set via token parameter or NOTION_API_TOKEN environment variable."
                session.error(error_msg)
                return {"error": error_msg}
            
            # Check if client is initialized
            if not self._client:
                error_msg = "Notion client initialization failed"
                session.error(error_msg)
                return {"error": error_msg}
            
            # Check operation requirements
            if self.operation == "read_page" and not self.page_id:
                error_msg = "Page ID is required and could not be extracted from URL"
                session.error(error_msg)
                return {"error": error_msg}
                
            if self.operation == "query_database" and not self.database_id:
                error_msg = "Database ID is required and could not be extracted from URL"
                session.error(error_msg)
                return {"error": error_msg}
            
            # Execute the operation
            result = self._execute_operation()
            
            # Enhance result for create_page and update_page operations
            if self.operation in ["create_page", "update_page"] and not result.get("error"):
                # Generate a success message with the page URL
                page_url = result.get("url", "")
                page_title = self._extract_page_title(result)
                
                # Create a display-friendly success message (for logs and direct printing)
                display_message = ""
                if self.operation == "create_page":
                    display_message = f"Successfully created Notion page: '{page_title}'"
                else:  # update_page
                    display_message = f"Successfully updated Notion page: '{page_title}'"
                
                if page_url:
                    display_message += f"\nView your page at: {page_url}"
                
                # Create a markdown-formatted version for the result
                markdown_message = display_message
                
                # Add both versions to the result
                result["success_message"] = display_message
                result["success_message_markdown"] = markdown_message
                result["page_url"] = page_url
                result["page_title"] = page_title
                
                # Log the display-friendly version
                session.info(display_message)
            
            session.info(f"Completed Notion {self.operation} operation")
            return result
            
        except Exception as e:
            error_msg = f"Failed to execute Notion {self.operation}: {str(e)}"
            session.error(error_msg)
            session.error(traceback.format_exc())
            
            # Return structured error for better handling
            return {
                "error": str(e),
                "operation": self.operation,
                "traceback": traceback.format_exc()
            }
    
    def _extract_page_title(self, page_data):
        """Extract page title from Notion page data.
        
        Args:
            page_data: Notion page data
            
        Returns:
            Page title as string, or "Untitled" if not found
        """
        if not page_data:
            return "Untitled"
            
        # Try to extract title from properties
        if "properties" in page_data:
            properties = page_data.get("properties", {})
            # Check for title property
            title_prop = properties.get("title", properties.get("Name", None))
            if title_prop and "title" in title_prop and title_prop["title"]:
                # Extract text from title
                title_text = []
                for text_obj in title_prop["title"]:
                    if "plain_text" in text_obj:
                        title_text.append(text_obj["plain_text"])
                    elif "text" in text_obj and "content" in text_obj["text"]:
                        title_text.append(text_obj["text"]["content"])
                
                if title_text:
                    return " ".join(title_text)
        
        # Use page ID as fallback
        return page_data.get("id", "Untitled")
    
    def _execute_operation(self) -> Any:
        """Execute the specific Notion operation."""
        if self.operation == "read_page":
            return self._read_page()
        elif self.operation == "create_page":
            return self._create_page()
        elif self.operation == "update_page":
            return self._update_page()
        elif self.operation == "search":
            return self._search()
        elif self.operation == "query_database":
            return self._query_database()
        elif self.operation == "create_database":
            return self._create_database()
        elif self.operation == "update_database":
            return self._update_database()
        elif self.operation == "list_users":
            return self._list_users()
        elif self.operation == "get_page_info":
            return self._get_page_info()
        elif self.operation == "get_database_info":
            return self._get_database_info()
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")
    
    def _read_page(self) -> Dict[str, Any]:
        """Read a Notion page.
        
        Returns:
            Page data including properties and content
        """
        # Get the page
        page = self._client.pages.retrieve(self.page_id)
        
        # Get page content (blocks)
        blocks = []
        has_more = True
        cursor = None
        
        while has_more:
            response = self._client.blocks.children.list(
                block_id=self.page_id,
                start_cursor=cursor
            )
            blocks.extend(response["results"])
            has_more = response["has_more"]
            cursor = response.get("next_cursor")
        
        # Combine page metadata with content
        result = {
            "page": page,
            "blocks": blocks
        }
        
        return result
    
    def _create_page(self) -> Dict[str, Any]:
        """Create a new Notion page.
        
        Returns:
            The created page data with URL
        """
        # Create parent reference
        if self.parent_type == "page":
            parent = {"page_id": self.parent_id}
        elif self.parent_type == "database":
            parent = {"database_id": self.parent_id}
        elif self.parent_type == "workspace":
            parent = {"workspace": True}
        else:
            raise ValueError(f"Invalid parent_type: {self.parent_type}")
        
        # Prepare page creation data
        page_data = {
            "parent": parent,
            "properties": self.properties
        }
        
        # Handle content in chunks to avoid the 100 block limit
        original_content = self.content
        initial_content = []
        
        # If content exists, take only the first 100 blocks for initial creation
        if original_content and len(original_content) > 0:
            initial_content = original_content[:100]
            page_data["children"] = initial_content
        elif original_content:
            page_data["children"] = original_content
        
        # Create the page with initial content
        page = self._client.pages.create(**page_data)
        
        # Ensure the URL is included in the response
        # If the URL is not already in the response, construct it
        if "url" not in page and "id" in page:
            page_id = page["id"]
            page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
            page["url"] = page_url
        
        # If we have more content to add, append it in chunks
        if original_content and len(original_content) > 100:
            remaining_content = original_content[100:]
            page_id = page["id"]
            
            # Add remaining content in chunks of 100
            for i in range(0, len(remaining_content), 100):
                chunk = remaining_content[i:i+100]
                try:
                    self._client.blocks.children.append(
                        block_id=page_id,
                        children=chunk
                    )
                except Exception as e:
                    page["content_append_error"] = str(e)
                    break
            
            # Add a flag to indicate multiple chunks were processed
            page["content_chunked"] = True
            page["total_content_blocks"] = len(original_content)
        
        return page
    
    def _update_page(self) -> Dict[str, Any]:
        """Update a Notion page.
        
        Returns:
            The updated page data with URL
        """
        update_data = {}
        
        # Add properties if provided
        if self.properties:
            update_data["properties"] = self.properties
        
        # Update the page
        page = self._client.pages.update(page_id=self.page_id, **update_data)
        
        # If content is provided, update the page content
        if self.content:
            # First archive existing content
            existing_blocks = self._client.blocks.children.list(block_id=self.page_id)
            for block in existing_blocks.get("results", []):
                self._client.blocks.update(block_id=block["id"], archived=True)
            
            # Then add new content
            self._client.blocks.children.append(
                block_id=self.page_id,
                children=self.content
            )
            
            # Get the updated content
            updated_blocks = self._client.blocks.children.list(block_id=self.page_id)
            page["blocks"] = updated_blocks.get("results", [])
        
        # Ensure the URL is included in the response
        # If the URL is not already in the response, construct it
        if "url" not in page and "id" in page:
            page_id = page["id"]
            page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
            page["url"] = page_url
        
        return page
    
    def _search(self) -> Dict[str, Any]:
        """Search Notion workspace.
        
        Returns:
            Search results
        """
        search_params = {
            "query": self.search_query,
            "page_size": self.limit
        }
        
        # Add filter if provided
        if self.search_filter:
            search_params["filter"] = self.search_filter
        
        # Perform search
        results = self._client.search(**search_params)
        
        return results
    
    def _query_database(self) -> Dict[str, Any]:
        """Query a Notion database.
        
        Returns:
            Database query results
        """
        query_params = {
            "database_id": self.database_id,
            "page_size": self.limit
        }
        
        # Add filter if provided
        if self.query_filter:
            query_params["filter"] = self.query_filter
        
        # Add sorts if provided
        if self.query_sorts:
            query_params["sorts"] = self.query_sorts
        
        # Query the database
        results = self._client.databases.query(**query_params)
        
        return results
    
    def _create_database(self) -> Dict[str, Any]:
        """Create a new Notion database.
        
        Returns:
            The created database data
        """
        # Create parent reference
        parent = {"page_id": self.parent_id}
        
        # Create the database
        database = self._client.databases.create(
            parent=parent,
            title=self.content if self.content else [{"text": {"content": "Untitled Database"}}],
            properties=self.properties
        )
        
        return database
    
    def _update_database(self) -> Dict[str, Any]:
        """Update a Notion database.
        
        Returns:
            The updated database data
        """
        update_data = {
            "database_id": self.database_id
        }
        
        # Add title if provided
        if self.content:
            update_data["title"] = self.content
        
        # Add properties if provided
        if self.properties:
            update_data["properties"] = self.properties
        
        # Update the database
        database = self._client.databases.update(**update_data)
        
        return database
    
    def _list_users(self) -> Dict[str, Any]:
        """List users in the workspace.
        
        Returns:
            List of users
        """
        users = self._client.users.list()
        
        return users
        
    def _get_page_info(self) -> Dict[str, Any]:
        """Get basic information about a page.
        
        Returns:
            Simplified page metadata
        """
        # Get the page
        page = self._client.pages.retrieve(self.page_id)
        
        # Extract the most relevant information
        title = ""
        if "properties" in page and "title" in page["properties"]:
            title_obj = page["properties"]["title"]
            if "title" in title_obj and title_obj["title"]:
                title = " ".join([t.get("plain_text", "") for t in title_obj["title"]])
        
        # Get basic block count without retrieving full content
        blocks_response = self._client.blocks.children.list(
            block_id=self.page_id,
            page_size=100  # Just to get an idea of content size
        )
        
        # Create a simplified response with the most important information
        simple_info = {
            "id": page["id"],
            "title": title,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", ""),
            "properties": self._simplify_properties(page.get("properties", {})),
            "parent_type": page.get("parent", {}).get("type", ""),
            "block_count": len(blocks_response.get("results", [])),
            "has_more_blocks": blocks_response.get("has_more", False)
        }
        
        return simple_info
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic information about a database.
        
        Returns:
            Simplified database metadata and schema
        """
        # Get the database
        database = self._client.databases.retrieve(self.database_id)
        
        # Extract title
        title = ""
        if "title" in database and database["title"]:
            title = " ".join([t.get("plain_text", "") for t in database["title"]])
        
        # Get a sample of rows to understand content
        rows_response = self._client.databases.query(
            database_id=self.database_id,
            page_size=5  # Just get a few rows as a sample
        )
        
        # Create a simplified response with the most important information
        simple_info = {
            "id": database["id"],
            "title": title,
            "url": database.get("url", ""),
            "created_time": database.get("created_time", ""),
            "last_edited_time": database.get("last_edited_time", ""),
            "property_schema": self._simplify_database_schema(database.get("properties", {})),
            "sample_rows_count": len(rows_response.get("results", [])),
            "total_rows_available": rows_response.get("has_more", False)
        }
        
        return simple_info
    
    def _simplify_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify page properties for easier consumption.
        
        Args:
            properties: Raw properties dictionary from Notion API
            
        Returns:
            Simplified properties with plain text values
        """
        simplified = {}
        
        for name, prop in properties.items():
            prop_type = prop.get("type", "")
            value = None
            
            if prop_type == "title" and prop.get("title"):
                value = " ".join([t.get("plain_text", "") for t in prop["title"]])
            elif prop_type == "rich_text" and prop.get("rich_text"):
                value = " ".join([t.get("plain_text", "") for t in prop["rich_text"]])
            elif prop_type == "number":
                value = prop.get("number")
            elif prop_type == "select" and prop.get("select"):
                value = prop["select"].get("name", "")
            elif prop_type == "multi_select" and prop.get("multi_select"):
                value = [item.get("name", "") for item in prop["multi_select"]]
            elif prop_type == "date" and prop.get("date"):
                value = prop["date"].get("start", "")
                if prop["date"].get("end"):
                    value += f" to {prop['date'].get('end', '')}"
            elif prop_type == "checkbox":
                value = prop.get("checkbox", False)
            elif prop_type == "url":
                value = prop.get("url", "")
            elif prop_type == "email":
                value = prop.get("email", "")
            elif prop_type == "phone_number":
                value = prop.get("phone_number", "")
            elif prop_type == "status" and prop.get("status"):
                value = prop["status"].get("name", "")
            else:
                # For other property types, just note the type
                value = f"<{prop_type} property>"
                
            simplified[name] = value
            
        return simplified
    
    def _simplify_database_schema(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify database schema for easier consumption.
        
        Args:
            properties: Raw properties dictionary from the database schema
            
        Returns:
            Simplified schema with property types and options
        """
        schema = {}
        
        for name, prop in properties.items():
            prop_type = prop.get("type", "")
            
            prop_info = {
                "type": prop_type
            }
            
            # Add options for select properties
            if prop_type == "select" and "select" in prop:
                prop_info["options"] = [option.get("name", "") for option in prop["select"].get("options", [])]
            elif prop_type == "multi_select" and "multi_select" in prop:
                prop_info["options"] = [option.get("name", "") for option in prop["multi_select"].get("options", [])]
            elif prop_type == "status" and "status" in prop:
                prop_info["options"] = [option.get("name", "") for option in prop["status"].get("options", [])]
            
            schema[name] = prop_info
            
        return schema
    
    def __str__(self):
        """Return a string representation of the action."""
        if self.operation == "read_page" and self.page_id:
            return f"NotionAction({self.operation}: {self.page_id})"
        elif self.operation == "query_database" and self.database_id:
            return f"NotionAction({self.operation}: {self.database_id})"
        elif self.operation == "search" and self.search_query:
            return f"NotionAction({self.operation}: {self.search_query})"
        else:
            return f"NotionAction({self.operation})"


# Example usage:
if __name__ == "__main__":
    # Create a model
    model = lf.llms.OpenAI(model="gpt-4")
    
    # Create a session
    session = action_lib.Session()
    
    # Example 1: Get simplified page info using URL
    page_info_action = NotionAction(
        operation="get_page_info",
        url="https://www.notion.so/myworkspace/83c75a51b3b343a9a2af4e016ace0062"
        # token will be taken from environment variable NOTION_API_TOKEN if not specified
    )
    page_info = page_info_action(session=session, lm=model)
    if not page_info.get("error"):
        print(f"Page title: {page_info.get('title')}")
        print(f"Created: {page_info.get('created_time')}")
        print(f"URL: {page_info.get('url')}")
    else:
        print(f"Error: {page_info['error']}")
    
    # Example 2: Query a database using URL
    query_action = NotionAction(
        operation="query_database",
        url="https://www.notion.so/myworkspace/5cb03dd565974f7790496d5c1cfc6abf",
        query_filter={
            "property": "Status",
            "status": {
                "equals": "Done"
            }
        },
        limit=5
    )
    results = query_action(session=action_lib.Session(), lm=model)
    if not results.get("error"):
        print(f"Found {len(results.get('results', []))} database entries")
    else:
        print(f"Error: {results['error']}")
    
    # Example 3: Create a page in a database using URL
    create_page_action = NotionAction(
        operation="create_page",
        url="https://www.notion.so/myworkspace/5cb03dd565974f7790496d5c1cfc6abf",  # Database URL
        parent_type="database",  # Specify this is a database
        properties={
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": "New task created via API"
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": "To Do"
                }
            }
        }
    )
    new_page = create_page_action(session=action_lib.Session(), lm=model)
    if not new_page.get("error"):
        print(f"Created new page with ID: {new_page.get('id')}")
    else:
        print(f"Error: {new_page['error']}")
        
    # Example 4: Get database schema information
    db_info_action = NotionAction(
        operation="get_database_info",
        url="https://www.notion.so/myworkspace/5cb03dd565974f7790496d5c1cfc6abf"
    )
    db_info = db_info_action(session=action_lib.Session(), lm=model)
    if not db_info.get("error"):
        print(f"Database: {db_info.get('title')}")
        print(f"Properties: {', '.join(db_info.get('property_schema', {}).keys())}")
        print(f"Sample rows: {db_info.get('sample_rows_count')}")
    else:
        print(f"Error: {db_info['error']}")
        
    # Example 5: Search for pages or databases
    search_action = NotionAction(
        operation="search",
        search_query="Project",
        search_filter={"property": "object", "value": "page"}
    )
    search_results = search_action(session=action_lib.Session(), lm=model)
    if not search_results.get("error"):
        print(f"Found {len(search_results.get('results', []))} matching items")
        for i, result in enumerate(search_results.get("results", [])[:3]):
            result_type = result.get("object", "unknown")
            if result_type == "page":
                title = ""
                for prop in result.get("properties", {}).values():
                    if prop.get("type") == "title" and prop.get("title"):
                        title = " ".join([t.get("plain_text", "") for t in prop["title"]])
                        break
                print(f"  {i+1}. Page: {title}")
            elif result_type == "database":
                title = " ".join([t.get("plain_text", "") for t in result.get("title", [])])
                print(f"  {i+1}. Database: {title}")
    else:
        print(f"Error: {search_results['error']}")