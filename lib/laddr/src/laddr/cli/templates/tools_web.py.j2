"""
Web research tools with improved reliability and error handling.
"""
from __future__ import annotations

from typing import Dict, List
import os

try:
    from laddr import tool  # type: ignore
except Exception:
    def tool(*_a, **_k):
        def _d(f):
            return f
        return _d


@tool(
    name="web_search",
    description="Search the web using Serper.dev API. Returns title, URL, and snippet for each result.",
    trace=True,
    trace_mask=[],
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string", 
                "description": "Search query (be specific for better results)"
            },
            "max_results": {
                "type": "integer", 
                "description": "Maximum number of results to return (1-10, default 5)",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
def web_search(query: str, max_results: int = 5) -> Dict:
    """
    Search the web and return structured results.
    
    Returns:
        {
            "query": str,
            "results": [{"title": str, "link": str, "snippet": str, "site": str}, ...],
            "count": int,
            "status": "success" | "error"
        }
    
    Setup: Set SERPER_API_KEY in your .env file (get key from serper.dev)
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "status": "error",
            "error": "SERPER_API_KEY environment variable not set. Get API key from https://serper.dev"
        }

    try:
        import requests  # type: ignore
    except ImportError:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "status": "error",
            "error": "requests library not installed. Run: pip install requests"
        }

    try:
        # Clamp max_results to valid range
        num_results = max(1, min(int(max_results or 5), 10))
        
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": num_results, "hl": "en"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        # Parse results with priority order: Knowledge Graph > Answer Box > Organic
        results: List[Dict] = []
        
        # Add knowledge graph (best for factual queries)
        if data.get("knowledgeGraph"):
            kg = data["knowledgeGraph"]
            results.append({
                "title": kg.get("title", "Knowledge Graph"),
                "link": kg.get("descriptionUrl", kg.get("website", "")),
                "snippet": kg.get("description", "")[:500],
                "site": "Knowledge Graph",
                "type": "knowledge_graph"
            })
        
        # Add answer box (best for direct answers)
        if data.get("answerBox"):
            ab = data["answerBox"]
            results.append({
                "title": ab.get("title", "Direct Answer"),
                "link": ab.get("link", ""),
                "snippet": (ab.get("answer") or ab.get("snippet") or "")[:500],
                "site": ab.get("source", "Answer Box"),
                "type": "answer_box"
            })
        
        # Add organic search results
        for item in (data.get("organic", []) or [])[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": (item.get("snippet") or "")[:500],
                "site": item.get("domain", item.get("link", "")),
                "type": "organic"
            })

        return {
            "query": query,
            "results": results[:num_results],
            "count": len(results[:num_results]),
            "status": "success"
        }
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP {e.response.status_code}"
        if e.response.status_code == 403:
            error_msg = "API key invalid or quota exceeded. Check your SERPER_API_KEY."
        elif e.response.status_code == 429:
            error_msg = "Rate limit exceeded. Wait a moment and try again."
        
        return {
            "query": query,
            "results": [],
            "count": 0,
            "status": "error",
            "error": error_msg
        }
    
    except Exception as e:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "status": "error",
            "error": f"Search failed: {str(e)}"
        }


@tool(
    name="scrape_url",
    description="Extract clean text content from a webpage URL. Returns up to 8000 characters. Fast fail on blocked sites.",
    trace=True,
    trace_mask=[],
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to scrape (must start with http:// or https://)"
            }
        },
        "required": ["url"]
    }
)
def scrape_url(url: str) -> Dict:
    """
    Scrape and extract clean text from a webpage.
    
    Returns:
        {
            "url": str,
            "content": str,  # Clean text content (up to 8000 chars)
            "title": str,    # Page title if available
            "status": "success" | "failed",
            "length": int    # Original content length before truncation
        }
    
    Features:
    - Fast fail on blocked sites (no retries)
    - Removes scripts, styles, and navigation elements
    - Returns clean, readable text
    - 15 second timeout
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": "Missing dependencies. Run: pip install requests beautifulsoup4"
        }
    
    # Validate URL
    if not url.startswith(("http://", "https://")):
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": "Invalid URL. Must start with http:// or https://"
        }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else ""
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
            element.decompose()
        
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Success - return content
        content_length = len(text)
        truncated_content = text[:8000]
        
        return {
            "url": url,
            "title": title,
            "content": truncated_content,
            "length": content_length,
            "truncated": content_length > 8000,
            "status": "success"
        }
        
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            error_msg = "Website blocked this request (403 Forbidden). Skip this source."
        elif status_code == 404:
            error_msg = "Page not found (404). URL may be invalid or outdated."
        elif status_code == 429:
            error_msg = "Rate limited (429). Too many requests to this site."
        else:
            error_msg = f"HTTP error {status_code}. Website may be blocking bots."
        
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": error_msg
        }
        
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": "Request timed out after 15 seconds. Skip this source and try another."
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": "Connection failed. Site may be down or URL is invalid."
        }
        
    except Exception as e:
        return {
            "url": url,
            "content": "",
            "status": "failed",
            "error": f"Scraping failed: {str(e)}"
        }


@tool(
    name="extract_links",
    description="Extract all HTTP/HTTPS links from a webpage. Returns list of URLs.",
    trace=True,
    trace_mask=[],
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to extract links from"
            },
            "max_links": {
                "type": "integer",
                "description": "Maximum number of links to return (default 50)",
                "default": 50
            }
        },
        "required": ["url"]
    }
)
def extract_links(url: str, max_links: int = 50) -> Dict:
    """
    Extract all links from a webpage.
    
    Returns:
        {
            "url": str,
            "links": List[str],  # List of absolute URLs
            "count": int,
            "status": "success" | "failed"
        }
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
    except ImportError:
        return {
            "url": url,
            "links": [],
            "count": 0,
            "status": "failed",
            "error": "Missing dependencies. Run: pip install requests beautifulsoup4"
        }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract and normalize all links
        links = []
        seen = set()
        
        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href', '').strip()
            if not href:
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Only include HTTP/HTTPS links
            parsed = urlparse(absolute_url)
            if parsed.scheme in ('http', 'https'):
                if absolute_url not in seen:
                    seen.add(absolute_url)
                    links.append(absolute_url)
                    
                    if len(links) >= max_links:
                        break
        
        return {
            "url": url,
            "links": links,
            "count": len(links),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "url": url,
            "links": [],
            "count": 0,
            "status": "failed",
            "error": str(e)
        }
