# Phase 5: Writer Agent - Research

**Researched:** 2026-01-19
**Domain:** LangGraph Node Implementation, Claude 4.x Prompt Engineering, 3Blue1Brown Pedagogical Style
**Confidence:** HIGH

## Summary

Phase 5 transforms the placeholder `writer_agent_node` into an LLM-powered agent that drafts articles using the selected pedagogical approach. Unlike the approach agent (Phase 3), the writer agent does NOT need tools - it receives all necessary context (topic, selected approach) from state and produces markdown content via a single LLM invocation.

The implementation follows the established project pattern: nodes receive full state, invoke the LLM, and return partial dict updates. The writer agent is simpler than the approach agent because it has no tool-calling loop - just a well-crafted system prompt, the topic/approach context as user message, and one `model.invoke()` call that returns the article draft.

The key challenge is prompt engineering for 3Blue1Brown pedagogical style. This style emphasizes: (1) visual thinking and concrete examples even in text, (2) shift-in-perspective moments that make complex ideas suddenly clear, (3) building intuition before formalism, and (4) connecting to familiar concepts through metaphors. The selected approach already contains a metaphor - the writer should weave this throughout the article.

**Primary recommendation:** Implement `writer_agent_node` as a simple LLM node (no tools) with a carefully crafted system prompt that establishes 3Blue1Brown style. Use `ChatAnthropic` with `claude-sonnet-4-20250514` for consistency with approach agent. Return markdown article in `current_draft` field. Prepare for Phase 6 iteration by accepting optional `critic_feedback` from state.

## Standard Stack

The established libraries/tools for this phase:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-anthropic | latest | LLM for article generation | Provides `ChatAnthropic` with strong long-form writing capabilities. Already used in approach agent. |
| langchain-core | 1.2.7 | Message types | Provides `SystemMessage`, `HumanMessage` for structured prompts. Already installed. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| N/A | - | - | Writer agent needs no additional libraries beyond what's already installed. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single LLM call | Tool-calling agent | Tools unnecessary - all context comes from state |
| Markdown output | Structured output (Pydantic) | Free-form markdown is more flexible for articles |
| claude-sonnet-4 | claude-opus-4-5 | Opus has better creative writing but higher cost; Sonnet sufficient for reference implementation |

**Installation:**
```bash
# No new dependencies required
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── graph/
│   ├── __init__.py
│   ├── state.py           # ArticleState - already has current_draft field
│   ├── nodes.py           # writer_agent_node implementation goes here
│   └── workflow.py        # No changes needed - writer_agent already wired
├── tools/                 # Not used by writer agent
├── schemas/               # Not used by writer agent (free-form markdown output)
└── main.py
```

### Pattern 1: Simple LLM Node (No Tools)

**What:** A node that invokes the LLM once with context from state and returns the result.

**When to use:** When the agent has all information it needs from state and doesn't need external tools.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/workflows-agents
from langchain_anthropic import ChatAnthropic
from src.graph.state import ArticleState


def writer_agent_node(state: ArticleState) -> dict:
    """Draft article using selected pedagogical approach.

    This is a simple LLM node - no tools needed. All context (topic,
    selected approach) comes from state. Returns markdown article.
    """
    topic = state["topic"]
    approaches = state["approaches"]
    selected_idx = state["selected_approach_index"]
    approach = approaches[selected_idx]

    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Write an article about: {topic}\n\nUsing this pedagogical approach:\n{format_approach(approach)}"},
    ]

    response = model.invoke(messages)

    return {"current_draft": response.content}
