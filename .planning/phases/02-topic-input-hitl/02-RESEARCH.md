# Phase 2: Topic Input (HITL) - Research

**Researched:** 2026-01-19
**Domain:** LangGraph Human-in-the-Loop, interrupt(), Command(resume=...), Thread Persistence
**Confidence:** HIGH

## Summary

Phase 2 implements the first human-in-the-loop interaction point using LangGraph's `interrupt()` function. The user provides a topic for the article, and the graph pauses until input is received. This builds on the Phase 1 foundation (InMemorySaver checkpointer already configured) by modifying the `topic_input_node` to call `interrupt()` and updating `main.py` to handle the interrupt/resume cycle.

The research confirms that LangGraph's HITL pattern is stable and well-documented since v0.2.31. The `interrupt()` function is the modern, recommended approach (replacing older `interrupt_before`/`interrupt_after` parameters). The pattern requires three elements: (1) a checkpointer (already have InMemorySaver), (2) a thread_id in config (already implemented), and (3) the `interrupt()` call inside a node. Resumption uses `Command(resume=value)` passed to `invoke()` or `stream()`.

**Primary recommendation:** Modify `topic_input_node` to call `interrupt("Please provide a topic for the article:")` and return the interrupt value as the topic. Update `main.py` to detect the `__interrupt__` key in results and demonstrate the resume flow with `Command(resume="user topic")`.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.6 | Graph orchestration with HITL | Provides `interrupt()` function, `Command` class, and checkpointing. Already installed. |
| langgraph.types | (part of langgraph) | Type imports | Provides `interrupt`, `Command`, `Interrupt` classes for HITL patterns. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing_extensions | latest | TypedDict | Already used for state schema. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `interrupt()` function | `interrupt_before`/`interrupt_after` | Static breakpoints are deprecated; `interrupt()` is cleaner, more flexible, and the recommended approach. |
| `invoke()` for HITL | `stream()` for HITL | Both work; `invoke()` is simpler for Phase 2. `stream()` offers event visibility but adds complexity. |

**Installation:**
```bash
# No new packages needed - langgraph already provides interrupt/Command
pip install langgraph>=1.0.6  # Already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── graph/
│   ├── __init__.py
│   ├── state.py           # ArticleState TypedDict (no changes needed)
│   ├── nodes.py           # topic_input_node uses interrupt()
│   └── workflow.py        # No changes needed (checkpointer already configured)
└── main.py                # Demonstrates interrupt/resume cycle
tests/
└── test_graph.py          # Add tests for interrupt/resume behavior
```

### Pattern 1: Using interrupt() for User Input

**What:** Call `interrupt()` inside a node to pause execution and collect user input.

**When to use:** Any node that requires external input before proceeding.

**Example:**
```python
# Source: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/
from langgraph.types import interrupt

def topic_input_node(state: ArticleState) -> dict:
    """Collect topic from user via interrupt.

    The interrupt() call pauses graph execution and returns its argument
    to the caller. When resumed with Command(resume=value), the interrupt()
    call returns that value, which becomes the topic.
    """
    # Pause and wait for user input
    topic = interrupt("Please provide a topic for the article:")
    return {"topic": topic}
```

### Pattern 2: Detecting Interrupts in Results

**What:** Check for `__interrupt__` key in invoke/stream results to detect when graph is paused.

**When to use:** In calling code (main.py, tests) to know when to prompt user.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/interrupts
config = {"configurable": {"thread_id": "session-1"}}

# First invocation - hits interrupt and pauses
result = graph.invoke(initial_state, config)

# Check if graph is interrupted
if "__interrupt__" in result:
    # result["__interrupt__"] contains list of Interrupt objects
    # Each has: value (the prompt), id (for multiple interrupts), resumable (bool)
    interrupt_info = result["__interrupt__"][0]
    print(f"Graph paused: {interrupt_info.value}")  # "Please provide a topic..."
