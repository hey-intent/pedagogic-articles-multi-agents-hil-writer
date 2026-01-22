# Phase 4: Approach Selection (HITL) - Research

**Researched:** 2026-01-19
**Domain:** LangGraph Human-in-the-Loop, interrupt(), Command(resume=..., goto=...), Conditional Routing, State for Rejection Tracking
**Confidence:** HIGH

## Summary

Phase 4 implements the second human-in-the-loop interaction point where users select one of 3 generated approaches OR reject all to regenerate. This phase builds on the interrupt/resume patterns established in Phase 2 (topic input) and adds two new capabilities: (1) conditional routing based on user selection, and (2) passing rejected approaches back to the approach agent to avoid repetition.

The key insight is that LangGraph's `Command` object can combine state updates with routing decisions. When the user selects an approach, the node returns `Command(update={"selected_approach_index": idx}, goto="writer_agent")`. When they reject all, it returns `Command(update={"rejected_approaches": ...}, goto="approach_agent")`. This is cleaner than conditional edges because the selection logic lives in the node, not in edge definitions.

For rejected approach tracking, we add a `rejected_approaches` field to the state schema. This accumulates titles/summaries of rejected approaches across retries. The approach agent's prompt is modified to include these rejected approaches with a clear instruction: "Do not repeat these approaches." This ensures the agent generates fresh alternatives on retry.

**Primary recommendation:** Create an `approach_selection_node` that uses `interrupt()` to pause for user input, validates the input (index 1-3 or "reject"), and returns a `Command` with appropriate routing. Add `rejected_approaches: list[dict] | None` to ArticleState. Modify `approach_agent_node` to include rejected approaches in its prompt.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.6 | Graph orchestration with HITL | Provides `interrupt()`, `Command`, conditional routing. Already installed. |
| langgraph.types | (part of langgraph) | Type imports | Provides `interrupt`, `Command` classes for HITL patterns. |
| typing_extensions | latest | Literal type for Command annotations | Required for `Command[Literal["node_a", "node_b"]]` return type. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing | stdlib | Type hints | For Literal type annotation on Command return. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Command(goto=...)` | `add_conditional_edges()` | Conditional edges separate routing from logic; Command keeps it together. Command is cleaner for this use case. |
| `rejected_approaches` in state | Messages history | Messages would require parsing; dedicated field is explicit and easy to use in prompts. |
| Validation loop in node | Separate validation node | Loop in single node is simpler for simple validation (index 1-3 or "reject"). |

**Installation:**
```bash
# No new packages needed - langgraph already provides interrupt/Command
pip install langgraph>=1.0.6  # Already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/
|-- graph/
|   |-- __init__.py
|   |-- state.py           # Add rejected_approaches field
|   |-- nodes.py           # Add approach_selection_node, modify approach_agent_node
|   |-- workflow.py        # Update graph: add node, change edges to handle routing
|-- main.py                # Update to handle second interrupt/resume cycle
tests/
|-- test_graph.py          # Add tests for selection, rejection, loop back
```

### Pattern 1: Approach Selection with Conditional Routing

**What:** A node that uses `interrupt()` to pause, then routes based on user input.

**When to use:** When user input determines the next node in the graph.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api#combine-control-flow-and-state-updates-with-command
from typing import Literal
from langgraph.types import interrupt, Command
from src.graph.state import ArticleState


def approach_selection_node(state: ArticleState) -> Command[Literal["writer_agent", "approach_agent"]]:
    """Pause for user to select an approach or reject all.

    Presents the 3 generated approaches and waits for user input:
    - "1", "2", or "3" to select an approach
    - "reject" to reject all and regenerate

    Returns Command with:
    - update: selected_approach_index (if selection) or rejected_approaches (if rejection)
    - goto: "writer_agent" (if selection) or "approach_agent" (if rejection)
    """
    approaches = state["approaches"]

    # Build prompt showing the 3 approaches
    prompt = "Select an approach (1, 2, or 3) or type 'reject' to regenerate:\n\n"
    for i, approach in enumerate(approaches, 1):
        prompt += f"{i}. {approach['title']}\n"
        prompt += f"   Metaphor: {approach['metaphor']}\n\n"

    # Pause and wait for user input
    user_input = interrupt(prompt)

    # Validate and route
    if user_input.lower() == "reject":
        # Add current approaches to rejected list
        rejected = state.get("rejected_approaches") or []
        rejected = rejected + approaches  # Append current approaches
        return Command(
            update={"rejected_approaches": rejected},
            goto="approach_agent"
        )

    # Parse selection (expecting "1", "2", or "3")
    try:
        index = int(user_input) - 1  # Convert to 0-based
        if 0 <= index < 3:
            return Command(
                update={"selected_approach_index": index},
                goto="writer_agent"
            )
    except ValueError:
        pass

    # Invalid input - could re-interrupt with error message
    # For simplicity, treat as rejection (or implement validation loop)
    rejected = state.get("rejected_approaches") or []
    rejected = rejected + approaches
    return Command(
        update={"rejected_approaches": rejected},
        goto="approach_agent"
    )
```