```

### Pattern 2: System Prompt for 3Blue1Brown Style

**What:** A detailed system prompt that establishes the pedagogical writing style.

**When to use:** When you need the LLM to write in a specific voice/style consistently.

**Example:**
```python
WRITER_SYSTEM_PROMPT = """You are a pedagogical writer who creates accessible, engaging articles in the style of 3Blue1Brown. Your goal is to make complex topics intuitive and enjoyable to learn.

## Writing Style Principles

1. **Build intuition before formalism**: Start with concrete examples and visuals (described in text), then introduce formal definitions. Readers should feel they "could have discovered this themselves."

2. **Use the provided metaphor throughout**: The pedagogical approach includes a metaphor - weave this metaphor as a recurring thread throughout the article, referring back to it when introducing new concepts.

3. **Create "shift in perspective" moments**: Structure explanations so readers experience that satisfying "aha!" moment when a new viewpoint suddenly makes everything click.

4. **Ground abstract ideas in familiar experience**: Connect every abstract concept to something tangible and relatable. Use phrases like "Imagine..." and "Think of it like..."

5. **Be conversational but precise**: Write as if explaining to a curious friend. Avoid jargon, but when technical terms are necessary, introduce them naturally with clear context.

## Article Structure

Write a markdown article with:
- An engaging title that hints at the core insight
- An introduction that poses an intriguing question or problem
- Body sections that progressively build understanding using the metaphor
- A conclusion that ties everything together and suggests further exploration

## Output Format

Return your article as well-formatted markdown with:
- `#` for the main title
- `##` for major sections
- `###` for subsections if needed
- Clear paragraph breaks
- Occasional *emphasis* for key insights
- No code blocks unless the topic specifically involves code"""
```

### Pattern 3: Preparing for Iteration (Phase 6)

**What:** Design the node to accept optional critic feedback for revisions.

**When to use:** When the node will be called multiple times in a revision loop.

**Example:**
```python
def writer_agent_node(state: ArticleState) -> dict:
    """Draft or revise article based on state.

    On first call: current_draft is None, writes fresh article.
    On revision calls (Phase 6): critic_feedback in state, revises draft.
    """
    topic = state["topic"]
    approach = state["approaches"][state["selected_approach_index"]]

    # Check if this is a revision (critic feedback present)
    critic_feedback = state.get("critic_feedback")  # Will be added in Phase 6
    current_draft = state.get("current_draft")

    if critic_feedback and current_draft:
        # Revision mode: incorporate feedback
        user_content = f"""Revise this article based on the critic's feedback.

Original article:
{current_draft}

Critic feedback:
{critic_feedback}

Topic: {topic}
Approach: {approach['title']} - {approach['metaphor']}

Provide the complete revised article."""
    else:
        # Initial draft mode
        user_content = f"""Write an article about: {topic}

Using this pedagogical approach:
Title: {approach['title']}
Description: {approach['description']}
Metaphor: {approach['metaphor']}
Why effective: {approach['why_effective']}"""

    model = ChatAnthropic(model="claude-sonnet-4-20250514")
    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    response = model.invoke(messages)
    return {"current_draft": response.content}
```

### Anti-Patterns to Avoid

- **Adding tools unnecessarily:** The writer agent has all context from state - don't add web search or other tools.
- **Using structured output:** Free-form markdown is more appropriate for creative writing than Pydantic schemas.
- **Ignoring the selected approach:** The whole point is to use the approach - don't let the LLM ignore it.
- **Over-engineering for Phase 6:** Keep the initial implementation simple; add revision logic when needed.
- **Verbose system prompts:** Claude 4.x models are concise by default; overly detailed prompts can constrain creativity.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM invocation | Raw HTTP to Anthropic API | `ChatAnthropic.invoke()` | Handles auth, retries, message formatting |
| Message construction | Manual dict building | LangChain message types | Type safety, consistency with project |
| Markdown formatting | Custom formatting logic | LLM output directly | Claude produces clean markdown natively |

**Key insight:** The writer agent is intentionally simple. The complexity is in the prompt engineering, not the code. Don't add abstractions that aren't needed.

## Common Pitfalls

### Pitfall 1: Ignoring the Selected Approach

**What goes wrong:** LLM writes a generic article that doesn't use the selected metaphor or approach.

**Why it happens:** System prompt doesn't emphasize using the approach strongly enough.

**How to avoid:** Explicitly state in system prompt: "You MUST use the provided metaphor throughout the article." Include the approach details prominently in the user message.

**Warning signs:** Article doesn't mention the metaphor, or only mentions it once.

### Pitfall 2: Article Too Short

**What goes wrong:** LLM produces a 200-word summary instead of a full article.

**Why it happens:** Claude 4.x models are trained to be concise; may interpret "article" as "brief summary."

**How to avoid:** Specify desired length in prompt: "Write a substantial article of approximately 800-1200 words." Or: "Write a thorough, educational article with multiple sections."

**Warning signs:** Output is under 500 words, lacks depth.

### Pitfall 3: Too Academic/Formal

**What goes wrong:** Article reads like a textbook or Wikipedia entry, not 3Blue1Brown style.

**Why it happens:** LLM defaults to formal explanatory writing.

**How to avoid:** System prompt should emphasize conversational tone: "Write as if explaining to a curious friend." Include examples of the desired voice.

**Warning signs:** Heavy use of passive voice, no "you" or "imagine," no questions posed to reader.

### Pitfall 4: Missing State Fields

**What goes wrong:** Node crashes with KeyError when accessing state fields.

**Why it happens:** Not handling case where optional fields are None.

**How to avoid:** Use `state.get("field")` with default values. Check required fields explicitly.

**Warning signs:** KeyError exceptions in tests.

### Pitfall 5: Max Tokens Exceeded

**What goes wrong:** Response is cut off mid-sentence.

**Why it happens:** Default max_tokens may be too low for long articles.

**How to avoid:** Set explicit `max_tokens=4096` or higher when creating ChatAnthropic instance.

**Warning signs:** Articles ending abruptly, incomplete sentences.

## Code Examples

Verified patterns from official sources:

### Complete Writer Agent Node

```python
# Source: Synthesized from LangChain docs and Claude best practices
# File: src/graph/nodes.py (addition to existing file)

