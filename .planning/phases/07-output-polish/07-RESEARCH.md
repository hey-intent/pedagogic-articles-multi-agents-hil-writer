# Phase 7: Output & Polish - Research

**Researched:** 2026-01-19
**Domain:** File Output, LangGraph Visualization, Code Documentation
**Confidence:** HIGH

## Summary

Phase 7 completes the pedagogical article writer by implementing file output, graph visualization, and code quality polish. This phase has three distinct objectives: (1) save the final article as a markdown file to disk, (2) generate a Mermaid diagram showing the workflow graph, and (3) ensure the codebase is clean, readable, and well-documented as a learning reference.

The implementation is straightforward since it builds on Python standard library (pathlib for file I/O) and LangGraph's built-in visualization capabilities (`get_graph().draw_mermaid()`). The file output is already stubbed in `save_output_node`, which currently just marks `is_approved=True`. The visualization can be generated either as Mermaid text (embeddable in markdown) or as PNG via the Mermaid.Ink API. Code quality involves adding explanatory comments highlighting LangGraph patterns for educational purposes.

No new dependencies are required. The existing `pathlib` (stdlib) handles file output with UTF-8 encoding, and `langgraph` provides `draw_mermaid()` and `draw_mermaid_png()` for visualization. The main work is implementing the save logic, adding a visualization output, and enhancing documentation.

**Primary recommendation:** Modify `save_output_node` to write the article to a markdown file using `pathlib.Path.write_text()` with explicit UTF-8 encoding. Generate Mermaid diagram text via `get_graph().draw_mermaid()` and include it in the output or write to a separate `.mmd` file. Enhance code comments to explain LangGraph concepts at key points (state schema, Command routing, interrupt patterns).

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib | File system operations | Python standard library since 3.4. Provides clean, object-oriented file handling with cross-platform support. |
| langgraph | 1.0.6 | Graph visualization | Already installed. Provides `get_graph().draw_mermaid()` for Mermaid diagram generation. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Timestamp generation | For timestamped output filenames or metadata in output files. |
| textwrap | stdlib | Text formatting | For formatting code comments or output headers if needed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pathlib.write_text()` | `open() with statement` | Both work; pathlib is more concise for simple writes. Use `open()` for streaming large files. |
| Mermaid text output | `draw_mermaid_png()` | PNG requires API call to Mermaid.Ink or pyppeteer dependency. Text is dependency-free and embeds in markdown. |
| Manual comments | Sphinx docstrings | Sphinx adds complexity. For a reference implementation, inline comments + good docstrings suffice. |

**Installation:**
```bash
# No new packages needed - all required libraries already installed or in stdlib
```

## Architecture Patterns

### Recommended Project Structure
```
src/
|-- graph/
|   |-- nodes/
|       |-- save_output.py    # MODIFY: Add file writing logic
src/
|-- main.py                   # MODIFY: Display file paths, add visualization output
output/                       # NEW: Directory for generated files
|-- article_YYYY-MM-DD_HH-MM.md    # Generated article files
|-- workflow_diagram.mmd      # Optional: Mermaid diagram source
```

### Pattern 1: File Output with Pathlib

**What:** Write the final article to a markdown file using pathlib for clean, cross-platform file handling.

**When to use:** Any time you need to persist output to the filesystem.

**Example:**
```python
# Source: Python stdlib pathlib + project pattern
from pathlib import Path
from datetime import datetime

def save_output_node(state: ArticleState) -> dict:
    """Save final article to markdown file and mark workflow complete.

    Creates an output directory (if needed) and writes the article with
    a timestamped filename for easy identification.

    Args:
        state: Current graph state containing the final approved draft.

    Returns:
        Dict with 'is_approved' set to True and 'output_path' with file location.
    """
    current_draft = state["current_draft"]
    topic = state["topic"]

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Generate timestamped filename
    # Sanitize topic for filename (replace spaces, remove special chars)
    safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:30])
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"article_{safe_topic}_{timestamp}.md"

    output_path = output_dir / filename

    # Write with explicit UTF-8 encoding for cross-platform compatibility
    output_path.write_text(current_draft, encoding="utf-8")

    return {
        "is_approved": True,
        "output_path": str(output_path),  # Store path in state for reference
    }
