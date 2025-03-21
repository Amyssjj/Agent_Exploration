"""Web browsing and Google search operations for langfun agents."""

from typing import Any, Dict, List, Optional, Union, Literal, ClassVar
import os
import json
import urllib.parse
import traceback
import requests
from bs4 import BeautifulSoup
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg

google_search_api_key = os.environ.get('GOOGLE_API_KEY')
google_search_cx_id = os.environ.get('GOOGLE_CX_ID')


class SearchAction(action_lib.Action):
    """Unified action for web browsing and Google search operations."""
    
    # Allow attribute assignment at runtime
    allow_symbolic_assignment = True
    
    operation: Literal["google_search", "browse_url", "extract_text", "extract_links"] = "google_search"
    api_key = google_search_api_key
    cx_id = google_search_cx_id
    query: Optional[str] = None
    url: Optional[str] = None
    num_results: Optional[int] = 5
    timeout: Optional[int] = 10
    user_agent: Optional[str] = None
    
    
    # Class variables to define defaults
    default_user_agent: ClassVar[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    google_search_url: ClassVar[str] = "https://www.googleapis.com/customsearch/v1"
    
    def _on_bound(self):
        super()._on_bound()
        # Set default user agent if not provided
        if not self.user_agent:
            self.user_agent = self.default_user_agent
            
        # Validate required parameters based on operation
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate parameters based on the operation."""
        # Google search requires a query
        if self.operation == "google_search" and not self.query:
            raise ValueError("Query is required for Google search operation")
            
        # API search requires API key and CX ID
        if self.operation == "google_search" and not self.api_key:
            # We'll use web scraping as fallback if no API key is provided
            # But issue a warning via print
            print("WARNING: Google Search API key not provided. Using web scraping which may be less reliable.")
        
        # URL operations require a URL
        if self.operation in ["browse_url", "extract_text", "extract_links"] and not self.url:
            raise ValueError("URL is required for browsing operations")
        
        # Validate URL format
        if self.url and not (self.url.startswith("http://") or self.url.startswith("https://")):
            self.url = "https://" + self.url
    
    def call(self, session, *, lm=None, **kwargs):
        """Execute the web browsing or search operation.
        
        Args:
            session: The current session.
            lm: Language model (unused but required by langfun Action interface).
            **kwargs: Additional arguments.
            
        Returns:
            Operation-specific result:
                google_search: List of search results (dicts with title, url, snippet)
                browse_url: HTML content of the page
                extract_text: Plain text content of the page
                extract_links: List of links from the page
        """
        try:
            # Log the start of operation with full details
            if self.operation == "google_search":
                session.info(f"Starting Google search for query: {self.query}")
            else:
                session.info(f"Starting {self.operation} operation on {self.url}")
            
            # Execute operation
            result = self._execute_operation()
            
            # Log success
            session.info(f"Successfully executed {self.operation} operation")
            return result
            
        except Exception as e:
            # Log full exception details
            error_msg = f"Failed to execute {self.operation} operation: {str(e)}"
            session.error(error_msg)
            session.error(traceback.format_exc())
            raise RuntimeError(error_msg) from e
    
    def _execute_operation(self) -> Any:
        """Execute the specific web operation."""
        if self.operation == "google_search":
            if self.api_key and self.cx_id:
                return self._google_search_api()
            else:
                return self._google_search_scrape()
        
        elif self.operation == "browse_url":
            return self._browse_url()
        
        elif self.operation == "extract_text":
            html_content = self._browse_url()
            return self._extract_text_from_html(html_content)
        
        elif self.operation == "extract_links":
            html_content = self._browse_url()
            return self._extract_links_from_html(html_content)
        
        else:
            raise ValueError(f"Unsupported operation: {self.operation}")
    
    def _google_search_api(self) -> List[Dict[str, str]]:
        """Perform a Google search using the Custom Search API."""
        params = {
            'key': self.api_key,
            'cx': self.cx_id,
            'q': self.query,
            'num': min(self.num_results, 10),  # API limit is 10 per request
            'sort': 'date'  # Sort by date (most recent first)
        }
        
        response = requests.get(
            self.google_search_url,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        search_results = []
        
        if 'items' in data:
            for item in data['items']:
                search_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')
                })
                
            # Sort results by relevance score and then by date if available
            search_results.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return search_results
    
    def _google_search_scrape(self) -> List[Dict[str, str]]:
        """Perform a Google search by scraping results (fallback method)."""
        # Use DuckDuckGo instead - it's more scraping-friendly
        # Add 'sort:date' to the query to prioritize recent results
        search_query = f"{self.query} sort:date"
        params = {
            'q': search_query,
        }
        
        # Set up headers to avoid being blocked
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Print debugging info
        print(f"Searching DuckDuckGo for: {search_query}")
        
        # Make the request
        response = requests.get(
            "https://html.duckduckgo.com/html/", 
            params=params, 
            headers=headers, 
            timeout=self.timeout
        )
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract search results - DuckDuckGo uses different selectors
        search_results = []
        
        # Try different selectors that might work
        selectors = [
            '.result', '.web-result', '.results_links', '.links_main', 
            'article', '.serp__results', '.react-results--main'
        ]
        
        results = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                print(f"Found {len(found)} results with selector '{selector}'")
                results = found
                break
                
        if not results:
            print("No results found with any selector. Using direct extraction method.")
            # Simple direct extraction of links and text
            links = soup.find_all('a')
            print(f"Found {len(links)} links in the page")
            
            for link in links[:self.num_results]:
                if link.get('href') and not link.get('href').startswith('#'):
                    search_results.append({
                        'title': link.get_text().strip() or "No title",
                        'url': link.get('href'),
                        'snippet': "No snippet available",
                        'date': ''  # Date is unknown
                    })
        else:
            print(f"Processing {len(results)} results")
        
        for result in results[:self.num_results]:
            try:
                # DuckDuckGo HTML structure
                title_element = result.select_one('.result__title')
                link_element = result.select_one('.result__url')
                snippet_element = result.select_one('.result__snippet')
                date_element = result.select_one('.result__date') or result.select_one('.result-timestamp')
                
                if title_element:
                    title = title_element.get_text().strip()
                    url_tag = title_element.find('a')
                    url = url_tag.get('href') if url_tag else ""
                    
                    # Get snippet if available
                    snippet = ""
                    if snippet_element:
                        snippet = snippet_element.get_text().strip()
                    
                    # Get date if available
                    date = ""
                    if date_element:
                        date = date_element.get_text().strip()
                    
                    # DuckDuckGo redirects through their server, so extract the real URL
                    if url and '/redirect/' in url:
                        url_param = url.split('uddg=')[-1].split('&')[0]
                        url = urllib.parse.unquote(url_param)
                    
                    search_results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'date': date
                    })
            except Exception as e:
                # Print exception for debugging
                print(f"Error parsing result: {str(e)}")
                # Skip results that can't be parsed
                continue
        
        # Sort results by date (if available)
        # If date isn't available for all results, they will stay in their original order
        search_results.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return search_results
    
    def _browse_url(self) -> str:
        """Fetch content from a given URL."""
        headers = {
            'User-Agent': self.user_agent
        }
        
        response = requests.get(self.url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        return response.text
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract readable text from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text and normalize whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_links_from_html(self, html_content: str) -> List[Dict[str, str]]:
        """Extract links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.get_text().strip()
            
            if href and href.startswith(('http://', 'https://')):
                links.append({
                    'url': href,
                    'text': text
                })
        
        return links