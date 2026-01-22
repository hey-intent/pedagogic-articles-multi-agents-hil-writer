"""Web search tool using Brave Search API.

This module provides a LangChain tool for searching the web using Brave's
Search API. The tool returns JSON-formatted results that can be used by
an LLM agent to research pedagogical approaches.
"""

import json
import time

from langchain_core.tools import tool

from src.config import config

# Retry configuration
MAX_RETRIES = 4
RETRY_DELAY = 1.0  # seconds


@tool
def web_search(query: str) -> str:
    """Search the web for educational resources and teaching approaches.

    Args:
        query: The search query to find relevant content about teaching methods,
               metaphors, or pedagogical approaches for a topic.

    Returns:
        JSON string with up to 5 search results, each containing title, url,
        and description.
    """
    import httpx

    api_key = config.brave_search_api_key
    if not api_key:
        return json.dumps({"error": "BRAVE_SEARCH_API_KEY not set"})

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": 5,
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = httpx.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("web", {}).get("results", [])

            simplified = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                }
                for r in results[:5]
            ]
            return json.dumps(simplified, indent=2)

        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {str(e)}"
            if e.response.status_code >= 500:
                # Retry on server errors
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            # Don't retry on client errors (4xx)
            return json.dumps({"error": last_error})
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = str(e)
            time.sleep(RETRY_DELAY * (attempt + 1))
            continue
        except Exception as e:
            return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Failed after {MAX_RETRIES} retries: {last_error}"})