### Pattern 2: Modified Approach Agent with Rejection Context

**What:** Modify the approach agent's prompt to include rejected approaches.

**When to use:** When the agent needs to avoid repeating previous outputs.

**Example:**
```python
# Source: Synthesized from LangGraph best practices
def approach_agent_node(state: ArticleState) -> dict:
    """Generate 3 pedagogical approaches, avoiding previously rejected ones."""
    topic = state["topic"]
    rejected = state.get("rejected_approaches") or []

    # Build system prompt with rejection context
    system_prompt = APPROACH_SYSTEM_PROMPT

    if rejected:
        system_prompt += "\n\nIMPORTANT: The user has rejected these approaches. "
        system_prompt += "Do NOT repeat them. Generate completely different approaches:\n"
        for r in rejected:
            system_prompt += f"- REJECTED: {r['title']} (metaphor: {r['metaphor']})\n"

    # ... rest of agent logic unchanged
```

### Pattern 3: Input Validation Loop

**What:** Re-interrupt with error message if user input is invalid.

**When to use:** When strict input validation is needed.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/interrupts
def approach_selection_node(state: ArticleState) -> Command[Literal["writer_agent", "approach_agent"]]:
    """Selection node with validation loop."""
    approaches = state["approaches"]

    prompt = build_selection_prompt(approaches)

    while True:
        user_input = interrupt(prompt)

        # Check for rejection
        if user_input.lower() == "reject":
            rejected = (state.get("rejected_approaches") or []) + approaches
            return Command(update={"rejected_approaches": rejected}, goto="approach_agent")

        # Check for valid selection
        try:
            index = int(user_input) - 1
            if 0 <= index < 3:
                return Command(update={"selected_approach_index": index}, goto="writer_agent")
        except ValueError:
            pass

        # Invalid - update prompt and re-interrupt
        prompt = f"Invalid input '{user_input}'. Please enter 1, 2, 3, or 'reject':\n\n"
        prompt += build_selection_prompt(approaches)
```

### Pattern 4: Workflow with Conditional Routing

**What:** Graph structure that supports routing from selection to either writer or approach agent.

**When to use:** When a node can route to multiple destinations.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api
from langgraph.graph import StateGraph, START, END

def build_graph() -> StateGraph:
    builder = StateGraph(ArticleState)

    # Add nodes
    builder.add_node("topic_input", topic_input_node)
    builder.add_node("approach_agent", approach_agent_node)
    builder.add_node("approach_selection", approach_selection_node)  # New node
    builder.add_node("writer_agent", writer_agent_node)
    builder.add_node("save_output", save_output_node)

    # Fixed edges
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    builder.add_edge("approach_agent", "approach_selection")  # Changed: agent -> selection
    # No edge from approach_selection - Command handles routing!
    builder.add_edge("writer_agent", "save_output")
    builder.add_edge("save_output", END)

    return builder
```