```

### Pattern 3: Resuming with Command(resume=...)

**What:** Use `Command(resume=value)` to provide input and continue execution from the interrupt point.

**When to use:** After detecting an interrupt, to provide the user's input and continue.

**Example:**
```python
# Source: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/
from langgraph.types import Command

# Resume with user-provided topic
# The value passed to resume becomes the return value of interrupt() inside the node
user_topic = "Quantum Computing for Beginners"
result = graph.invoke(Command(resume=user_topic), config)

# Graph continues from interrupt point through remaining nodes
print(f"Final topic: {result['topic']}")  # "Quantum Computing for Beginners"
```

### Pattern 4: Complete Interrupt/Resume Cycle

**What:** Full workflow showing initial invocation, interrupt detection, and resumption.

**When to use:** Reference pattern for main.py implementation.

**Example:**
```python
# Source: Synthesized from official LangGraph documentation
from langgraph.types import Command, interrupt
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# Node with interrupt
def topic_input_node(state):
    topic = interrupt("Please provide a topic for the article:")
    return {"topic": topic}

# Build and compile graph (checkpointer required for interrupt)
builder = StateGraph(ArticleState)
builder.add_node("topic_input", topic_input_node)
# ... add other nodes and edges ...
graph = builder.compile(checkpointer=InMemorySaver())

# Execute with interrupt/resume
config = {"configurable": {"thread_id": "article-session-1"}}

# Step 1: Initial invocation - will pause at interrupt
result = graph.invoke(initial_state, config)

# Step 2: Check for interrupt
if "__interrupt__" in result:
    prompt = result["__interrupt__"][0].value
    print(f"Input needed: {prompt}")

    # Step 3: Get user input (in real app, this would be actual user input)
    user_input = input("> ")

    # Step 4: Resume with user input
    final_result = graph.invoke(Command(resume=user_input), config)
    print(f"Topic set to: {final_result['topic']}")
```

### Anti-Patterns to Avoid

- **Wrapping interrupt() in try/except:** The interrupt mechanism uses exceptions internally; catching them breaks the pattern.
- **Conditionally skipping interrupt() calls:** Multiple interrupts use index-based matching; skipping one breaks the order.
- **Non-JSON-serializable interrupt values:** Both the interrupt prompt and resume value must be JSON-serializable.
- **Side effects before interrupt():** Code before `interrupt()` re-runs when resumed; make it idempotent.
- **Forgetting checkpointer:** Without a checkpointer, interrupt state cannot be persisted. (We already have InMemorySaver.)
- **Missing thread_id:** Without thread_id, the runtime cannot identify which interrupted state to resume.
- **Returning full state from nodes:** Continue returning partial dict updates, not full state.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pausing for user input | Custom polling/waiting logic | `interrupt()` function | Built-in persistence, resource-efficient waiting, production-ready |
| Resuming with input | Custom state injection | `Command(resume=...)` | Proper state restoration, works with checkpointer |
| Detecting pause state | Custom flags in state | Check `__interrupt__` key | Standard pattern, includes metadata (prompt, id) |
| Thread management | Custom session tracking | thread_id in config | Handles state isolation, persistence automatically |

**Key insight:** LangGraph's interrupt/Command pattern handles the complex state management required for asynchronous human-in-the-loop workflows. An interrupted thread uses no resources beyond storage and can resume much later, even on a different machine.

## Common Pitfalls

### Pitfall 1: Node Restarts on Resume

**What goes wrong:** Code before `interrupt()` executes again when the graph resumes.

**Why it happens:** LangGraph restarts the entire node from the beginning on resume, not from the exact line where interrupt was called.

**How to avoid:** Make all code before `interrupt()` idempotent. For simple topic input, there's no code before interrupt, so this is not an issue.

**Warning signs:** Duplicate side effects (logs, writes) when resuming.

### Pitfall 2: Not Checking __interrupt__ Before Resume

**What goes wrong:** Calling `Command(resume=...)` when graph is not actually interrupted causes unexpected behavior.

**Why it happens:** Assuming graph always pauses at interrupt point.

**How to avoid:** Always check `"__interrupt__" in result` before attempting to resume.

**Warning signs:** Errors about "no interrupt to resume" or unexpected state.

### Pitfall 3: Using Wrong Thread ID on Resume

**What goes wrong:** Resume goes to wrong/non-existent thread, losing the interrupted state.

**Why it happens:** Thread ID is a string that must match exactly between interrupt and resume.

**How to avoid:** Store config with thread_id and reuse it for resume call.

**Warning signs:** "Thread not found" errors or unexpected fresh state.

### Pitfall 4: Non-Serializable Interrupt Values

**What goes wrong:** Interrupt fails with serialization error.

**Why it happens:** Both the prompt passed to `interrupt()` and the value passed to `Command(resume=...)` must be JSON-serializable.

**How to avoid:** Use strings, numbers, booleans, lists, and dicts with simple values. For Phase 2, both prompt and topic are strings, so no issue.

**Warning signs:** Serialization errors during interrupt or resume.

### Pitfall 5: Testing Without Unique Thread IDs

**What goes wrong:** Tests interfere with each other's state.

**Why it happens:** Using same thread_id across tests with persistent checkpointer.

**How to avoid:** Use unique thread_id for each test (e.g., `f"test-{uuid4()}"`).

**Warning signs:** Test flakiness, unexpected state from previous tests.

## Code Examples

Verified patterns from official sources:

### topic_input_node with interrupt()

```python
# Source: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/
from langgraph.types import interrupt
from src.graph.state import ArticleState


