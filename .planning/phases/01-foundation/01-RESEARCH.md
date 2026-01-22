# Phase 1: Foundation - Research

**Researched:** 2026-01-18
**Domain:** LangGraph StateGraph, TypedDict State, Checkpointing, Node/Edge Definition
**Confidence:** HIGH

## Summary

Phase 1 establishes the foundational graph skeleton using LangGraph 1.0.6. The core requirements are:
1. A `StateGraph` with a `TypedDict` state schema
2. `InMemorySaver` checkpointer for state persistence
3. Named placeholder nodes with clear boundaries
4. START to END flow control

The research confirms that LangGraph's API is stable and well-documented. The key pattern is: define state as `TypedDict`, add nodes as functions returning partial state updates (plain `dict`), connect with edges using `START` and `END` constants, compile with a checkpointer, and invoke with a `thread_id` configuration.

**Primary recommendation:** Use `TypedDict` for internal state (lightweight, no runtime overhead), define reducers with `Annotated` for list fields, and return partial `dict` updates from nodes rather than full state objects.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.6 | Graph orchestration framework | Official LangChain framework for multi-agent workflows. Provides `StateGraph`, checkpointing, START/END constants. |
| langchain-core | 1.2.7 | Base abstractions (messages, types) | Minimal dependency providing core building blocks without full langchain overhead. |
| typing_extensions | latest | TypedDict, Annotated | Standard Python typing support for state schema definition. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| operator | stdlib | Reducer functions (add) | Use `operator.add` as reducer for list concatenation in state. |
| pydantic | 2.x | External validation | Only for API boundaries, not internal state. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TypedDict | Pydantic BaseModel | Pydantic adds validation overhead; use only at boundaries, not internal state. |
| InMemorySaver | PostgresSaver | PostgresSaver for production persistence; InMemorySaver is appropriate for pedagogical/development use. |

**Installation:**
```bash
pip install langgraph>=1.0.6 langchain-core>=1.2.7
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── graph/
│   ├── __init__.py
│   ├── state.py           # TypedDict state schema definition
│   ├── nodes.py           # Node function implementations
│   └── workflow.py        # Graph construction and compilation
├── main.py                # Entry point with invoke/stream logic
└── config.py              # Configuration (thread_id, etc.)
```

### Pattern 1: StateGraph with TypedDict State Schema

**What:** Define graph state using Python's `TypedDict` for type safety without runtime overhead.

**When to use:** Always for internal LangGraph state definitions.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api
from typing import TypedDict, Annotated
from typing_extensions import TypedDict
from operator import add

class ArticleState(TypedDict):
    """State schema for the pedagogical article writer."""
    topic: str | None
    approaches: list[dict] | None
    selected_approach_index: int | None
    current_draft: str | None
    critic_feedback: str | None
    is_approved: bool
    revision_count: int
    # Use Annotated with reducer for list fields that accumulate
    messages: Annotated[list, add]
```

### Pattern 2: Node Functions Returning Partial Updates

**What:** Nodes receive full state, return only the fields they want to update as a plain `dict`.

**When to use:** Every node function.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/use-graph-api
def placeholder_node(state: ArticleState) -> dict:
    """Placeholder node that passes through state unchanged.

    In Phase 1, this demonstrates node structure without business logic.
    """
    # Return partial update - LangGraph merges this into existing state
    return {}  # No changes, or return {"field": "new_value"} for updates

def topic_placeholder(state: ArticleState) -> dict:
    """Placeholder for topic input node."""
    # In later phases, this will use interrupt() for human input
    return {"topic": state.get("topic") or "placeholder topic"}
```

### Pattern 3: Graph Construction with START/END

**What:** Use `START` and `END` constants to define entry and exit points.

**When to use:** Every graph must have at least one edge from `START` and to `END`.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api
from langgraph.graph import StateGraph, START, END

def build_graph(state_class):
    """Construct the graph with placeholder nodes."""
    builder = StateGraph(state_class)

    # Add nodes
    builder.add_node("topic_input", topic_placeholder)
    builder.add_node("approach_agent", placeholder_node)
    builder.add_node("writer_agent", placeholder_node)
    builder.add_node("save_output", placeholder_node)

    # Define edges (linear flow for Phase 1)
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    builder.add_edge("approach_agent", "writer_agent")
    builder.add_edge("writer_agent", "save_output")
    builder.add_edge("save_output", END)

    return builder
```

### Pattern 4: Compilation with Checkpointer

**What:** Compile graph with `InMemorySaver` to enable state persistence across invocations.

**When to use:** Required for any human-in-the-loop or multi-turn interaction.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/add-memory
from langgraph.checkpoint.memory import InMemorySaver

def compile_graph(builder):
    """Compile graph with checkpointer for state persistence."""
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph
```

### Pattern 5: Invocation with Thread Configuration

**What:** Each invocation includes a `thread_id` in the config to maintain separate conversation states.