```

### Pattern 2: Mermaid Diagram Generation

**What:** Generate a Mermaid diagram showing the workflow graph structure.

**When to use:** For documentation, debugging, or educational purposes to visualize the graph.

**Example:**
```python
# Source: LangGraph docs + project pattern
from langgraph.graph import StateGraph

def generate_mermaid_diagram(graph) -> str:
    """Generate Mermaid diagram text from compiled graph.

    LangGraph's get_graph().draw_mermaid() returns the Mermaid syntax
    representing the graph structure with nodes and edges.

    Args:
        graph: Compiled LangGraph instance.

    Returns:
        String containing Mermaid diagram syntax.
    """
    return graph.get_graph().draw_mermaid()


def save_mermaid_diagram(graph, output_path: str = "output/workflow_diagram.mmd") -> str:
    """Save Mermaid diagram to file.

    Generates the Mermaid diagram and saves it to a .mmd file.
    The .mmd extension is standard for Mermaid source files.

    Args:
        graph: Compiled LangGraph instance.
        output_path: Path for the output file.

    Returns:
        Path to the saved diagram file.
    """
    from pathlib import Path

    mermaid_code = graph.get_graph().draw_mermaid()

    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(mermaid_code, encoding="utf-8")

    return str(output_file)
```

### Pattern 3: Embedding Mermaid in Markdown

**What:** Include the Mermaid diagram directly in the output markdown file.

**When to use:** When you want a self-contained output with both article and workflow visualization.

**Example:**
```python
# Source: Mermaid markdown syntax + project pattern
def create_article_with_diagram(article: str, mermaid_code: str, metadata: dict) -> str:
    """Create markdown output with article and workflow diagram.

    Combines the generated article with a Mermaid diagram showing the
    workflow that produced it. Many markdown renderers (GitHub, VSCode)
    support Mermaid code blocks natively.

    Args:
        article: The generated article content.
        mermaid_code: Mermaid diagram syntax from get_graph().draw_mermaid().
        metadata: Dict with topic, revisions, timestamp info.

    Returns:
        Complete markdown string with article and appendix.
    """
    return f"""{article}

---

## Appendix: Workflow

This article was generated using the following LangGraph workflow:

```mermaid
{mermaid_code}
```

**Metadata:**
- Topic: {metadata['topic']}
- Revisions: {metadata['revision_count']}
- Generated: {metadata['timestamp']}
"""
```

### Pattern 4: Educational Code Comments

**What:** Comments that explain LangGraph patterns for readers learning from the codebase.

**When to use:** Throughout the codebase, especially at key LangGraph integration points.

**Example:**
```python
# Source: Google Python Style Guide + project conventions
"""Approach agent node - generates pedagogical approaches using LLM with tools.

This module demonstrates the inline tool-calling loop pattern in LangGraph.
Rather than using a subgraph (like create_react_agent), it runs the tool
loop directly within the node. This simpler approach works well for
single-purpose agents that don't need complex state management.

Key LangGraph Concepts Demonstrated:
- bind_tools(): Enables an LLM to request tool calls in its response
- with_structured_output(): Forces LLM to return a validated Pydantic model
- Tool message pattern: ToolMessage links results to their tool_call_id
"""

# --- Inside function ---

