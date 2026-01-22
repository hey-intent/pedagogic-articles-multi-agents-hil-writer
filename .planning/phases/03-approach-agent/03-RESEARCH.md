# Phase 3: Approach Agent - Research

**Researched:** 2026-01-19
**Domain:** LangGraph Tool Calling, Brave Search API, Custom Tools, ReAct Agent Patterns, Structured Output
**Confidence:** HIGH

## Summary

Phase 3 transforms the placeholder `approach_agent_node` into an LLM-powered agent that generates 3 pedagogical approaches with metaphors. The agent uses two custom tools: (1) a web search tool using Brave Search API to discover existing pedagogical resources, and (2) a web page reader tool using httpx/BeautifulSoup to fetch and extract content from URLs returned by search.

The research confirms two viable architectures for integrating the agent into the existing StateGraph:

**Option A (Recommended): Inline Tool-Calling Loop** - Keep the agent as a single node that runs an internal tool-calling loop. The node receives state, calls the LLM with tools bound, executes any tool calls, feeds results back to the LLM, and repeats until the LLM returns structured output (3 approaches). This fits cleanly with the existing linear graph flow.

**Option B: Subgraph Integration** - Use `create_react_agent` as a subgraph invoked from within the `approach_agent_node`. This provides more modularity but requires state transformation between parent and subgraph schemas.

The standard stack for tools is LangChain's `@tool` decorator for simple function-based tools, with `ChatAnthropic` (from `langchain-anthropic`) providing tool-calling capabilities. For structured output (exactly 3 approaches), use `with_structured_output()` to bind a Pydantic model that validates the agent's final response.

**Primary recommendation:** Implement Option A (inline tool-calling loop) within `approach_agent_node`. Define tools as decorated functions in a new `src/tools/` module. Use `ChatAnthropic.bind_tools()` for tool calling and `ChatAnthropic.with_structured_output()` for the final structured response containing exactly 3 approaches.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-anthropic | latest | LLM with tool calling | Provides `ChatAnthropic` with native tool calling via `bind_tools()` and structured output via `with_structured_output()`. |
| langchain-core | 1.2.7 | Tool abstractions | Provides `@tool` decorator, `BaseTool`, `ToolMessage`, `AIMessage` classes. Already installed. |
| httpx | latest | HTTP client for web fetching | Async-capable, modern HTTP client for fetching web pages. |
| beautifulsoup4 | latest | HTML parsing | Extract text content from HTML pages returned by httpx. |
| pydantic | 2.x | Structured output schema | Define `ApproachList` model for validating agent's structured response. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| brave-search-python-client | 0.4.27+ | Brave Search API client | Alternative to direct API calls; provides typed interface. |
| python-dotenv | 1.0.0 | Environment variables | Load BRAVE_SEARCH_API_KEY from .env file. Already installed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Brave Search API | Tavily Search | Tavily is more LLM-optimized but Brave is free tier friendly (2000/month) |
| httpx + BeautifulSoup | LangChain WebBaseLoader | WebBaseLoader is higher-level but less control; httpx is simple and sufficient |
| Inline tool loop | create_react_agent subgraph | Subgraph adds modularity but requires state transformation; inline is simpler |
| ChatAnthropic | ChatOpenAI | Both support tool calling; Anthropic chosen for consistency with project |

**Installation:**
```bash
pip install langchain-anthropic httpx beautifulsoup4
# Optional: pip install brave-search-python-client
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── graph/
│   ├── __init__.py
│   ├── state.py           # ArticleState TypedDict (already exists)
│   ├── nodes.py           # approach_agent_node implementation
│   └── workflow.py        # No changes needed
├── tools/
│   ├── __init__.py
│   ├── web_search.py      # Brave Search API tool
│   └── web_reader.py      # Web page reader tool
├── schemas/
│   ├── __init__.py
│   └── approaches.py      # Pydantic models for approach output
└── main.py                # Entry point
tests/
├── test_graph.py          # Existing tests
├── test_tools.py          # Tool unit tests
└── test_approach_agent.py # Agent integration tests
```

### Pattern 1: Custom Tool with @tool Decorator

**What:** Define tools as decorated functions that the LLM can call.

