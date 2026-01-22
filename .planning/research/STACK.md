# Technology Stack

**Project:** Pedagogical Article Writer (LangGraph Multi-Agent)
**Researched:** 2026-01-18
**Overall Confidence:** HIGH (versions verified via PyPI, patterns verified via official LangChain docs)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| langgraph | 1.0.6 | Agent orchestration, state machine | The official LangChain framework for multi-agent workflows. Provides `StateGraph`, `interrupt()`, `Command`, and checkpointing out of the box. Reached 1.0 milestone with production-ready features. | HIGH |
| langchain-core | 1.2.7 | Base abstractions (messages, prompts, output parsers) | Minimal dependency that provides the core building blocks. Avoids pulling in the full `langchain` package when you only need primitives. | HIGH |
| langchain | 1.2.6 | Full LangChain utilities (optional) | Only if you need chains, document loaders, or other LangChain utilities. For this project, `langchain-core` may suffice. | MEDIUM |

### LLM Provider Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| langchain-anthropic | latest (check PyPI) | Claude integration | First-class support for Claude models including tool calling. Recommended for pedagogical clarity due to Claude's instruction-following. | HIGH |
| langchain-openai | 1.1.7 | OpenAI/GPT integration | Alternative provider. Well-documented, widely used. Good for users who prefer GPT models. | HIGH |

**Recommendation:** Pick ONE provider for the reference implementation to keep it focused. Claude (via `langchain-anthropic`) recommended for pedagogical projects due to clear reasoning traces.

### Persistence / Checkpointing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| langgraph (InMemorySaver) | built-in | Development/testing checkpointer | Zero setup. Perfect for learning and prototyping. State persists in memory only. | HIGH |
| langgraph-checkpoint-postgres | latest | Production checkpointer | For durable state across restarts. Not needed for a pedagogical project but good to mention for completeness. | MEDIUM |

**Recommendation:** Use `InMemorySaver` exclusively for this learning project. It demonstrates the checkpointing pattern without infrastructure complexity.

### Python Environment

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.11 or 3.12 | Runtime | LangGraph 1.0.6 requires Python >=3.10. 3.11/3.12 offer best balance of features, performance, and library compatibility. 3.13 supported but some libraries may lag. | HIGH |
| uv | latest | Package manager | Fast, modern Python package manager. Handles virtual environments and dependency resolution better than pip. Recommended by many in the Python community. | MEDIUM |
| pip | latest | Package manager (alternative) | Traditional choice. Works fine if you prefer it. | HIGH |

### Development Tools

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| python-dotenv | latest | Environment variables | Load API keys from `.env` files. Standard practice for local development. | HIGH |
| pydantic | 2.x | Data validation, typed state | LangGraph state benefits from Pydantic models. Type hints improve clarity for pedagogical code. | HIGH |

## What NOT to Use

| Technology | Why Avoid |
|------------|-----------|
| `langchain` (full package) when `langchain-core` suffices | Unnecessary dependencies. For a focused multi-agent workflow, you often only need core abstractions. |
| `interrupt_before`/`interrupt_after` (old pattern) | Deprecated in favor of the `interrupt()` function as of LangGraph 0.2.31. Use `interrupt()` for human-in-the-loop. |
| Custom state persistence | Don't build your own. Use LangGraph's built-in checkpointers (`InMemorySaver` for dev, Postgres for prod). |
| LangServe | Not needed for this project. LangServe is for deploying chains as APIs. The pedagogical focus is on the workflow itself. |
| LangSmith | Optional observability platform. Nice for debugging but adds complexity. Mention as optional enhancement. |
| AutoGen, CrewAI, other frameworks | Scope creep. This project demonstrates LangGraph specifically. |

## Installation

### Minimal Install (Recommended for Pedagogical Project)

```bash
# Using pip
pip install langgraph langchain-core langchain-anthropic python-dotenv pydantic

# Using uv
uv pip install langgraph langchain-core langchain-anthropic python-dotenv pydantic
```

### With OpenAI Alternative

```bash
pip install langgraph langchain-core langchain-openai python-dotenv pydantic
```

### Requirements.txt

```
langgraph>=1.0.6
langchain-core>=1.2.7
langchain-anthropic>=0.3.0  # Check PyPI for exact latest
python-dotenv>=1.0.0
pydantic>=2.0.0
```

## Key Patterns Enabled by This Stack

### 1. Human-in-the-Loop via `interrupt()`

```python
from langgraph.types import interrupt, Command

def human_approval_node(state):
    # Pause execution, wait for human input
    response = interrupt("Do you approve this draft? (yes/no)")
    return {"human_approved": response == "yes"}
```

Resume with:
```python
graph.invoke(Command(resume="yes"), thread_config)
```

### 2. Agent Handoffs via State Transitions

```python
from langgraph.graph import StateGraph, END

def router(state):
    if state["needs_critique"]:
        return "critic"
    return END

graph.add_conditional_edges("writer", router, ["critic", END])
```

### 3. Checkpointing for Durability

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

# All state automatically persisted
thread = {"configurable": {"thread_id": "article-1"}}
app.invoke(initial_state, thread)
```

## Version Verification Sources

| Package | Version | Source | Verified Date |
|---------|---------|--------|---------------|
| langgraph | 1.0.6 | [PyPI](https://pypi.org/project/langgraph/) | 2026-01-18 |
| langchain | 1.2.6 | [PyPI](https://pypi.org/project/langchain/) | 2026-01-18 |
| langchain-core | 1.2.7 | [PyPI](https://pypi.org/project/langchain-core/) | 2026-01-18 |
| langchain-openai | 1.1.7 | Web search results | 2026-01-18 |

## Architecture Implications

This stack enables the target workflow:

```
Topic Selection --> Approach Agent --> [INTERRUPT: Select Approach] --> Writer Agent --> Critic Agent --> [Loop until approved] --> Save
```

- **StateGraph**: Models the workflow as a directed graph with typed state
- **interrupt()**: Pauses at approach selection for human input
- **Conditional edges**: Routes from critic back to writer if not approved
- **InMemorySaver**: Preserves state across the interrupt/resume cycle

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Core versions (langgraph, langchain) | HIGH | Verified via PyPI on 2026-01-18 |
| Human-in-the-loop pattern | HIGH | Documented in official LangChain blog and docs |
| Provider packages | MEDIUM | Versions from search results; verify exact version on install |
| Development tools (uv, dotenv) | HIGH | Standard Python ecosystem practices |

## Open Questions for Implementation

1. **Exact langchain-anthropic version**: Verify latest on PyPI at install time
2. **State schema design**: Will need to be defined during implementation
3. **LangSmith integration**: Optional; decide if debugging observability is worth the complexity for a pedagogical project

---

## Sources

- [LangGraph PyPI](https://pypi.org/project/langgraph/) - Version 1.0.6
- [LangChain PyPI](https://pypi.org/project/langchain/) - Version 1.2.6
- [LangChain and LangGraph 1.0 Announcement](https://www.blog.langchain.com/langchain-langgraph-1dot0/)
- [Human-in-the-Loop with interrupt() Blog Post](https://www.blog.langchain.com/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt/)
- [LangGraph Human-in-the-Loop Docs](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/wait-user-input/)
- [LangGraph Multi-Agent Workflows](https://www.blog.langchain.com/langgraph-multi-agent-workflows/)
