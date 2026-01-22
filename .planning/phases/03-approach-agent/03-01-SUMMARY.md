---
phase: 03-approach-agent
plan: 01
subsystem: tools
tags: [web-search, brave-api, httpx, beautifulsoup, pydantic, langchain-tools]
dependency-graph:
  requires: [01-foundation]
  provides: [web_search-tool, read_webpage-tool, approach-schemas]
  affects: [03-02-approach-node]
tech-stack:
  added: [langchain-anthropic, httpx, beautifulsoup4]
  patterns: [@tool-decorator, pydantic-structured-output, graceful-error-handling]
key-files:
  created:
    - src/tools/__init__.py
    - src/tools/web_search.py
    - src/tools/web_reader.py
    - src/schemas/__init__.py
    - src/schemas/approaches.py
    - .env.example
    - tests/test_tools.py
  modified:
    - requirements.txt
decisions: []
metrics:
  duration: 4 min
  completed: 2026-01-19
---

# Phase 03 Plan 01: Web Tools and Schemas Summary

**One-liner:** Brave Search API tool, web reader with BeautifulSoup, Pydantic schemas enforcing exactly 3 approaches

## What Was Built

### 1. Web Search Tool (`src/tools/web_search.py`)

LangChain `@tool`-decorated function that searches the web using Brave Search API:
- Accepts a query string, returns JSON with up to 5 results
- Each result contains title, url, and description
- Handles missing API key gracefully (returns error JSON)
- Uses httpx with 10-second timeout
- Catches HTTPStatusError and general exceptions

```python
@tool
def web_search(query: str) -> str:
    """Search the web for educational resources and teaching approaches."""
    # Returns JSON: [{"title": "...", "url": "...", "description": "..."}]
```

### 2. Web Page Reader Tool (`src/tools/web_reader.py`)

LangChain `@tool`-decorated function that extracts text from web pages:
- Fetches URL with httpx, follows redirects
- Parses HTML with BeautifulSoup
- Removes script, style, nav, footer, header, aside elements
- Truncates to 4000 characters to fit token limits
- Handles timeout and HTTP errors gracefully

```python
@tool
def read_webpage(url: str) -> str:
    """Read and extract the main text content from a web page."""
    # Returns extracted text, truncated to 4000 chars
```

### 3. Approach Schemas (`src/schemas/approaches.py`)

Pydantic models for structured LLM output:
- `PedagogicalApproach`: title, description, metaphor, why_effective
- `ApproachList`: list of exactly 3 approaches (min_length=3, max_length=3)

```python
class ApproachList(BaseModel):
    approaches: list[PedagogicalApproach] = Field(
        min_length=3, max_length=3
    )
```

### 4. Test Coverage

10 unit tests covering:
- Tool decorator verification (invoke method exists)
- Error handling for missing API key and timeouts
- JSON response format validation
- HTML element removal
- Content truncation
- Pydantic validation for exactly 3 approaches

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 1eafc31 | feat | Create web tools module |
| 7245066 | feat | Create Pydantic schemas for structured output |
| 2d8e004 | test | Add unit tests for tools and schemas |

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

None - all implementation details followed the research document patterns exactly.

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| langchain-anthropic | >=0.3.0 | ChatAnthropic with tool calling |
| httpx | >=0.27.0 | HTTP requests for web tools |
| beautifulsoup4 | >=4.12.0 | HTML parsing for web reader |

## Environment Variables Required

Added `.env.example` documenting:
- `BRAVE_SEARCH_API_KEY` - For web search tool
- `ANTHROPIC_API_KEY` - For LLM operations

## Next Phase Readiness

Plan 03-02 can now implement the approach agent node using:
- `web_search` and `read_webpage` tools from `src/tools`
- `ApproachList` schema for structured output from `src/schemas`
- Pattern: `ChatAnthropic.bind_tools()` + inline tool loop + `with_structured_output()`

All building blocks are tested and ready for integration.