**When to use:** Every `invoke()` or `stream()` call.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/add-memory
def run_graph(graph, initial_state: dict, thread_id: str):
    """Run graph with thread-based persistence."""
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = graph.invoke(initial_state, config)
    return result
```

### Anti-Patterns to Avoid

- **Mutating state objects:** Never modify `state` directly. Always return a new `dict` with updates.
- **Forgetting checkpointer:** Without a checkpointer, `interrupt()` won't work in later phases.
- **Missing thread_id:** State won't persist correctly across invocations without unique thread identifiers.
- **Returning full state:** Nodes should return partial `dict`, not the full state object.
- **Using Pydantic for internal state:** Adds overhead; reserve for API boundaries only.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| State persistence | Custom file/DB storage | `InMemorySaver` / `PostgresSaver` | Handles checkpointing, thread management, time-travel debugging built-in |
| List field merging | Manual append logic | `Annotated[list, operator.add]` | Reducers handle merge automatically, works with parallel execution |
| Graph execution | Custom node sequencing | `StateGraph.compile().invoke()` | Handles edge routing, error recovery, streaming built-in |
| Entry/Exit points | Custom start/end logic | `START` / `END` constants | Standard pattern, works with visualization tools |

**Key insight:** LangGraph's abstractions (StateGraph, checkpointers, reducers) handle complex edge cases like parallel execution, state merging, and persistence that would be error-prone to implement manually.

## Common Pitfalls

### Pitfall 1: Missing Checkpointer for Human-in-the-Loop

**What goes wrong:** Graph compiles without checkpointer, but later phases using `interrupt()` fail because state can't be saved/restored.

**Why it happens:** Checkpointer seems optional in simple examples.

**How to avoid:** Always configure checkpointer in Phase 1, even for placeholder nodes.

**Warning signs:** Resume fails with "thread not found" errors in later phases.

### Pitfall 2: Mutating State Instead of Returning Updates

**What goes wrong:** Node modifies `state["field"]` directly instead of returning `{"field": new_value}`.

**Why it happens:** Python dicts are mutable; feels natural to modify in place.

**How to avoid:** Establish coding convention: nodes return `dict`, never modify input state.

**Warning signs:** Unexpected state values, issues with parallel execution.

### Pitfall 3: Not Setting Thread ID

**What goes wrong:** Multiple invocations overwrite each other's state because thread_id is missing or hardcoded.

**Why it happens:** Thread configuration seems boilerplate for simple tests.

**How to avoid:** Always pass unique `thread_id` in config. Use UUID for production, simple strings for testing.

**Warning signs:** State from previous runs unexpectedly persists or disappears.

### Pitfall 4: Forgetting END Edge

**What goes wrong:** Graph execution never terminates, or terminates unexpectedly.

**Why it happens:** Focus on node logic, forget to connect final node to END.

**How to avoid:** Always verify: one+ edge from START, one+ edge to END.

**Warning signs:** Graph hangs or `GraphRecursionError`.

## Code Examples

Verified patterns from official sources:

### Complete Minimal Graph (Phase 1 Target)

```python
# Source: Synthesized from https://docs.langchain.com/oss/python/langgraph/graph-api
#         and https://docs.langchain.com/oss/python/langgraph/add-memory

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


# 1. Define State Schema (FOUND-01)
class ArticleState(TypedDict):
    """State for the pedagogical article writer graph."""
    topic: str | None
    approaches: list[dict] | None
    selected_approach_index: int | None
    current_draft: str | None
    is_approved: bool
    revision_count: int


# 2. Define Placeholder Nodes (FOUND-03)
def topic_input_node(state: ArticleState) -> dict:
    """Placeholder for topic input. Will use interrupt() in Phase 2."""
    return {"topic": state.get("topic") or "Placeholder Topic"}


def approach_agent_node(state: ArticleState) -> dict:
    """Placeholder for approach generation. Will use LLM in Phase 2."""
    return {"approaches": [{"title": "Approach 1", "description": "Placeholder"}]}


def writer_agent_node(state: ArticleState) -> dict:
    """Placeholder for article writing. Will use LLM in Phase 3."""
    return {"current_draft": f"Draft about: {state.get('topic', 'unknown')}"}


def save_output_node(state: ArticleState) -> dict:
    """Placeholder for saving final output."""
    return {"is_approved": True}


# 3. Build Graph (FOUND-04)
def build_article_graph() -> StateGraph:
    """Construct the article writer graph with placeholder nodes."""
    builder = StateGraph(ArticleState)

    # Add nodes with names
    builder.add_node("topic_input", topic_input_node)
    builder.add_node("approach_agent", approach_agent_node)
    builder.add_node("writer_agent", writer_agent_node)
    builder.add_node("save_output", save_output_node)

    # Define linear flow: START -> topic -> approach -> writer -> save -> END
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    builder.add_edge("approach_agent", "writer_agent")
    builder.add_edge("writer_agent", "save_output")
    builder.add_edge("save_output", END)

    return builder