**When to use:** For simple, stateless operations like API calls.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langchain/tools
from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web for pedagogical resources and teaching approaches.

    Args:
        query: The search query to find relevant educational content.

    Returns:
        JSON string containing search results with titles, URLs, and descriptions.
    """
    import os
    import httpx
    import json

    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": 5}

    response = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers=headers,
        params=params,
    )
    response.raise_for_status()

    results = response.json().get("web", {}).get("results", [])
    simplified = [
        {"title": r["title"], "url": r["url"], "description": r.get("description", "")}
        for r in results[:5]
    ]
    return json.dumps(simplified, indent=2)
```

### Pattern 2: Web Page Reader Tool

**What:** Fetch and extract text content from a URL.

**When to use:** After web search returns URLs to read for detailed content.

**Example:**
```python
# Source: https://brightdata.com/blog/web-data/web-scraping-with-httpx
from langchain_core.tools import tool


@tool
def read_webpage(url: str) -> str:
    """Read and extract text content from a web page.

    Args:
        url: The URL of the web page to read.

    Returns:
        The main text content extracted from the page, truncated to 4000 characters.
    """
    import httpx
    from bs4 import BeautifulSoup

    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Truncate to avoid token limits
        return text[:4000]
    except Exception as e:
        return f"Error reading page: {str(e)}"
```

### Pattern 3: Structured Output Schema with Pydantic

**What:** Define Pydantic models to enforce the exact structure of agent output.

**When to use:** When the agent must return data in a specific format (3 approaches with metaphors).

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langchain/structured-output
from pydantic import BaseModel, Field


class PedagogicalApproach(BaseModel):
    """A single pedagogical approach with metaphor."""

    title: str = Field(description="A concise title for this approach")
    description: str = Field(description="2-3 sentences explaining the approach")
    metaphor: str = Field(description="A concrete metaphor or analogy to make the concept intuitive")
    why_effective: str = Field(description="Why this approach works for teaching the topic")


class ApproachList(BaseModel):
    """Exactly 3 pedagogical approaches for teaching a topic."""

    approaches: list[PedagogicalApproach] = Field(
        description="Exactly 3 distinct pedagogical approaches",
        min_length=3,
        max_length=3,
    )
```

### Pattern 4: Inline Tool-Calling Loop in Node

**What:** Run a ReAct-style loop within a single node, handling tool calls internally.

**When to use:** When integrating an agent into an existing StateGraph without subgraphs.

**Example:**
```python
# Source: Synthesized from https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.graph.state import ArticleState
from src.tools.web_search import web_search
from src.tools.web_reader import read_webpage
from src.schemas.approaches import ApproachList


APPROACH_SYSTEM_PROMPT = """You are a pedagogical expert who creates teaching approaches.
Given a topic, research existing educational resources and create exactly 3 distinct
pedagogical approaches, each with a unique metaphor or analogy.

Use the web_search tool to find relevant teaching resources.
Use the read_webpage tool to read promising pages for detailed content.