# LangGraph Pattern: State is immutable between nodes.
# We receive the full state but ONLY return fields we want to update.
# The graph automatically merges our return dict into the existing state.
topic = state["topic"]  # Read from state
return {"approaches": approaches}  # Return only what changed
```

### Anti-Patterns to Avoid

- **Hardcoded output paths:** Use configurable paths or generate from topic/timestamp. Hardcoded paths overwrite previous outputs.
- **Missing UTF-8 encoding:** Always specify `encoding="utf-8"` to prevent platform-specific encoding issues.
- **PNG generation without fallback:** `draw_mermaid_png()` requires an API call or pyppeteer. Text-based Mermaid is safer for a reference implementation.
- **Over-commenting obvious code:** Comments should explain WHY or explain LangGraph patterns, not describe what code does line-by-line.
- **Mutating state in save_output:** Return new dict with `output_path`, don't modify the input state.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File path handling | String concatenation | `pathlib.Path` | Cross-platform, handles edge cases (slashes, encoding) |
| Filename sanitization | Regex | Simple char filter | Regex is overkill; `isalnum()` filter is readable and sufficient |
| Graph visualization | Manual DOT/graph | `get_graph().draw_mermaid()` | Built into LangGraph, generates valid Mermaid syntax |
| Timestamp formatting | Manual string building | `datetime.strftime()` | Standard, locale-aware, well-tested |
| Directory creation | `os.makedirs` | `Path.mkdir(parents=True, exist_ok=True)` | Cleaner API, handles existing directories |

**Key insight:** Phase 7 is about polishing an existing working implementation. The file I/O and visualization are solved problems - use standard library and LangGraph built-ins.

## Common Pitfalls

### Pitfall 1: Filename Collisions

**What goes wrong:** Running twice in the same second overwrites the previous output file.

**Why it happens:** Timestamp resolution is only to the minute/second.

**How to avoid:** Include more resolution (seconds or milliseconds) or append a short UUID. Or accept that same-second runs overwrite.

**Warning signs:** "Where did my previous output go?" complaints.

### Pitfall 2: Platform-Specific Path Issues

**What goes wrong:** Code works on Linux but fails on Windows (or vice versa).

**Why it happens:** Using `/` hardcoded in strings, or not specifying encoding.

**How to avoid:** Always use `pathlib.Path` for paths, always specify `encoding="utf-8"` for text files.

**Warning signs:** `UnicodeEncodeError` or `FileNotFoundError` only on specific platforms.

### Pitfall 3: Missing Output Directory

**What goes wrong:** `FileNotFoundError` when writing to `output/article.md`.

**Why it happens:** The `output/` directory doesn't exist on first run.

**How to avoid:** Always call `path.parent.mkdir(parents=True, exist_ok=True)` before writing.

**Warning signs:** Works on dev machine (directory exists) but fails in CI or fresh clone.

### Pitfall 4: State Field Not Added

**What goes wrong:** Wanting to store `output_path` in state but getting `KeyError`.

**Why it happens:** New field not added to `ArticleState` TypedDict.

**How to avoid:** Add any new state fields to the TypedDict definition before using them.

**Warning signs:** `KeyError: 'output_path'` when accessing final state.

### Pitfall 5: Comments Explaining WHAT Not WHY

**What goes wrong:** Comments describe obvious code ("increment counter by 1") rather than purpose.

**Why it happens:** Habit of commenting everything without considering value.

**How to avoid:** Focus comments on:
  - LangGraph patterns (for educational value)
  - Business logic decisions (why this threshold?)
  - Non-obvious implications (why immutable state matters)

**Warning signs:** Comments are longer than code, say the same thing as code.

## Code Examples

Verified patterns from official sources and established project conventions:

### Complete save_output_node Implementation

```python
# Source: Synthesized from project patterns + pathlib best practices
# File: src/graph/nodes/save_output.py
"""Save output node - writes final article to markdown file.

This node handles the terminal step of the workflow: persisting the
approved article to disk. It demonstrates simple file I/O patterns
that are suitable for a reference implementation.

Key Concepts:
- Uses pathlib for cross-platform path handling
- Explicit UTF-8 encoding for text files
- Timestamped filenames to prevent overwrites
"""

from datetime import datetime
from pathlib import Path

from src.graph.state import ArticleState


def save_output_node(state: ArticleState) -> dict:
    """Save final article to markdown file and mark workflow complete.

    This terminal node writes the approved article to the output directory
    with a timestamped filename. It also stores the output path in state
    for reference by the caller.

    Output files are saved to: output/article_{topic}_{timestamp}.md

    Args:
        state: Current graph state containing:
            - current_draft: The approved article content
            - topic: The article topic (used in filename)

    Returns:
        Dict with:
            - is_approved: True (marks workflow complete)
            - output_path: Path to the saved markdown file
    """
    current_draft = state["current_draft"]
    topic = state["topic"]

    # Create output directory if it doesn't exist
    # exist_ok=True prevents error if directory already exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Generate safe filename from topic
    # Replace any non-alphanumeric characters with underscore
    safe_topic = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in topic[:30]
    ).strip("_")

    # Timestamp for uniqueness (resolution to minute)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"article_{safe_topic}_{timestamp}.md"

    output_path = output_dir / filename

    # Write with explicit UTF-8 encoding
    # This ensures consistent behavior across Windows/Linux/Mac
    output_path.write_text(current_draft, encoding="utf-8")

    return {
        "is_approved": True,
        "output_path": str(output_path),
    }
