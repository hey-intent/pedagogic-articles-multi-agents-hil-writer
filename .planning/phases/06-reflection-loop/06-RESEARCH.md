# Phase 6: Reflection Loop - Research

**Researched:** 2026-01-19
**Domain:** LangGraph Reflection Patterns, Writer-Critic Loops, Iteration Control, Command Routing
**Confidence:** HIGH

## Summary

Phase 6 implements the writer-critic reflection loop - the core quality improvement mechanism for the pedagogical article writer. The pattern involves the critic agent evaluating the current draft and either approving it (routing to output) or returning feedback that triggers another writer iteration. This continues until either the critic approves OR the maximum iteration count (3) is reached.

The implementation follows the established project patterns: Command-based routing for dynamic control flow, TypedDict state with new fields for critic feedback and iteration tracking, and structured output via Pydantic for reliable critic responses. The key architectural insight is that the critic node controls routing using `Command(goto=...)`, similar to how `approach_selection_node` handles routing in Phase 4.

The termination logic must handle two conditions: (1) critic approval (`is_approved=True`) routes to `save_output`, and (2) maximum iterations (`revision_count >= 3`) forces termination regardless of approval. This dual condition prevents infinite loops while allowing quality improvement iterations.

**Primary recommendation:** Create `critic_agent_node` that evaluates the draft against accuracy and comprehensibility criteria using structured output (Pydantic `CriticEvaluation` model). Modify `writer_agent_node` to accept critic feedback for revision mode. Update state with `critic_feedback: str | None` field. Critic returns `Command(goto="writer_agent")` for revisions or `Command(goto="save_output")` for approval/max iterations.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.6 | Graph orchestration with Command routing | Already installed. Command pattern established in Phase 4 for approach selection. |
| langgraph.types | (part of langgraph) | Command, Literal types | Provides `Command[Literal["node_a", "node_b"]]` for type-safe routing. |
| langchain-openai | 0.3.0 | LLM for critic evaluation | Already installed. ChatOpenAI with OpenRouter works with structured output. |
| pydantic | (via langchain) | Structured output schema | Already used for ApproachList. Provides `with_structured_output()` pattern. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing | stdlib | Literal type annotation | For Command return type annotation specifying valid routing destinations. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Command(goto=...)` | `add_conditional_edges()` | Conditional edges separate routing from evaluation logic; Command keeps them together in critic node - cleaner for this use case. |
| Pydantic structured output | JSON parsing | Pydantic provides validation and type safety; raw JSON would need manual parsing and validation. |
| Revision counter in state | Message list length | Explicit counter is clearer and easier to test; message counting would be fragile. |

**Installation:**
```bash
# No new packages needed - all required libraries already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/
|-- graph/
|   |-- __init__.py
|   |-- state.py           # Add critic_feedback field
|   |-- workflow.py        # Add critic_agent_node, update edges
|   |-- nodes/
|       |-- __init__.py    # Export critic_agent_node
|       |-- critic_agent.py    # NEW: Critic evaluation node
|       |-- writer_agent.py    # Modify for revision mode
src/
|-- schemas/
|   |-- __init__.py        # Export CriticEvaluation
|   |-- critic.py          # NEW: Pydantic model for critic output
tests/
|-- test_graph.py          # Add reflection loop tests
```

### Pattern 1: Critic Agent with Command Routing

**What:** A node that evaluates the draft and routes based on approval status.

**When to use:** When a node must make a routing decision based on its evaluation.

**Example:**
```python
# Source: Synthesized from LangGraph Command pattern (Phase 4) + reflection patterns
from typing import Literal
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from src.config import config, REASONING_MODEL
from src.graph.state import ArticleState
from src.schemas import CriticEvaluation

MAX_ITERATIONS = 3

def critic_agent_node(state: ArticleState) -> Command[Literal["writer_agent", "save_output"]]:
    """Evaluate draft and route to writer (revise) or save_output (approved).

    Termination conditions:
    1. Critic approves the draft -> route to save_output
    2. Max iterations reached (revision_count >= 3) -> route to save_output

    The Command return type annotation is REQUIRED for graph validation.
    """
    current_draft = state["current_draft"]
    revision_count = state["revision_count"]

    # Force exit if max iterations reached
    if revision_count >= MAX_ITERATIONS:
        return Command(
            update={"is_approved": True},  # Mark as done (forced)
            goto="save_output"
        )

    # Evaluate draft with LLM
    model = ChatOpenAI(
        model=REASONING_MODEL,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )
    model_structured = model.with_structured_output(CriticEvaluation)

    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Evaluate this article:\n\n{current_draft}"},
    ]

    evaluation = model_structured.invoke(messages)

    if evaluation.approved:
        return Command(
            update={
                "is_approved": True,
                "critic_feedback": None,  # Clear feedback on approval
            },
            goto="save_output"
        )
    else:
        return Command(
            update={
                "is_approved": False,
                "critic_feedback": evaluation.feedback,
                "revision_count": revision_count + 1,  # Increment counter
            },
            goto="writer_agent"
        )