def topic_input_node(state: ArticleState) -> dict:
    """Collect article topic from user via human-in-the-loop interrupt.

    This node pauses graph execution using interrupt() and waits for
    the user to provide a topic. The graph resumes when the caller
    invokes with Command(resume=topic_string).

    The interrupt() call:
    1. Pauses execution and saves state to checkpointer
    2. Returns its argument ("Please provide...") to the caller in __interrupt__
    3. When resumed, returns the value from Command(resume=value)

    Args:
        state: Current graph state (not used for this node).

    Returns:
        Dict with 'topic' field set to user-provided topic string.
    """
    topic = interrupt("Please provide a topic for the article:")
    return {"topic": topic}
```

### main.py Demonstrating Interrupt/Resume

```python
# Source: Synthesized from official documentation
from langgraph.types import Command
from src.graph.workflow import create_compiled_graph


def main():
    """Demonstrate HITL topic input via interrupt/resume cycle."""
    graph = create_compiled_graph()

    config = {"configurable": {"thread_id": "article-session-1"}}

    initial_state = {
        "topic": None,
        "approaches": None,
        "selected_approach_index": None,
        "current_draft": None,
        "is_approved": False,
        "revision_count": 0,
    }

    # Step 1: Start graph - will pause at topic_input_node interrupt
    print("Starting article writer...")
    result = graph.invoke(initial_state, config)

    # Step 2: Handle interrupt
    if "__interrupt__" in result:
        prompt = result["__interrupt__"][0].value
        print(f"\n{prompt}")
        user_topic = input("> ")

        # Step 3: Resume with user input
        result = graph.invoke(Command(resume=user_topic), config)

    # Step 4: Display results
    print(f"\n=== Final State ===")
    print(f"Topic: {result['topic']}")
    print(f"Draft: {result['current_draft']}")


if __name__ == "__main__":
    main()
```

### Test for Interrupt/Resume Cycle

```python
# Source: Pattern derived from official documentation
import pytest
from langgraph.types import Command
from src.graph import create_compiled_graph