```

### Updated State Schema with output_path

```python
# Source: Existing pattern from state.py
# File: src/graph/state.py (modification)
from typing_extensions import TypedDict


class ArticleState(TypedDict):
    """State schema for the pedagogical article writer workflow.

    Phase 7 addition:
    - output_path: Path where the final article was saved
    """

    topic: str | None
    approaches: list[dict] | None
    selected_approach_index: int | None
    rejected_approaches: list[dict] | None
    current_draft: str | None
    critic_feedback: str | None
    is_approved: bool
    revision_count: int
    output_path: str | None  # NEW: Path to saved article file
```

### Mermaid Diagram Generation in main.py

```python
# Source: LangGraph visualization docs
# File: src/main.py (addition to main function)

def save_workflow_diagram(graph, output_path: str = "output/workflow_diagram.mmd"):
    """Save workflow diagram as Mermaid source file.

    Generates a Mermaid diagram showing the graph structure.
    The .mmd file can be:
    - Viewed at mermaid.live
    - Rendered in GitHub markdown
    - Rendered in VSCode with Mermaid extension

    Args:
        graph: Compiled LangGraph instance.
        output_path: Path for the output file.

    Returns:
        Path to the saved diagram file.
    """
    from pathlib import Path

    mermaid_code = graph.get_graph().draw_mermaid()

    output_file = Path(output_path)
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(mermaid_code, encoding="utf-8")

    return str(output_file)


# In main() function, after workflow completes:
def main():
    # ... existing code ...

    # After workflow completes, save diagram
    diagram_path = save_workflow_diagram(graph)
    print(f"\nWorkflow diagram saved to: {diagram_path}")
    print(f"View at: https://mermaid.live or in VSCode with Mermaid extension")

    # Show output file location
    if result.get("output_path"):
        print(f"Article saved to: {result['output_path']}")
```

### Enhanced Module Documentation Example

```python
# Source: Google Python Style Guide + project conventions
# File: src/graph/workflow.py (enhanced documentation)
"""Graph construction and compilation for the Pedagogical Article Writer.

This module provides functions to build and compile the LangGraph workflow.
The graph defines the sequence of nodes and edges that form the article
writing pipeline.

Key LangGraph Concepts Demonstrated
===================================

StateGraph
    The graph builder that takes a state schema (ArticleState TypedDict).
    Nodes are added with `add_node()`, edges with `add_edge()`.

START/END
    Special constants marking graph entry and exit points.
    Every graph must have at least one path from START to END.

Nodes
    Functions that receive full state and return partial updates.
    They NEVER mutate state directly - LangGraph handles merging.

Command Routing
    Nodes can return `Command(goto="node_name")` for dynamic routing.
    This replaces rigid conditional edges with node-controlled flow.
    Used by: approach_selection_node, critic_agent_node

InMemorySaver
    Checkpointer that persists state for HITL workflows.
    Required for interrupt/resume patterns to work.
    Thread ID identifies which state to resume.

Workflow Structure
==================

The workflow has two HITL interrupts and one reflection loop:

    START -> topic_input(HITL) -> approach_agent -> approach_selection(HITL)
                                                           |
                        +----------------------------------+
                        |
                        v
                   writer_agent <--+
                        |          |
                        v          | (revision)
                   critic_agent ---+
                        |
                        v (approved)
                   save_output -> END

See Also
--------
- src/graph/state.py: State schema definition
- src/graph/nodes/: Node implementations
- LangGraph docs: https://docs.langchain.com/langgraph
"""
```

### Educational Comment Examples for Key Patterns

```python
# Source: Project conventions
# Example comments to add throughout codebase for CODE-02

# --- In topic_input.py ---
def topic_input_node(state: ArticleState) -> dict:
    """Pause for user topic input via LangGraph interrupt.

    LangGraph Pattern: interrupt() for Human-in-the-Loop
    ====================================================
    The interrupt() function pauses graph execution and returns control
    to the caller. The caller then provides input via Command(resume=value),
    which becomes the return value of interrupt().

    This pattern requires:
    - A checkpointer (InMemorySaver) to persist state during pause
    - A thread_id to identify which paused state to resume

    Flow:
    1. graph.invoke({}) -> hits interrupt() -> returns with __interrupt__
    2. graph.invoke(Command(resume="topic")) -> interrupt() returns "topic"
    3. Node continues, returns {"topic": "topic"}
    """
    user_topic = interrupt("Please provide a topic for the article:")
    return {"topic": user_topic}