### Anti-Patterns to Avoid

- **Conditional edges for Command routing:** When using `Command(goto=...)`, don't also define conditional edges for that node. Command handles routing.
- **Forgetting type annotation:** `Command[Literal["node_a", "node_b"]]` return type is required for graph validation.
- **Complex resume values:** Keep resume values simple (string or int). Don't pass complex objects.
- **Mutating rejected list:** Use `rejected + approaches` (new list), not `rejected.append()` (mutation).
- **Missing default for new state field:** `rejected_approaches` should default to `None` or `[]` in state schema.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conditional routing based on input | Custom edge functions | `Command(goto=...)` | Built-in, type-safe, keeps logic in node |
| State updates with routing | Separate update then route | `Command(update=..., goto=...)` | Atomic operation, cleaner code |
| Input validation loop | External validation wrapper | `while True: interrupt(prompt)` | LangGraph supports re-interrupting from same node |
| Tracking rejected items | Messages parsing | Dedicated state field | Explicit, easy to use in prompts |

**Key insight:** The `Command` object is the modern LangGraph way to combine state updates and routing decisions. It eliminates the need for separate conditional edge functions and keeps related logic together.

## Common Pitfalls

### Pitfall 1: Missing Type Annotation on Command Return

**What goes wrong:** Graph compilation fails or graph visualization is incorrect.

**Why it happens:** LangGraph uses return type annotations to validate routing destinations.

**How to avoid:** Always annotate: `def my_node(state) -> Command[Literal["node_a", "node_b"]]:`

**Warning signs:** Type errors, unexpected "node not found" errors.

### Pitfall 2: Routing to Non-Existent Node

**What goes wrong:** Runtime error when Command tries to route to a node that doesn't exist.

**Why it happens:** Typo in node name or forgot to add node to graph.

**How to avoid:** Use Literal type annotation (catches typos at type-check time). Verify node names match graph.add_node calls.

**Warning signs:** "Node not found" errors at runtime.

### Pitfall 3: State Collision on Rejected Approaches

**What goes wrong:** Rejected approaches from one session appear in another.

**Why it happens:** Using same thread_id across different "conversations" or tests.

**How to avoid:** Use unique thread_id per session. In tests, use `f"test-{uuid4()}"`.

**Warning signs:** Unexpected rejected approaches in fresh sessions.

### Pitfall 4: Infinite Rejection Loop

**What goes wrong:** User keeps rejecting, agent keeps generating, loop never ends.

**Why it happens:** No limit on rejections.

**How to avoid:** Add rejection counter to state. After N rejections (e.g., 3), force selection or end with error.

**Warning signs:** Runaway API costs, never-ending loops.

### Pitfall 5: Resume Value Type Mismatch

**What goes wrong:** Node receives unexpected type from resume.

**Why it happens:** User provides string when int expected, or vice versa.

**How to avoid:** Validate resume value type before using. Handle both string and int for selection (user might type "1" or 1).

**Warning signs:** Type errors in node, unexpected behavior.

## Code Examples

Verified patterns from official sources:

### Updated State Schema

```python
# Source: Existing pattern from project
# File: src/graph/state.py
from typing_extensions import TypedDict


class ArticleState(TypedDict):
    """State schema for the pedagogical article writer workflow."""

    topic: str | None
    approaches: list[dict] | None
    selected_approach_index: int | None  # Set by approach_selection_node
    rejected_approaches: list[dict] | None  # NEW: Accumulates rejected approaches
    current_draft: str | None
    is_approved: bool
    revision_count: int
```

### Approach Selection Node