After researching, provide your final answer with exactly 3 approaches."""


def approach_agent_node(state: ArticleState) -> dict:
    """Generate 3 pedagogical approaches using LLM with web search tools.

    This node implements an inline tool-calling loop:
    1. Initialize LLM with tools bound
    2. Send topic to LLM
    3. If LLM returns tool calls, execute them and feed results back
    4. Repeat until LLM provides final structured output
    5. Return approaches to state
    """
    topic = state["topic"]
    tools = [web_search, read_webpage]

    # LLM with tools for research phase
    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    model_with_tools = model.bind_tools(tools)

    # LLM with structured output for final response
    model_structured = model.with_structured_output(ApproachList)

    messages = [
        {"role": "system", "content": APPROACH_SYSTEM_PROMPT},
        {"role": "user", "content": f"Create 3 pedagogical approaches for teaching: {topic}"},
    ]

    # Tool-calling loop (max iterations to prevent infinite loops)
    max_iterations = 10
    for _ in range(max_iterations):
        response = model_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # No more tool calls - get structured final output
            break

        # Execute tool calls
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name == "web_search":
                result = web_search.invoke(tool_args)
            elif tool_name == "read_webpage":
                result = read_webpage.invoke(tool_args)
            else:
                result = f"Unknown tool: {tool_name}"

            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
            ))

    # Get structured output
    final_prompt = messages + [
        {"role": "user", "content": "Now provide exactly 3 pedagogical approaches based on your research."}
    ]
    structured_response = model_structured.invoke(final_prompt)

    # Convert to list of dicts for state
    approaches = [
        {
            "title": a.title,
            "description": a.description,
            "metaphor": a.metaphor,
            "why_effective": a.why_effective,
        }
        for a in structured_response.approaches
    ]

    return {"approaches": approaches}
```

### Pattern 5: Testing with Mock LLM

**What:** Use `GenericFakeChatModel` to test agent logic without real API calls.

**When to use:** Unit tests for agent behavior.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langchain/test
from langchain_core.messages import AIMessage, ToolCall
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel


def test_approach_agent_calls_tools():
    """Verify agent uses tools before returning approaches."""
    # Mock LLM that returns tool call first, then final response
    mock_responses = [
        AIMessage(content="", tool_calls=[
            ToolCall(name="web_search", args={"query": "teaching quantum computing"}, id="1")
        ]),
        AIMessage(content="Based on my research, here are 3 approaches..."),
    ]
    mock_model = GenericFakeChatModel(messages=iter(mock_responses))

    # ... test logic with mock_model
```

### Anti-Patterns to Avoid

- **Hardcoding API keys:** Use environment variables via `os.environ` or `python-dotenv`.
- **Unbounded tool loops:** Always set a max_iterations limit to prevent infinite loops.
- **Ignoring tool errors:** Wrap tool execution in try/except and return error messages to LLM.
- **Not truncating web content:** Web pages can be huge; always truncate to fit token limits.
- **Using subgraphs unnecessarily:** Inline tool loops are simpler for single-purpose agents.
- **Skipping structured output validation:** Always use Pydantic to enforce exactly 3 approaches.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool definition | Custom JSON schema generation | `@tool` decorator | Auto-generates schema from function signature and docstring |
| Tool call routing | Manual if/else dispatch | `tool.invoke(args)` on tool objects | Type-safe invocation with error handling |
| Structured output | Regex/JSON parsing | `model.with_structured_output(Pydantic)` | Validates output, returns typed objects |
| Web search | Custom HTTP to Google | Brave Search API | Free tier (2000/month), no scraping required |
| HTML to text | Manual tag stripping | BeautifulSoup `get_text()` | Handles edge cases, script removal |
| HTTP requests | urllib | httpx | Modern, async-capable, better error handling |

**Key insight:** LangChain's tool abstraction and structured output handle the complex type conversions between Python functions, JSON schemas, and LLM function calling. The `@tool` decorator is sufficient for most use cases.

## Common Pitfalls

### Pitfall 1: API Key Not Set

**What goes wrong:** Brave Search API returns 401 Unauthorized.

**Why it happens:** `BRAVE_SEARCH_API_KEY` environment variable not set or not loaded.

**How to avoid:** Load `.env` file early with `load_dotenv()`. Check key exists before first API call.

**Warning signs:** 401 errors, empty search results.

### Pitfall 2: Token Limit Exceeded

**What goes wrong:** LLM returns error about context length exceeded.

**Why it happens:** Web page content is passed directly without truncation; multiple pages accumulate.

**How to avoid:** Truncate web content to 4000 chars max. Limit search results to 5. Cap tool iterations.

**Warning signs:** Context length errors, extremely slow responses.

### Pitfall 3: Tool Loop Never Terminates

**What goes wrong:** Agent keeps calling tools indefinitely.

**Why it happens:** LLM doesn't know when to stop or keeps finding more to research.

**How to avoid:** Set `max_iterations` (e.g., 10). Add explicit instruction in prompt to finish after initial research.

**Warning signs:** Timeouts, runaway API costs.

### Pitfall 4: Structured Output Validation Fails

**What goes wrong:** `with_structured_output` raises validation error.

**Why it happens:** LLM returns 2 or 4 approaches instead of exactly 3.

**How to avoid:** Use `min_length=3, max_length=3` in Pydantic field. Retry with clearer prompt if validation fails.

**Warning signs:** Pydantic validation errors, inconsistent approach counts.

### Pitfall 5: Tool Not Found in Responses

**What goes wrong:** `tool_call["name"]` doesn't match expected tool names.

**Why it happens:** Tool names are derived from function names unless explicitly set.

**How to avoid:** Use explicit `@tool("tool_name")` or verify function names match expected values.

**Warning signs:** KeyError on tool dispatch, "unknown tool" errors.

### Pitfall 6: httpx Timeout on Slow Pages

**What goes wrong:** `read_webpage` hangs or times out.

**Why it happens:** Some pages are slow to respond or very large.

**How to avoid:** Set explicit timeout (10s). Handle TimeoutException gracefully.

**Warning signs:** Hanging tests, timeout exceptions.

## Code Examples

Verified patterns from official sources:

### Complete Web Search Tool

```python
# Source: https://brave.com/search/api/
# File: src/tools/web_search.py
import json
import os
from langchain_core.tools import tool


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

    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
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
        return json.dumps({"error": f"HTTP {e.response.status_code}: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### Complete Web Reader Tool

```python
# Source: https://brightdata.com/blog/web-data/web-scraping-with-httpx
# File: src/tools/web_reader.py
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
```

### Approach Schema

```python
# Source: https://docs.langchain.com/oss/python/langchain/structured-output
# File: src/schemas/approaches.py
from pydantic import BaseModel, Field


class PedagogicalApproach(BaseModel):
    """A single pedagogical approach for teaching a topic."""

    title: str = Field(
        description="A concise, descriptive title for this teaching approach"
    )
    description: str = Field(
        description="2-3 sentences explaining how this approach teaches the topic"
    )
    metaphor: str = Field(
        description="A concrete metaphor or analogy that makes the concept intuitive. "
                    "Should relate the topic to something familiar and tangible."
    )
    why_effective: str = Field(
        description="1-2 sentences explaining why this approach is effective for learners"
    )


class ApproachList(BaseModel):
    """Container for exactly 3 pedagogical approaches."""

    approaches: list[PedagogicalApproach] = Field(
        description="Exactly 3 distinct pedagogical approaches for teaching the topic",
        min_length=3,
        max_length=3,
    )
```

### Environment Configuration

```python
# File: src/config.py
import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()

    config = {
        "brave_api_key": os.environ.get("BRAVE_SEARCH_API_KEY"),
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
    }

    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    return config
```

### Example .env File

```bash
# File: .env.example
BRAVE_SEARCH_API_KEY=your_brave_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `initialize_agent()` + `AgentExecutor` | `create_react_agent` or inline loops | LangGraph 1.0 | Simpler, more explicit control flow |
| Manual JSON schema for tools | `@tool` decorator auto-schema | LangChain 0.1 | Less boilerplate, docstrings become descriptions |
| Parsing LLM text for structure | `with_structured_output(Pydantic)` | LangChain 0.2 | Native function calling, typed responses |
| requests library | httpx | 2024 | Async support, better timeout handling |

**Deprecated/outdated:**
- `AgentExecutor`: Use LangGraph `create_react_agent` or custom StateGraph nodes instead
- `initialize_agent()`: Deprecated in favor of explicit graph construction
- `FakeLLM`: Use `GenericFakeChatModel` for testing tool-calling agents

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal max_iterations for tool loop**
   - What we know: Need a limit to prevent infinite loops
   - What's unclear: What's the typical number of iterations for good research
   - Recommendation: Start with 10; adjust based on testing

2. **Brave Search free tier reliability**
   - What we know: 2000 queries/month, 1 query/second limit
   - What's unclear: How it handles rate limiting (429 responses)
   - Recommendation: Add retry logic with backoff; mock for tests

3. **Handling tool call validation errors**
   - What we know: `with_structured_output` raises ValidationError if output doesn't match
   - What's unclear: Best retry strategy when LLM returns wrong number of approaches
   - Recommendation: Retry once with clearer prompt; fail gracefully if persists

4. **Web page reader for JavaScript-rendered pages**
   - What we know: httpx + BeautifulSoup only gets static HTML
   - What's unclear: How many educational pages need JS rendering
   - Recommendation: Start with static approach; add Playwright if needed later

## Sources

### Primary (HIGH confidence)
- [LangChain Tools Documentation](https://docs.langchain.com/oss/python/langchain/tools) - @tool decorator, BaseTool, tool calling patterns
- [LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output) - with_structured_output, Pydantic integration
- [LangGraph ReAct Agent from Scratch](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/) - Tool loop pattern, state management
- [Brave Search API Documentation](https://brave.com/search/api/) - Endpoints, authentication, rate limits
- [ChatAnthropic Documentation](https://docs.langchain.com/oss/python/integrations/chat/anthropic) - bind_tools, tool calling

### Secondary (MEDIUM confidence)
- [LangGraph ToolNode Reference](https://github.com/langchain-ai/langgraph/blob/main/libs/prebuilt/langgraph/prebuilt/tool_node.py) - ToolNode implementation patterns
- [httpx + BeautifulSoup Guide](https://brightdata.com/blog/web-data/web-scraping-with-httpx) - Web scraping patterns
- [LangChain Testing Guide](https://docs.langchain.com/oss/python/langchain/test) - GenericFakeChatModel, mock patterns

### Tertiary (LOW confidence)
- [brave-search-python-client](https://brave-search-python-client.readthedocs.io/) - Alternative client library (verify API compatibility)
- [Medium: Building ReAct Agents](https://medium.com/@umang91999/building-a-react-agent-with-langgraph-a-step-by-step-guide-812d02bafefa) - Community tutorial (verify against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official docs and PyPI
- Architecture patterns: HIGH - Inline tool loop pattern from official LangGraph how-to
- Tool implementation: HIGH - @tool decorator and httpx patterns well-documented
- Pitfalls: MEDIUM - Some edge cases (rate limiting, JS pages) need runtime validation

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - APIs and patterns are stable)