# --- In approach_selection.py ---
def approach_selection_node(state: ArticleState):
    """Handle approach selection or rejection via Command routing.

    LangGraph Pattern: Command for Dynamic Routing
    ==============================================
    Command(goto="node_name") lets a node control where the graph
    goes next, instead of relying on fixed edges. This is powerful
    for conditional flows like:
    - User selects approach -> go to writer
    - User rejects approaches -> go back to approach_agent

    The Command return type annotation is REQUIRED:
    - `Command[Literal["writer_agent", "approach_agent"]]`
    - This tells LangGraph which nodes are valid destinations
    - Graph compilation fails if annotation is missing

    Note: No explicit edge FROM this node is needed in build_graph()
    because Command handles routing dynamically.
    """
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.path.join()` for paths | `pathlib.Path` / operator | Python 3.4+ (widespread adoption ~2020) | Cleaner code, cross-platform by default |
| `open()` for all file I/O | `Path.write_text()` for simple writes | Python 3.5+ | More concise for common cases |
| Manual graph drawing | `get_graph().draw_mermaid()` | LangGraph 0.2+ | Built-in visualization support |
| PNG-only visualization | Mermaid text (embeddable in markdown) | Current best practice | No external dependencies, GitHub renders natively |

**Deprecated/outdated:**
- **`os.makedirs()` with manual exist check:** Use `Path.mkdir(exist_ok=True)` instead.
- **`draw_mermaid_png()` with pyppeteer:** Requires extra dependency and has known issues. Use text-based Mermaid for simplicity.
- **Explicit file close:** Always use context managers (`with`) or `write_text()`. Never rely on explicit `close()`.

## Open Questions

Things that couldn't be fully resolved:

1. **Output filename format**
   - What we know: Need timestamped, topic-based filename
   - What's unclear: Exact format preference (with or without seconds? UUID suffix?)
   - Recommendation: Use `article_{topic}_{YYYY-MM-DD_HH-MM}.md` - readable and unique enough for learning context

2. **Mermaid diagram location**
   - What we know: Can embed in article markdown or save as separate file
   - What's unclear: Whether to embed in article or keep separate
   - Recommendation: Save as separate `.mmd` file for cleanliness. The article is the main output.

3. **State field for output_path**
   - What we know: Useful to have path in final state for main.py to display
   - What's unclear: Whether to add to TypedDict (structural change) or just print directly
   - Recommendation: Add `output_path: str | None` to state - clean pattern, useful for testing

4. **Comment density for educational purposes**
   - What we know: CODE-02 requires comments explaining LangGraph patterns
   - What's unclear: How many comments is "educational" vs "noisy"
   - Recommendation: Focus on module docstrings + key pattern comments. Don't comment obvious code.

## Sources

### Primary (HIGH confidence)
- [LangGraph Visualization Docs](https://docs.langchain.com/oss/python/langgraph/use-graph-api) - `get_graph()`, `draw_mermaid()` methods
- [Python pathlib Module](https://realpython.com/python-pathlib/) - File handling best practices
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) - Docstring format, comment guidelines
- Project codebase - Established patterns for nodes, state, file structure

### Secondary (MEDIUM confidence)
- [LangGraph Visualization with get_graph](https://medium.com/@josephamyexson/langgraph-visualization-with-get-graph-ffa45366d6cb) - Practical visualization examples
- [Python File Handling with Pathlib](https://dev.to/emmimal_alexander_3be8cc7/python-file-handling-mastery-ditch-common-pitfalls-with-pathlib-context-managers-2em4) - UTF-8 encoding, cross-platform tips
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/) - Comment conventions

### Tertiary (LOW confidence)
- WebSearch results on markdown file writing - Community patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using stdlib (pathlib) and already-installed langgraph
- File output patterns: HIGH - Python pathlib is well-documented, patterns are established
- Visualization: HIGH - LangGraph's draw_mermaid() is built-in and documented
- Code quality guidelines: MEDIUM - Educational comment style is somewhat subjective
- Specific filename format: MEDIUM - Convention choice, not a technical constraint

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - stdlib and LangGraph visualization APIs are stable)