class TestTopicInputInterrupt:
    """Tests for Phase 2 HITL topic input via interrupt."""

    def test_graph_pauses_at_topic_input(self):
        """Verify graph pauses at topic_input_node with interrupt."""
        graph = create_compiled_graph()
        config = {"configurable": {"thread_id": "test-interrupt-1"}}

        result = graph.invoke({}, config)

        # Should have interrupted, not completed
        assert "__interrupt__" in result
        assert result["__interrupt__"][0].value == "Please provide a topic for the article:"

    def test_resume_with_command_sets_topic(self):
        """Verify Command(resume=...) correctly sets topic and continues."""
        graph = create_compiled_graph()
        config = {"configurable": {"thread_id": "test-interrupt-2"}}

        # Start - will interrupt
        graph.invoke({}, config)

        # Resume with topic
        result = graph.invoke(Command(resume="Test Topic"), config)

        # Topic should be set and graph should complete
        assert result["topic"] == "Test Topic"
        assert "__interrupt__" not in result  # Graph completed
        assert result["is_approved"] is True  # Reached final node

    def test_different_threads_independent(self):
        """Verify different thread_ids maintain independent interrupt states."""
        graph = create_compiled_graph()
        config1 = {"configurable": {"thread_id": "thread-a"}}
        config2 = {"configurable": {"thread_id": "thread-b"}}

        # Start both - both interrupt
        graph.invoke({}, config1)
        graph.invoke({}, config2)

        # Resume with different topics
        result1 = graph.invoke(Command(resume="Topic A"), config1)
        result2 = graph.invoke(Command(resume="Topic B"), config2)

        assert result1["topic"] == "Topic A"
        assert result2["topic"] == "Topic B"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `interrupt_before`/`interrupt_after` params | `interrupt()` function | LangGraph 0.2.31 | Dynamic, flexible interrupts anywhere in node code |
| `NodeInterrupt` exception | `interrupt()` function | LangGraph 0.2.31 | Cleaner API, same underlying mechanism |
| Manual `__interrupt__` checking | Auto-surfacing in `invoke()` | LangGraph 0.4 | Interrupts appear in invoke result automatically |

**Deprecated/outdated:**
- `interrupt_before`/`interrupt_after` graph compile parameters: Use `interrupt()` function inside nodes instead
- `NodeInterrupt` exception pattern: Use `interrupt()` function instead
- Streaming required for interrupts: As of v0.4, `invoke()` also surfaces interrupts properly

## Open Questions

Things that couldn't be fully resolved:

1. **Exact Interrupt object structure in v1.0.6**
   - What we know: `__interrupt__` contains `Interrupt` objects with `value`, `id`, and `resumable` fields
   - What's unclear: Whether any additional fields exist in 1.0.6
   - Recommendation: Access `.value` for the prompt message, which is all we need for Phase 2

2. **invoke() vs stream() for production HITL**
   - What we know: Both work; `invoke()` is simpler, `stream()` provides event visibility
   - What's unclear: Whether there are edge cases where one is preferred
   - Recommendation: Use `invoke()` for Phase 2 (simpler for learning); can upgrade to `stream()` later if needed

## Sources

### Primary (HIGH confidence)
- [LangGraph How-To: Wait for User Input](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/) - Complete interrupt/resume pattern with code examples
- [LangGraph Interrupts Documentation](https://docs.langchain.com/oss/python/langgraph/interrupts) - Requirements, internal mechanism, anti-patterns
- [LangGraph Types Reference](https://reference.langchain.com/python/langgraph/types/) - API signatures for interrupt, Command, Interrupt classes

### Secondary (MEDIUM confidence)
- [LangGraph v0.4 Changelog](https://changelog.langchain.com/announcements/langgraph-v0-4-working-with-interrupts) - invoke() auto-surfacing interrupts
- [LangGraph Blog: Human-in-the-Loop with interrupt](https://www.blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/) - Design rationale, comparison to Python input()
- [DEV.to: Interrupts and Commands in LangGraph](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl) - Full working example with router pattern

### Tertiary (LOW confidence)
- [Medium: Human-in-the-Loop with LangGraph](https://medium.com/the-advanced-school-of-ai/human-in-the-loop-with-langgraph-mastering-interrupts-and-commands-9e1cf2183ae3) - Tutorial series (verify patterns against official docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using already-installed langgraph with documented interrupt API
- Architecture patterns: HIGH - Direct from official how-to guide with verified examples
- Pitfalls: HIGH - Documented in official interrupts page, cross-verified

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - LangGraph HITL API is stable post-1.0)