```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api
# File: src/graph/nodes.py
from typing import Literal
from langgraph.types import interrupt, Command
from src.graph.state import ArticleState


def approach_selection_node(state: ArticleState) -> Command[Literal["writer_agent", "approach_agent"]]:
    """Pause for user to select an approach or reject all.

    This node uses interrupt() to pause and present the 3 generated approaches.
    User can:
    - Enter 1, 2, or 3 to select an approach -> routes to writer_agent
    - Enter "reject" to reject all -> routes back to approach_agent

    The Command return type annotation is REQUIRED for graph validation.
    It specifies all possible routing destinations.
    """
    approaches = state["approaches"]

    # Build selection prompt
    prompt = "Select an approach (1, 2, or 3) or type 'reject' to regenerate:\n\n"
    for i, approach in enumerate(approaches, 1):
        prompt += f"{i}. {approach['title']}\n"
        prompt += f"   {approach['description'][:100]}...\n"
        prompt += f"   Metaphor: {approach['metaphor']}\n\n"

    # Pause for user input
    user_input = interrupt(prompt)

    # Handle rejection
    if isinstance(user_input, str) and user_input.lower() == "reject":
        # Accumulate rejected approaches (for retry context)
        rejected = state.get("rejected_approaches") or []
        rejected = rejected + approaches  # Create new list, don't mutate
        return Command(
            update={"rejected_approaches": rejected},
            goto="approach_agent"
        )

    # Handle selection
    try:
        # Support both string "1" and int 1
        index = int(user_input) - 1 if isinstance(user_input, str) else user_input - 1
        if 0 <= index < len(approaches):
            return Command(
                update={"selected_approach_index": index},
                goto="writer_agent"
            )
    except (ValueError, TypeError):
        pass

    # Invalid input - treat as rejection (simple approach)
    # Alternative: re-interrupt with error message
    rejected = state.get("rejected_approaches") or []
    rejected = rejected + approaches
    return Command(
        update={"rejected_approaches": rejected},
        goto="approach_agent"
    )
```

### Modified Approach Agent with Rejection Context

```python
# Source: Synthesized from LangGraph patterns
# File: src/graph/nodes.py (modified approach_agent_node)

# Extended system prompt that can include rejection context
APPROACH_SYSTEM_PROMPT = """You are a pedagogical expert who creates teaching approaches.
Given a topic, research existing educational resources and create exactly 3 distinct
pedagogical approaches, each with a unique metaphor or analogy.

Use the web_search tool to find relevant teaching resources about the topic.
Use the read_webpage tool to read promising pages for detailed content.

After researching (typically 2-3 searches), provide your final answer with exactly 3 approaches.
Each approach must have:
- A clear, descriptive title
- A 2-3 sentence description of how to teach the topic using this approach
- A concrete metaphor or analogy that makes the concept intuitive
- An explanation of why this approach is effective for learners"""


def approach_agent_node(state: ArticleState) -> dict:
    """Generate 3 pedagogical approaches, avoiding previously rejected ones."""
    topic = state["topic"]
    rejected = state.get("rejected_approaches") or []
    tools = [web_search, read_webpage]

    # Build system prompt with rejection context if any
    system_prompt = APPROACH_SYSTEM_PROMPT

    if rejected:
        system_prompt += "\n\n--- IMPORTANT ---\n"
        system_prompt += "The user has REJECTED the following approaches. "
        system_prompt += "Do NOT repeat these. Generate completely DIFFERENT approaches:\n\n"
        for r in rejected:
            system_prompt += f"REJECTED: \"{r['title']}\"\n"
            system_prompt += f"  - Metaphor was: \"{r['metaphor']}\"\n\n"
        system_prompt += "Create 3 NEW approaches with different titles and metaphors.\n"

    # ... rest of agent logic (model setup, tool loop, structured output)
    # unchanged from Phase 3 implementation
```

### Updated Workflow Graph

