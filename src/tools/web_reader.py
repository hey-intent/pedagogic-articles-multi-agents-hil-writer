"""Web page content extraction tool.

This module provides a LangChain tool for fetching and extracting text content
from web pages. The tool uses httpx for HTTP requests and BeautifulSoup for
HTML parsing, removing non-content elements and truncating to fit token limits.
"""

from langchain_core.tools import tool


@tool
def read_webpage(url: str) -> str:
    """Read and extract the main text content from a web page.

    Args:
        url: The full URL of the web page to read.

    Returns:
        The extracted text content, truncated to 4000 characters.
        Returns an error message if the page cannot be read.
    """
    import httpx
    from bs4 import BeautifulSoup

    try:
        response = httpx.get(
            url,
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PedagogicalBot/1.0)"},
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Extract text with newlines between blocks
        text = soup.get_text(separator="\n", strip=True)

        # Truncate to fit token limits
        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated...]"

        return text

    except httpx.TimeoutException:
        return f"Error: Timeout reading {url}"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:
        return f"Error reading {url}: {str(e)}"