from langchain_anthropic import ChatAnthropic
from src.graph.state import ArticleState


# System prompt establishing 3Blue1Brown pedagogical style.
# Key principles: intuition before formalism, metaphor as thread,
# shift-in-perspective moments, conversational but precise.
WRITER_SYSTEM_PROMPT = """You are a pedagogical writer creating accessible, engaging articles in the style of 3Blue1Brown. Your goal is to make complex topics intuitive and enjoyable.

## Core Principles

1. **Build intuition first**: Start with concrete examples before definitions. Help readers feel they "could have discovered this themselves."

2. **Use the metaphor throughout**: The approach includes a metaphor - weave it as a recurring thread, referring back when introducing new concepts.

3. **Create "aha!" moments**: Structure explanations so readers experience that satisfying shift in perspective when everything clicks.

4. **Ground abstractions in experience**: Connect every abstract concept to something tangible. Use "Imagine..." and "Think of it like..."

5. **Be conversational but precise**: Write as if explaining to a curious friend. Introduce technical terms naturally with clear context.

## Article Structure

Write a well-structured markdown article with:
- An engaging title that hints at the core insight
- An introduction that poses an intriguing question
- Body sections that progressively build understanding using the metaphor
- A conclusion that ties everything together

Aim for approximately 800-1200 words - substantial enough to build real understanding.

## Output Format

Return clean markdown:
- `#` for the title
- `##` for major sections
- Clear paragraph breaks
- *Emphasis* for key insights"""


def writer_agent_node(state: ArticleState) -> dict:
    """Draft article using selected pedagogical approach.

    This is a simple LLM node - no tools needed. All context (topic,
    selected approach) comes from state. Returns markdown article
    stored in current_draft.

    In Phase 6, this node will also handle revisions when critic_feedback
    is present in state.

    Args:
        state: Current graph state with topic, approaches, selected_approach_index.

    Returns:
        Dict with 'current_draft' field containing the markdown article.
    """
    topic = state["topic"]
    approaches = state["approaches"]
    selected_idx = state["selected_approach_index"]
    approach = approaches[selected_idx]

    # Format approach details for the prompt
    approach_text = f"""Title: {approach['title']}

Description: {approach['description']}

Core Metaphor: {approach['metaphor']}

Why This Works: {approach['why_effective']}"""

    user_content = f"""Write an educational article about: {topic}

Use this pedagogical approach throughout the article:

{approach_text}

Remember to weave the metaphor throughout your explanation, returning to it when introducing new concepts."""

    # Create model with explicit max_tokens to ensure full article generation
    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
    )

    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    response = model.invoke(messages)

    return {"current_draft": response.content}
```

### Testing the Writer Agent

```python
# Source: Project test patterns
# File: tests/test_graph.py (addition to existing file)

import os
from uuid import uuid4

import pytest
from langgraph.types import Command

from src.graph import create_compiled_graph


requires_anthropic_api = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set - skipping integration test"
)