```python
# Source: https://docs.langchain.com/oss/python/langgraph/graph-api
# File: src/graph/workflow.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.graph.state import ArticleState
from src.graph.nodes import (
    topic_input_node,
    approach_agent_node,
    approach_selection_node,  # NEW
    writer_agent_node,
    save_output_node,
)


def build_graph() -> StateGraph:
    """Construct the article writer graph with approach selection."""
    builder = StateGraph(ArticleState)

    # Add all nodes
    builder.add_node("topic_input", topic_input_node)
    builder.add_node("approach_agent", approach_agent_node)
    builder.add_node("approach_selection", approach_selection_node)  # NEW
    builder.add_node("writer_agent", writer_agent_node)
    builder.add_node("save_output", save_output_node)

    # Define edges
    # Note: approach_selection uses Command for routing, so no edge needed from it
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    builder.add_edge("approach_agent", "approach_selection")  # NEW
    # NO edge from approach_selection - Command handles routing dynamically!
    builder.add_edge("writer_agent", "save_output")
    builder.add_edge("save_output", END)

    return builder
```

### Updated main.py with Two Interrupts

```python
# Source: Synthesized from project patterns
# File: src/main.py (relevant excerpt)
from langgraph.types import Command

def main():
    """Demonstrate full workflow with two HITL interrupts."""
    graph = create_compiled_graph()
    config = {"configurable": {"thread_id": "article-session-1"}}

    # Initial state
    initial_state = {
        "topic": None,
        "approaches": None,
        "selected_approach_index": None,
        "rejected_approaches": None,  # NEW
        "current_draft": None,
        "is_approved": False,
        "revision_count": 0,
    }

    # Step 1: Start graph - pauses at topic_input
    result = graph.invoke(initial_state, config)

    # Step 2: Handle topic input interrupt
    if "__interrupt__" in result:
        print(result["__interrupt__"][0].value)
        user_topic = input("> ")
        result = graph.invoke(Command(resume=user_topic), config)

    # Step 3: Handle approach selection interrupt (may loop on rejection)
    while "__interrupt__" in result:
        print(result["__interrupt__"][0].value)
        user_selection = input("> ")
        result = graph.invoke(Command(resume=user_selection), config)

    # Step 4: Display results
    print(f"Selected approach: {result['approaches'][result['selected_approach_index']]['title']}")
    print(f"Draft: {result['current_draft']}")
```

### Test for Approach Selection