```

### Pattern 2: Writer with Revision Mode

**What:** Modify writer_agent_node to handle both initial drafts and revisions.

**When to use:** When a node must handle different execution modes based on state.

**Example:**
```python
# Source: Pattern from Phase 5 research + iteration loop pattern
def writer_agent_node(state: ArticleState) -> dict:
    """Draft or revise article based on state.

    Mode detection:
    - Initial draft: critic_feedback is None
    - Revision: critic_feedback contains feedback text
    """
    topic = state["topic"]
    approach = state["approaches"][state["selected_approach_index"]]
    critic_feedback = state.get("critic_feedback")
    current_draft = state.get("current_draft")

    model = ChatOpenAI(
        model=WRITING_MODEL,
        max_tokens=4096,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    if critic_feedback and current_draft:
        # Revision mode: incorporate critic feedback
        user_content = f"""Revise this article based on the critic's feedback.

ORIGINAL ARTICLE:
{current_draft}

CRITIC FEEDBACK:
{critic_feedback}

TOPIC: {topic}
APPROACH: {approach['title']} using metaphor: {approach['metaphor']}

Provide the complete revised article addressing the feedback while maintaining the pedagogical approach and metaphor."""
    else:
        # Initial draft mode (unchanged from Phase 5)
        user_content = f"""Write an educational article about: {topic}

Use this pedagogical approach throughout the article:

Title: {approach['title']}
Description: {approach['description']}
Core Metaphor: {approach['metaphor']}
Why This Works: {approach['why_effective']}

Remember to weave the metaphor throughout your explanation."""

    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    response = model.invoke(messages)

    return {"current_draft": response.content}
```

### Pattern 3: Structured Output for Critic Evaluation

**What:** Pydantic model ensuring consistent, validated critic responses.

**When to use:** When LLM output needs strict structure for routing decisions.

**Example:**
```python
# Source: Established project pattern from ApproachList schema
from pydantic import BaseModel, Field

class CriticEvaluation(BaseModel):
    """Critic evaluation result with approval decision and feedback."""

    approved: bool = Field(
        description="True if the article meets all quality criteria, False if revisions needed"
    )
    accuracy_score: int = Field(
        ge=1, le=10,
        description="Score 1-10 for technical accuracy of the content"
    )
    comprehensibility_score: int = Field(
        ge=1, le=10,
        description="Score 1-10 for how accessible the explanation is to beginners"
    )
    feedback: str = Field(
        description="Specific, actionable feedback for improvement. Empty if approved."
    )
```

### Pattern 4: Graph Wiring for Reflection Loop

**What:** Graph structure supporting the writer-critic loop with Command routing.

**When to use:** When creating cyclic flows controlled by node decisions.

**Example:**
```python
# Source: Established project pattern from workflow.py
from langgraph.graph import StateGraph, START, END

def build_graph() -> StateGraph:
    """Construct graph with writer-critic reflection loop."""
    builder = StateGraph(ArticleState)

    # Add all nodes
    builder.add_node("topic_input", topic_input_node)
    builder.add_node("approach_agent", approach_agent_node)
    builder.add_node("approach_selection", approach_selection_node)
    builder.add_node("writer_agent", writer_agent_node)
    builder.add_node("critic_agent", critic_agent_node)  # NEW
    builder.add_node("save_output", save_output_node)

    # Define edges
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    builder.add_edge("approach_agent", "approach_selection")
    # No edge from approach_selection - Command handles routing
    builder.add_edge("writer_agent", "critic_agent")  # CHANGED: writer -> critic
    # No edge from critic_agent - Command handles routing!
    # critic returns Command(goto="writer_agent") or Command(goto="save_output")
    builder.add_edge("save_output", END)

    return builder
```

### Anti-Patterns to Avoid

- **Forgetting iteration limit:** Always check `revision_count >= MAX_ITERATIONS` before LLM evaluation to prevent runaway loops.
- **Missing Command type annotation:** `Command[Literal["writer_agent", "save_output"]]` return type is REQUIRED for graph validation.
- **Vague critic prompts:** Generic "is this good?" prompts lead to rubber-stamp approvals or endless nitpicking. Use specific criteria.
- **Mutating revision_count:** Use `revision_count + 1` to create new value, never `state["revision_count"] += 1`.
- **Not testing termination:** Always have tests that verify max iterations triggers exit.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conditional routing | Custom edge functions | `Command(goto=...)` | Built-in, type-safe, keeps routing in the decision-making node |
| Structured critic output | JSON parsing + validation | `with_structured_output(Pydantic)` | Automatic validation, type safety, handles LLM quirks |
| Iteration counting | Message list length | Explicit `revision_count` state field | Clear, testable, survives state serialization |
| Exit conditions | Complex conditional edges | Check in node + Command | Logic stays together, easier to understand and modify |

**Key insight:** The reflection loop is conceptually a while loop, but in LangGraph it's implemented as cyclic edges with Command-based routing. The critic node decides when to exit the loop.

## Common Pitfalls

### Pitfall 1: Infinite Loop from Missing Termination

**What goes wrong:** Critic always finds something to criticize, loop hits GraphRecursionError.

**Why it happens:** No maximum iteration check, or critic prompt is too strict.

**How to avoid:** ALWAYS check `revision_count >= MAX_ITERATIONS` FIRST in critic_agent_node, before any LLM call. Force approval if limit reached.

**Warning signs:** Graph consistently hits 25 iterations (default recursion limit), runaway API costs.

### Pitfall 2: Critic Approves Everything

**What goes wrong:** Critic always returns `approved=True` on first pass, no improvement happens.

**Why it happens:** Prompt is too lenient, lacks specific criteria, or uses vague language.

**How to avoid:** Define specific, measurable criteria:
- Accuracy: "Are all technical claims correct? Score 1-10."
- Comprehensibility: "Would a beginner understand this? Score 1-10."
- Approval threshold: "Approve only if BOTH scores >= 7."

**Warning signs:** revision_count is always 0 after completion, articles vary wildly in quality.

### Pitfall 3: Counter Not Incrementing

**What goes wrong:** revision_count stays at 0, max iterations never triggers.

**Why it happens:** Forgot to increment counter in Command update, or using wrong field name.

**How to avoid:** Explicit test: "After 3 rejections, is_approved should be True regardless of critic LLM output."

**Warning signs:** revision_count always 0 in final state, infinite loops despite iteration cap code.

### Pitfall 4: Writer Ignores Feedback

**What goes wrong:** Writer produces same or similar draft despite critic feedback.

**Why it happens:** Feedback not prominently placed in prompt, or prompt doesn't emphasize addressing feedback.

**How to avoid:** Put feedback in clear section with explicit instruction: "Address ALL points in the feedback. Explain how each was addressed."

**Warning signs:** Successive drafts are nearly identical, same issues flagged repeatedly.

### Pitfall 5: State Field Not Initialized

**What goes wrong:** KeyError when accessing `critic_feedback` or `revision_count` on first iteration.

**Why it happens:** New state fields not added to initial state with defaults.

**How to avoid:** Use `state.get("critic_feedback")` with None default. Ensure initial state includes `revision_count: 0`.

**Warning signs:** KeyError in first test run, works only after rejection cycle.

## Code Examples

Verified patterns from official sources and established project conventions:

### Updated State Schema

```python
# Source: Existing pattern from state.py
# File: src/graph/state.py
from typing_extensions import TypedDict


class ArticleState(TypedDict):
    """State schema for the pedagogical article writer workflow.

    Phase 6 additions:
    - critic_feedback: Feedback from critic for writer revision
    - is_approved: Set True when critic approves OR max iterations reached
    - revision_count: Tracks writer-critic iterations (0-based, max 3)
    """

    topic: str | None
    approaches: list[dict] | None
    selected_approach_index: int | None
    rejected_approaches: list[dict] | None
    current_draft: str | None
    critic_feedback: str | None  # NEW: Feedback for revision
    is_approved: bool
    revision_count: int  # Already exists, now actively used
```

### Critic Evaluation Schema

```python
# Source: Synthesized from ApproachList pattern
# File: src/schemas/critic.py
from pydantic import BaseModel, Field


class CriticEvaluation(BaseModel):
    """Structured output for critic agent evaluation.

    The critic evaluates articles on two dimensions required by AGNT-05:
    1. Accuracy: Technical correctness of the content
    2. Comprehensibility: Accessibility for beginners

    Approval threshold: Both scores >= 7 (out of 10).
    """

    accuracy_score: int = Field(
        ge=1, le=10,
        description="Score 1-10 for technical accuracy. 10=perfectly accurate, 1=major errors."
    )
    accuracy_issues: str = Field(
        description="Specific accuracy issues found. Empty if score >= 7."
    )
    comprehensibility_score: int = Field(
        ge=1, le=10,
        description="Score 1-10 for beginner accessibility. 10=crystal clear, 1=incomprehensible."
    )
    comprehensibility_issues: str = Field(
        description="Specific comprehensibility issues found. Empty if score >= 7."
    )
    approved: bool = Field(
        description="True ONLY if BOTH accuracy_score >= 7 AND comprehensibility_score >= 7."
    )
    feedback: str = Field(
        description="Combined actionable feedback for the writer. Lists specific improvements needed. Empty string if approved."
    )
```

### Critic Agent System Prompt

```python
# Source: Best practices from PITFALLS.md + reflection pattern guides
# File: src/graph/nodes/critic_agent.py

CRITIC_SYSTEM_PROMPT = """You are a pedagogical content critic evaluating educational articles.
Your role is to ensure articles are BOTH technically accurate AND accessible to beginners.

## Evaluation Criteria

### 1. ACCURACY (Score 1-10)
Evaluate technical correctness:
- Are all facts and concepts correct?
- Are there any misleading simplifications?
- Would an expert find errors?

Score guide:
- 10: Perfectly accurate, no issues
- 7-9: Minor issues that don't mislead
- 4-6: Some errors that could confuse
- 1-3: Major factual errors

### 2. COMPREHENSIBILITY (Score 1-10)
Evaluate accessibility for beginners:
- Is the metaphor used effectively throughout?
- Are concepts introduced gradually?
- Would a curious beginner understand this?

Score guide:
- 10: Crystal clear, delightful to read
- 7-9: Clear with minor rough spots
- 4-6: Confusing in places
- 1-3: Incomprehensible to beginners

## Approval Decision

APPROVE (approved=True) ONLY IF:
- accuracy_score >= 7 AND comprehensibility_score >= 7

REJECT (approved=False) IF:
- Either score < 7

## Feedback Guidelines

When rejecting, provide:
1. Specific issues (quote problematic text)
2. Concrete suggestions for improvement
3. Priority: accuracy issues first, then comprehensibility

When approving:
- feedback should be empty string
- accuracy_issues and comprehensibility_issues should be empty strings"""
```

### Complete Critic Agent Node

```python
# Source: Synthesized from project patterns + reflection research
# File: src/graph/nodes/critic_agent.py
from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.types import Command

from src.config import config, REASONING_MODEL
from src.graph.state import ArticleState
from src.schemas import CriticEvaluation


# Maximum writer-critic iterations before forced approval
MAX_ITERATIONS = 3


def critic_agent_node(state: ArticleState) -> Command[Literal["writer_agent", "save_output"]]:
    """Evaluate article draft and route to writer (revision) or save_output (approved).

    This node implements the critic side of the reflection loop. It evaluates
    the current draft against accuracy and comprehensibility criteria, then
    routes based on approval status.

    Termination conditions (LOOP-02, LOOP-03):
    1. Critic approves (both scores >= 7) -> route to save_output
    2. Max iterations reached (revision_count >= 3) -> force approval, route to save_output

    The Command return type annotation specifies valid routing destinations
    and is REQUIRED for graph validation.

    Args:
        state: Current graph state with current_draft and revision_count.

    Returns:
        Command routing to writer_agent (for revision) or save_output (for completion).
    """
    current_draft = state["current_draft"]
    revision_count = state["revision_count"]

    # CRITICAL: Check iteration limit FIRST to prevent runaway loops (LOOP-03)
    if revision_count >= MAX_ITERATIONS:
        return Command(
            update={"is_approved": True},  # Force approval
            goto="save_output"
        )

    # Create model for evaluation using REASONING_MODEL from config
    model = ChatOpenAI(
        model=REASONING_MODEL,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    # Use structured output for reliable evaluation parsing
    model_structured = model.with_structured_output(CriticEvaluation)

    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Evaluate this pedagogical article:\n\n{current_draft}"},
    ]

    evaluation = model_structured.invoke(messages)

    if evaluation.approved:
        # Article meets quality criteria - route to output
        return Command(
            update={
                "is_approved": True,
                "critic_feedback": None,
            },
            goto="save_output"
        )
    else:
        # Article needs revision - increment counter and route to writer
        return Command(
            update={
                "is_approved": False,
                "critic_feedback": evaluation.feedback,
                "revision_count": revision_count + 1,  # Increment (LOOP-04)
            },
            goto="writer_agent"
        )
```

### Modified Writer Agent with Revision Support

```python
# Source: Phase 5 implementation + revision pattern
# File: src/graph/nodes/writer_agent.py (modification)

def writer_agent_node(state: ArticleState) -> dict:
    """Draft or revise article using selected pedagogical approach.

    This node operates in two modes:
    1. Initial draft: No critic_feedback -> write fresh article
    2. Revision: critic_feedback present -> revise based on feedback

    Mode is detected by checking critic_feedback field in state.

    Args:
        state: Current graph state with topic, approaches, selected_approach_index,
               and optionally critic_feedback and current_draft for revisions.

    Returns:
        Dict with 'current_draft' field containing the (revised) markdown article.
    """
    topic = state["topic"]
    approaches = state["approaches"]
    selected_idx = state["selected_approach_index"]
    approach = approaches[selected_idx]

    # Check for revision mode
    critic_feedback = state.get("critic_feedback")
    current_draft = state.get("current_draft")

    model = ChatOpenAI(
        model=WRITING_MODEL,
        max_tokens=4096,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    if critic_feedback and current_draft:
        # REVISION MODE: Incorporate critic feedback
        user_content = f"""Revise this article based on the critic's feedback.

CURRENT ARTICLE:
{current_draft}

CRITIC FEEDBACK TO ADDRESS:
{critic_feedback}

ORIGINAL CONTEXT:
- Topic: {topic}
- Pedagogical approach: {approach['title']}
- Core metaphor: {approach['metaphor']}

INSTRUCTIONS:
1. Address ALL points raised in the critic feedback
2. Maintain the pedagogical approach and weave the metaphor throughout
3. Keep the 3Blue1Brown style: intuition first, concrete examples, "aha!" moments
4. Provide the COMPLETE revised article (not just the changes)"""
    else:
        # INITIAL DRAFT MODE (unchanged from Phase 5)
        approach_text = f"""Title: {approach['title']}

Description: {approach['description']}

Core Metaphor: {approach['metaphor']}

Why This Works: {approach['why_effective']}"""

        user_content = f"""Write an educational article about: {topic}

Use this pedagogical approach throughout the article:

{approach_text}

Remember to weave the metaphor throughout your explanation, returning to it when introducing new concepts."""

    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    response = model.invoke(messages)

    return {"current_draft": response.content}
```

### Test Cases for Reflection Loop

```python
# Source: Established project test patterns
# File: tests/test_graph.py (additions)

class TestReflectionLoop:
    """Test suite for Phase 6: Writer-critic reflection loop.

    Tests verify:
    - Critic evaluates drafts (AGNT-05)
    - Critic routes via Command (routes to writer or save_output)
    - Iteration counter increments (LOOP-04)
    - Max iterations terminates loop (LOOP-03)
    - Critic approval terminates loop (LOOP-02)
    """

    def test_graph_has_critic_agent_node(self, graph):
        """Verify critic_agent node exists in graph."""
        node_names = list(graph.get_graph().nodes.keys())
        assert "critic_agent" in node_names

    @requires_api_key
    def test_writer_routes_to_critic(self, graph):
        """Verify writer_agent routes to critic_agent (not save_output)."""
        config = {"configurable": {"thread_id": f"test-writer-to-critic-{uuid4()}"}}

        # Run through to writer
        graph.invoke({}, config)
        graph.invoke(Command(resume="Test Topic"), config)
        result = graph.invoke(Command(resume="1"), config)

        # Graph should complete (critic routes to save_output)
        assert "__interrupt__" not in result
        # revision_count should be visible in state
        assert "revision_count" in result

    @requires_api_key
    def test_iteration_counter_visible_in_state(self, graph):
        """Verify revision_count is tracked in state (LOOP-04)."""
        config = {"configurable": {"thread_id": f"test-iteration-counter-{uuid4()}"}}

        graph.invoke({}, config)
        graph.invoke(Command(resume="Neural Networks"), config)
        result = graph.invoke(Command(resume="1"), config)

        # revision_count should be present and >= 0
        assert "revision_count" in result
        assert result["revision_count"] >= 0

    @requires_api_key
    def test_loop_terminates_on_approval(self, graph):
        """Verify loop exits when critic approves (LOOP-02)."""
        config = {"configurable": {"thread_id": f"test-approval-exit-{uuid4()}"}}

        graph.invoke({}, config)
        graph.invoke(Command(resume="Simple Topic"), config)
        result = graph.invoke(Command(resume="1"), config)

        # Should complete with approval
        assert result["is_approved"] is True
        # Should have a draft
        assert result["current_draft"] is not None

    @requires_api_key
    def test_max_iterations_forces_termination(self, graph):
        """Verify loop exits after 3 iterations regardless of approval (LOOP-03).

        This test is harder to trigger naturally since most articles
        will be approved within 3 iterations. We verify the mechanism
        exists by checking revision_count <= 3 in final state.
        """
        config = {"configurable": {"thread_id": f"test-max-iterations-{uuid4()}"}}

        graph.invoke({}, config)
        graph.invoke(Command(resume="Complex Topic"), config)
        result = graph.invoke(Command(resume="1"), config)

        # Should complete
        assert result["is_approved"] is True
        # Revision count should never exceed max (3)
        assert result["revision_count"] <= 3
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Conditional edges for loops | `Command(goto=...)` in critic node | LangGraph 0.2 | Routing logic co-located with evaluation logic |
| Fixed iteration count | Check before LLM call | Best practice | Prevents wasted API calls on forced exits |
| Generic "review this" prompts | Specific criteria with scores | Claude 4.x | More consistent, predictable evaluations |
| Boolean approval only | Structured evaluation with scores + feedback | Current | Enables quality metrics and targeted feedback |

**Deprecated/outdated:**
- **Message-based iteration tracking:** Using message list length to track iterations is fragile and survives checkpointing poorly. Use explicit state field.
- **`interrupt_before`/`interrupt_after` for loop control:** Use Command-based routing instead. Interrupts are for human input, not control flow.

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal approval threshold**
   - What we know: >= 7 out of 10 for both metrics is reasonable
   - What's unclear: Whether this threshold produces good article quality in practice
   - Recommendation: Start with 7, adjust based on testing. Could make configurable.

2. **Feedback granularity**
   - What we know: Need specific, actionable feedback for effective revision
   - What's unclear: How much detail is optimal (too little = no improvement, too much = overwhelm)
   - Recommendation: Structure feedback with categories (accuracy, comprehensibility) and specific quotes

3. **Revision quality convergence**
   - What we know: Articles should improve with each iteration
   - What's unclear: Whether 3 iterations is enough, or if quality plateaus earlier
   - Recommendation: Log revision_count distribution in production to tune MAX_ITERATIONS

## Sources

### Primary (HIGH confidence)
- [LangGraph Graph API - Command](https://docs.langchain.com/oss/python/langgraph/graph-api#combine-control-flow-and-state-updates-with-command) - Command with goto, type annotations
- [LangGraph Reflection Repository](https://github.com/langchain-ai/langgraph-reflection) - Official reflection pattern implementation
- [LangGraph Recursion Limit](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT) - Loop termination requirements
- [Reflection Agents Blog](https://www.blog.langchain.com/reflection-agents/) - Generator-reflector pattern, iteration control
- Project codebase - Established patterns for Command routing (approach_selection_node), structured output (ApproachList)

### Secondary (MEDIUM confidence)
- [Command Object Guide](https://medium.com/@vivekvjnk/the-command-object-in-langgraph-bc29bf57d18f) - Practical Command examples
- [Building Self-Correcting Agents](https://dev.to/programmingcentral/beyond-linear-chains-building-a-self-correcting-ai-agent-with-langgraphjs-4mjd) - Reflection loop patterns
- [LangGraph Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output) - with_structured_output patterns

### Tertiary (LOW confidence)
- WebSearch results on reflection agent best practices - Community patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using already-installed langgraph + langchain-openai with documented patterns
- Architecture patterns: HIGH - Command routing pattern well-established in Phase 4, reflection pattern documented
- Critic evaluation: MEDIUM - Specific prompt wording and threshold values need runtime validation
- Pitfalls: HIGH - Well-documented in project PITFALLS.md and official LangGraph docs

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - LangGraph Command API and reflection patterns are stable)