class TestWriterAgent:
    """Test suite for Phase 5: Writer agent article generation."""

    @requires_anthropic_api
    def test_writer_produces_markdown_draft(self, graph):
        """Verify writer agent produces non-empty markdown content."""
        config = {"configurable": {"thread_id": f"test-writer-draft-{uuid4()}"}}

        # Start graph, provide topic
        graph.invoke({}, config)
        graph.invoke(Command(resume="Machine Learning"), config)

        # Select approach 1
        result = graph.invoke(Command(resume="1"), config)

        # Writer should have produced a draft
        assert result["current_draft"] is not None
        assert len(result["current_draft"]) > 500  # Substantial content
        assert "#" in result["current_draft"]  # Markdown heading

    @requires_anthropic_api
    def test_draft_incorporates_topic(self, graph):
        """Verify the draft references the topic."""
        config = {"configurable": {"thread_id": f"test-writer-topic-{uuid4()}"}}

        graph.invoke({}, config)
        graph.invoke(Command(resume="Quantum Computing"), config)
        result = graph.invoke(Command(resume="1"), config)

        # Draft should mention the topic
        draft_lower = result["current_draft"].lower()
        assert "quantum" in draft_lower

    @requires_anthropic_api
    def test_draft_uses_selected_approach(self, graph):
        """Verify the draft incorporates the selected approach's metaphor."""
        config = {"configurable": {"thread_id": f"test-writer-approach-{uuid4()}"}}

        graph.invoke({}, config)
        graph.invoke(Command(resume="Neural Networks"), config)
        result = graph.invoke(Command(resume="1"), config)

        # The approach's metaphor should appear in the draft
        selected_approach = result["approaches"][result["selected_approach_index"]]
        # Check that key words from metaphor appear
        # (exact match may not occur, but related concepts should)
        assert result["current_draft"] is not None
        assert len(result["current_draft"]) > 500
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Complex prompts with many examples | Concise, explicit instructions | Claude 4.x | Simpler prompts work better; over-prompting can constrain |
| Requesting "detailed" output | Specifying word count or depth | Claude 4.5 | More direct control over output length |
| Role-playing prompts | Clear system prompts with principles | Claude 4.x | System prompts are more effective than "act as" |
| Markdown formatting instructions | Native markdown output | Claude 4.x | Claude produces clean markdown by default |

**Deprecated/outdated:**
- **Long few-shot examples for style:** Claude 4.x pays close attention to examples and may over-fit; use principles instead.
- **"Do not" instructions:** "Tell Claude what to do instead of what not to do" - per official best practices.

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal article length**
   - What we know: 800-1200 words is reasonable for educational articles
   - What's unclear: Best length for this specific use case
   - Recommendation: Start with 800-1200 words; adjust based on output quality

2. **Handling very technical topics**
   - What we know: 3Blue1Brown style works great for math/physics
   - What's unclear: How well it adapts to other domains (e.g., business, humanities)
   - Recommendation: Test with varied topics; style principles should transfer

3. **Metaphor integration depth**
   - What we know: Metaphor should be woven throughout
   - What's unclear: How strongly to enforce this in prompts
   - Recommendation: Emphasize it clearly but don't over-constrain

## Sources

### Primary (HIGH confidence)
- [Claude 4 Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices) - Official Anthropic guidance on Claude 4.x prompting
- [Prompt Engineering Overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview) - Core prompting techniques
- [LangChain Workflows and Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - Node patterns for LangGraph
- [ChatAnthropic Documentation](https://docs.langchain.com/oss/python/integrations/chat/anthropic) - LangChain Anthropic integration
- [3Blue1Brown About](https://www.3blue1brown.com/about) - Official description of pedagogical approach

### Secondary (MEDIUM confidence)
- [Long Context Prompting](https://www.anthropic.com/news/prompting-long-context) - Techniques for better recall and output
- [3Blue1Brown Wikipedia](https://en.wikipedia.org/wiki/3Blue1Brown) - Background on teaching style

### Tertiary (LOW confidence)
- WebSearch results on 3Blue1Brown style characteristics - Community descriptions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Same libraries as approach agent, well-documented
- Architecture patterns: HIGH - Simple node pattern is well-established
- Prompt engineering: MEDIUM - 3Blue1Brown style synthesis based on multiple sources
- Pitfalls: MEDIUM - Based on Claude 4.x behavior documentation

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - prompting patterns are stable)