# 4. Compile with Checkpointer (FOUND-02)
def create_compiled_graph():
    """Create executable graph with persistence."""
    builder = build_article_graph()
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# 5. Execute with Thread Configuration
def main():
    """Demonstrate graph execution with state persistence."""
    graph = create_compiled_graph()

    # Thread configuration for persistence
    config = {"configurable": {"thread_id": "article-session-1"}}

    # Initial invocation
    initial_state = {
        "topic": None,
        "approaches": None,
        "selected_approach_index": None,
        "current_draft": None,
        "is_approved": False,
        "revision_count": 0,
    }

    result = graph.invoke(initial_state, config)

    print(f"Final state: {result}")
    print(f"Topic: {result['topic']}")
    print(f"Draft: {result['current_draft']}")
    print(f"Approved: {result['is_approved']}")


if __name__ == "__main__":
    main()
```

### Verification Tests

```python
# Source: Pattern from https://docs.langchain.com/oss/python/langgraph/graph-api

def test_graph_compiles():
    """Verify graph compiles without errors (Success Criteria 1)."""
    graph = create_compiled_graph()
    assert graph is not None


def test_state_flows_through_nodes():
    """Verify state flows through placeholder nodes (Success Criteria 2)."""
    graph = create_compiled_graph()
    config = {"configurable": {"thread_id": "test-1"}}

    result = graph.invoke({"topic": "Test Topic"}, config)

    assert result["topic"] == "Test Topic"
    assert result["approaches"] is not None
    assert result["current_draft"] is not None


def test_checkpointer_persists_state():
    """Verify state persists across invocations (Success Criteria 3)."""
    graph = create_compiled_graph()
    config = {"configurable": {"thread_id": "test-persist"}}

    # First invocation
    graph.invoke({"topic": "Persistence Test"}, config)

    # Get state from checkpointer
    state_snapshot = graph.get_state(config)
    assert state_snapshot.values["topic"] == "Persistence Test"


def test_start_to_end_flow():
    """Verify clear START to END flow (Success Criteria 4)."""
    graph = create_compiled_graph()
    config = {"configurable": {"thread_id": "test-flow"}}

    # Should complete without hanging
    result = graph.invoke({}, config)

    # Final node should have executed
    assert result["is_approved"] == True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `interrupt_before`/`interrupt_after` | `interrupt()` function | LangGraph 0.2.31 | Cleaner HITL pattern, use `interrupt()` exclusively |
| Conditional edges for all routing | `Command` for dynamic routing | LangGraph ~0.2.x | Nodes can specify their own routing via Command |
| `config_schema` parameter | `context_schema` parameter | LangGraph 0.6.0 | Use `context_schema` for run-scoped context |

**Deprecated/outdated:**
- `interrupt_before`/`interrupt_after` graph parameters: Use `interrupt()` function instead
- `NodeInterrupt` exception pattern: Use `interrupt()` function instead
- `config_schema` in StateGraph: Use `context_schema` instead (deprecated in v0.6.0)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact default initial state handling**
   - What we know: Nodes receive state dict, can use `.get()` for optional fields
   - What's unclear: Best practice for initializing all fields vs. letting them be None
   - Recommendation: Initialize all fields in initial_state dict passed to invoke()

2. **Graph visualization for verification**
   - What we know: LangGraph has visualization capabilities
   - What's unclear: Exact API for generating graph diagrams in 1.0.6
   - Recommendation: Use `graph.get_graph().draw_mermaid()` or similar if needed for debugging

## Sources

### Primary (HIGH confidence)
- [LangGraph Graph API Docs](https://docs.langchain.com/oss/python/langgraph/graph-api) - StateGraph, add_node, add_edge, compile
- [LangGraph Memory Docs](https://docs.langchain.com/oss/python/langgraph/add-memory) - InMemorySaver, thread_id configuration
- [LangGraph Graphs Reference](https://reference.langchain.com/python/langgraph/graphs/) - Method signatures, parameters
- [LangGraph PyPI](https://pypi.org/project/langgraph/) - Version 1.0.6 verified

### Secondary (MEDIUM confidence)
- [Type Safety in LangGraph](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to) - TypedDict vs Pydantic comparison
- [LangGraph State Management](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025) - Reducer patterns

### Tertiary (LOW confidence)
- [Medium articles on LangGraph](https://medium.com/@okanyenigun/built-with-langgraph-2-typing-dbe55e8bd39b) - Community examples (verify against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versions verified via PyPI, imports verified via official docs
- Architecture patterns: HIGH - Direct from official documentation with code examples
- Pitfalls: HIGH - Documented in PITFALLS.md and verified against official sources

**Research date:** 2026-01-18
**Valid until:** 2026-02-18 (30 days - LangGraph API is stable post-1.0)