```python
# Source: Pattern from existing tests
# File: tests/test_graph.py
import pytest
from langgraph.types import Command
from src.graph import create_compiled_graph


class TestApproachSelection:
    """Tests for Phase 4: Approach selection HITL."""

    def test_graph_pauses_at_approach_selection(self, graph):
        """Verify graph pauses after approach_agent with selection prompt."""
        config = {"configurable": {"thread_id": "test-selection-1"}}

        # Start and provide topic
        graph.invoke({}, config)
        result = graph.invoke(Command(resume="Test Topic"), config)

        # Should be interrupted at approach_selection
        assert "__interrupt__" in result
        assert "Select an approach" in result["__interrupt__"][0].value

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires LLM")
    def test_selection_routes_to_writer(self, graph):
        """Verify selecting an approach routes to writer_agent."""
        config = {"configurable": {"thread_id": "test-selection-2"}}

        # Provide topic and get approaches
        graph.invoke({}, config)
        graph.invoke(Command(resume="Machine Learning"), config)

        # Select approach 1
        result = graph.invoke(Command(resume="1"), config)

        # Should complete (reached writer and beyond)
        assert "__interrupt__" not in result
        assert result["selected_approach_index"] == 0
        assert result["current_draft"] is not None

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires LLM")
    def test_rejection_routes_back_to_approach_agent(self, graph):
        """Verify rejecting approaches loops back to approach_agent."""
        config = {"configurable": {"thread_id": "test-rejection-1"}}

        # Provide topic
        graph.invoke({}, config)
        result = graph.invoke(Command(resume="Data Structures"), config)

        # Get first set of approaches
        first_approaches = result.get("approaches") if "__interrupt__" not in result else None

        # Reject approaches
        result = graph.invoke(Command(resume="reject"), config)

        # Should be back at approach_selection with new interrupt
        assert "__interrupt__" in result
        assert result["rejected_approaches"] is not None
        assert len(result["rejected_approaches"]) >= 3

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires LLM")
    def test_rejected_approaches_accumulate(self, graph):
        """Verify rejected approaches accumulate across retries."""
        config = {"configurable": {"thread_id": "test-rejection-accumulate"}}

        # Start graph
        graph.invoke({}, config)
        graph.invoke(Command(resume="Python Basics"), config)

        # Reject first time
        graph.invoke(Command(resume="reject"), config)

        # Reject second time
        result = graph.invoke(Command(resume="reject"), config)

        # Should have 6 rejected approaches (3 + 3)
        assert len(result["rejected_approaches"]) >= 6
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `add_conditional_edges()` | `Command(goto=...)` | LangGraph 0.2 | Node controls routing, not separate edge functions |
| Separate update + route | `Command(update=..., goto=...)` | LangGraph 0.2 | Atomic state update and routing |
| `interrupt_before`/`interrupt_after` | `interrupt()` function | LangGraph 0.2.31 | Dynamic, flexible interrupts |
| Parsing messages for context | Dedicated state fields | Best practice | Explicit, type-safe, easy to test |

**Deprecated/outdated:**
- `add_conditional_edges()` for nodes using Command: When a node returns Command(goto=...), conditional edges are redundant and can conflict
- Manual state updates before routing: Use Command(update=..., goto=...) instead

## Open Questions

Things that couldn't be fully resolved:

1. **Maximum rejection limit**
   - What we know: Should have a limit to prevent infinite loops
   - What's unclear: What's a reasonable limit (2? 3? 5?)
   - Recommendation: Start with 3 rejections max; add `rejection_count` to state if needed

2. **Input validation strictness**
   - What we know: Can re-interrupt with error message if input invalid
   - What's unclear: Whether to be strict (reject invalid) or lenient (treat as rejection)
   - Recommendation: Be lenient for Phase 4 (treat invalid as rejection); can add strict validation later

3. **Approach comparison for deduplication**
   - What we know: We pass rejected titles/metaphors to avoid repetition
   - What's unclear: LLM might still generate similar (not identical) approaches
   - Recommendation: Trust LLM instruction following; semantic deduplication is out of scope

## Sources

### Primary (HIGH confidence)
- [LangGraph Graph API - Command](https://docs.langchain.com/oss/python/langgraph/graph-api#combine-control-flow-and-state-updates-with-command) - Command with goto, type annotations
- [LangGraph How-To: Wait for User Input](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/) - interrupt() and Command(resume=...)
- [LangGraph Interrupts Documentation](https://docs.langchain.com/oss/python/langgraph/interrupts) - Validation loops, JSON-serializable values

### Secondary (MEDIUM confidence)
- [Medium: The Command Object in LangGraph](https://medium.com/@vivekvjnk/the-command-object-in-langgraph-bc29bf57d18f) - Practical examples
- [DEV.to: Beginners Guide to Dynamic Routing](https://medium.com/ai-engineering-bootcamp/a-beginners-guide-to-dynamic-routing-in-langgraph-with-command-2c8c0f3ef451) - Command best practices
- [LangGraph Best Practices](https://www.swarnendu.de/blog/langgraph-best-practices/) - Retry and loop patterns

### Tertiary (LOW confidence)
- [GitHub Discussion: Route based on tool return](https://github.com/langchain-ai/langgraph/discussions/5113) - Community solutions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using already-installed langgraph with documented Command API
- Architecture patterns: HIGH - Command(goto=...) pattern is well-documented in official docs
- State modification: HIGH - Adding TypedDict field follows established project pattern
- Pitfalls: MEDIUM - Some edge cases (validation strictness, rejection limits) need runtime validation

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - LangGraph HITL/Command API is stable post-1.0)
