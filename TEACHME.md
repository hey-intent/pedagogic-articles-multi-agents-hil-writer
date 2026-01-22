# TEACHME: Pedagogical Article Writer

A hands-on guide to understanding LangGraph through a real-world multi-agent system.

---

## What This Project Teaches

This project is a **LangGraph reference implementation** that demonstrates how to build production-quality multi-agent AI systems. It generates educational articles in the style of 3Blue1Brown through a coordinated workflow of specialized agents.

### Core LangGraph Patterns Covered

| Pattern | Where to Find It |
|---------|------------------|
| Human-in-the-Loop (HITL) | `topic_input.py`, `approach_selection.py` |
| Interrupt/Resume | `main.py` |
| Dynamic Command Routing | `approach_selection.py`, `critic_agent.py` |
| Inline Tool-Calling Loop | `approach_agent.py` |
| Structured LLM Output | `approach_agent.py`, `critic_agent.py` |
| Reflection Loop | `critic_agent.py` ↔ `writer_agent.py` |
| State Reducers | `state.py` |
| Checkpointing | `workflow.py` |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKFLOW OVERVIEW                               │
└─────────────────────────────────────────────────────────────────────────────┘

User provides topic (HITL)
         │
         ▼
┌─────────────────┐
│  Approach Agent │ ──► researches topic + generates 3 approaches
└────────┬────────┘
         │
         ▼
User selects approach (HITL)
         │
    ┌────┴────┐
    │ reject  │──────────────────────────┐
    └────┬────┘                          │
         │ select                        │ loop back with
         ▼                               │ rejection context
┌─────────────────┐                      │
│  Writer Agent   │◄─────────────────────┘
└────────┬────────┘
         │ draft
         ▼
┌─────────────────┐
│  Critic Agent   │
└────────┬────────┘
         │
    ┌────┴────┐
    │ reject  │──► feedback ──► Writer (revision mode)
    └────┬────┘
         │ approve
         ▼
┌─────────────────┐
│   Save Output   │ ──► markdown file
└─────────────────┘
```

---

## Project Structure

```
src/
├── main.py                    # Entry point with HITL orchestration
├── config.py                  # Configuration via pydantic-settings
├── graph/
│   ├── workflow.py            # Graph construction (StateGraph)
│   ├── state.py               # ArticleState TypedDict schema
│   └── nodes/
│       ├── topic_input.py          # HITL: User provides topic
│       ├── approach_agent.py       # LLM: generates 3 approaches
│       ├── approach_selection.py   # HITL: User selects/rejects
│       ├── writer_agent.py         # LLM: drafts article
│       ├── critic_agent.py         # LLM: evaluates + routes
│       └── save_output.py          # File output
├── tools/
│   ├── web_search.py          # Brave Search API tool
│   └── web_reader.py          # Web page extractor
└── schemas/
    ├── approaches.py          # Pydantic: PedagogicalApproach
    └── critic.py              # Pydantic: CriticEvaluation
```

---

## Key Concepts Explained

### 1. Human-in-the-Loop with Interrupt/Resume

LangGraph's `interrupt()` pauses execution and returns control to the caller. The caller then resumes with `Command(resume=value)`.

**In `topic_input.py`:**
```python
from langgraph.types import interrupt, Command

def topic_input_node(state: ArticleState):
    # This PAUSES the graph and returns to main.py
    topic = interrupt("Please provide a topic for the article:")

    # When resumed, topic contains the user's input
    return Command(update={"topic": topic}, goto="approach_agent")
```

**In `main.py`:**
```python
# First invoke hits the interrupt
result = graph.invoke(initial_state, config)

if "__interrupt__" in result:
    user_topic = input("> ")
    # Resume with the user's input
    result = graph.invoke(Command(resume=user_topic), config)
```

---

### 2. Dynamic Routing with Command

Instead of pre-defined edges, `Command(goto="node_name")` enables runtime routing decisions.

**In `approach_selection.py`:**
```python
def approach_selection_node(state: ArticleState):
    user_selection = interrupt(prompt)

    if user_selection == "reject":
        # Dynamic route BACK to approach_agent
        return Command(
            update={"rejected_approaches": accumulated_rejections},
            goto="approach_agent"
        )
    else:
        # Dynamic route FORWARD to writer_agent
        return Command(
            update={"selected_approach_index": int(user_selection) - 1},
            goto="writer_agent"
        )
```

---

### 3. Inline Tool-Calling Loop

Agents can call tools in a loop without leaving the node.

**In `approach_agent.py`:**
```python
def approach_agent_node(state: ArticleState):
    model_with_tools = model.bind_tools([web_search, read_webpage])
    messages = [system_prompt, user_prompt]

    # Inline loop: agent researches until satisfied
    for iteration in range(3):
        response = model_with_tools.invoke(messages)

        if response.tool_calls:
            # Execute tools and append results
            for tool_call in response.tool_calls:
                result = execute_tool(tool_call)
                messages.append(ToolMessage(content=result, ...))
        else:
            break  # Agent done researching

    # Get structured output
    return model.with_structured_output(ApproachList).invoke(messages)
```

---

### 4. Structured Output with Pydantic

Ensure LLM responses match expected schemas.

**In `schemas/approaches.py`:**
```python
from pydantic import BaseModel, Field

class PedagogicalApproach(BaseModel):
    title: str = Field(description="A compelling title for this approach")
    core_metaphor: str = Field(description="The central analogy or metaphor")
    key_insights: list[str] = Field(description="3-5 main insights to convey")
    target_audience: str = Field(description="Who benefits most from this approach")
```

**Usage:**
```python
model_structured = model.with_structured_output(ApproachList)
result = model_structured.invoke(messages)  # Returns validated Pydantic object
```

---

### 5. Reflection Loop with Iteration Limits

The critic-writer loop continues until approval or max iterations.

**In `critic_agent.py`:**
```python
def critic_agent_node(state: ArticleState):
    revision_count = state.get("revision_count", 0)

    # Check limit BEFORE LLM call (saves tokens)
    if revision_count >= 3:
        return Command(update={"is_approved": True}, goto="save_output")

    evaluation = model.with_structured_output(CriticEvaluation).invoke(prompt)

    if evaluation.approved:
        return Command(update={"is_approved": True}, goto="save_output")
    else:
        return Command(
            update={
                "critic_feedback": evaluation.feedback,
                "revision_count": revision_count + 1
            },
            goto="writer_agent"  # Loop back for revision
        )
```

---

### 6. State Management with TypedDict

State flows through all nodes. Each node receives full state, returns only changes.

**In `state.py`:**
```python
from typing import TypedDict, Annotated

def keep_last_non_none(old, new):
    """Prevents None from overwriting valid values"""
    return new if new is not None and new != "" else old

class ArticleState(TypedDict):
    topic: Annotated[str | None, keep_last_non_none]
    approaches: list[dict] | None
    selected_approach_index: int | None
    rejected_approaches: list[dict] | None
    current_draft: str | None
    critic_feedback: str | None
    is_approved: bool
    revision_count: int
    output_path: str | None
```

---

### 7. Building the Graph

**In `workflow.py`:**
```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

def build_graph():
    graph = StateGraph(ArticleState)

    # Add nodes
    graph.add_node("topic_input", topic_input_node)
    graph.add_node("approach_agent", approach_agent_node)
    graph.add_node("approach_selection", approach_selection_node)
    graph.add_node("writer_agent", writer_agent_node)
    graph.add_node("critic_agent", critic_agent_node)
    graph.add_node("save_output", save_output_node)

    # Add edges (note: Command routing handles most transitions)
    graph.add_edge(START, "topic_input")
    graph.add_edge("writer_agent", "critic_agent")
    graph.add_edge("save_output", END)

    # Compile with checkpointer for state persistence
    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

---

## Two-Mode Node Design

The writer agent handles both initial drafts and revisions in a single node.

**In `writer_agent.py`:**
```python
def writer_agent_node(state: ArticleState):
    critic_feedback = state.get("critic_feedback")
    current_draft = state.get("current_draft")

    if critic_feedback and current_draft:
        # REVISION MODE
        prompt = f"Revise this article based on feedback:\n{current_draft}\n\nFeedback: {critic_feedback}"
    else:
        # INITIAL DRAFT MODE
        approach = state["approaches"][state["selected_approach_index"]]
        prompt = f"Write an article about {state['topic']} using: {approach}"

    response = model.invoke([system_prompt, prompt])
    return {"current_draft": response.content}
```

---

## Running the Project

### Prerequisites

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - OPENROUTER_API_KEY (required)
# - BRAVE_SEARCH_API_KEY (optional, for web search)
```

### Execution

```bash
uv run python -m src.main
```

The workflow will:
1. Ask for a topic
2. Generate 3 pedagogical approaches
3. Ask you to select one (or reject all)
4. Write an article draft
5. Critique and revise until approved
6. Save to `output/article_*.md`

---

## Learning Path

### Phase 1: Foundation
- Read `state.py` to understand the data model
- Read `workflow.py` to see how nodes connect

### Phase 2: Human-in-the-Loop
- Study `topic_input.py` for basic interrupt pattern
- Study `approach_selection.py` for interrupt + dynamic routing

### Phase 3: Agent Design
- Study `approach_agent.py` for inline tool-calling loops
- Study `writer_agent.py` for two-mode node design

### Phase 4: Reflection
- Study `critic_agent.py` for reflection loop pattern
- Trace the critic → writer → critic cycle

### Phase 5: Integration
- Read `main.py` to see full orchestration
- Follow thread_id usage for state persistence

---

## Design Decisions

### Why TypedDict over Pydantic for State?
- Lighter weight (no runtime validation on every state update)
- Faster for frequently-mutated state objects
- Pydantic still used for LLM output validation where it matters

### Why Inline Tool Loops vs. Separate Tool Nodes?
- Keeps related logic together
- Avoids graph complexity for tool execution
- Agent controls iteration (can stop when satisfied)

### Why Command Routing vs. Conditional Edges?
- More flexible (runtime decisions)
- Cleaner code (logic stays in nodes)
- Easier to add new routes without graph changes

### Why Check Iteration Limit Before LLM Call?
- Saves tokens on the final iteration
- Prevents wasted API calls
- Cleaner termination logic

---

## Common Patterns Recap

| Pattern | Code Example |
|---------|--------------|
| Pause for user input | `value = interrupt(prompt)` |
| Resume with value | `graph.invoke(Command(resume=value), config)` |
| Route to specific node | `return Command(goto="node_name")` |
| Update state and route | `return Command(update={...}, goto="node")` |
| Structured LLM output | `model.with_structured_output(Schema).invoke(...)` |
| Tool-equipped model | `model.bind_tools([tool1, tool2])` |
| State persistence | `graph.compile(checkpointer=InMemorySaver())` |
| Thread isolation | `config = {"configurable": {"thread_id": "unique-id"}}` |

---

## Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Tool Documentation](https://python.langchain.com/docs/modules/agents/tools/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## Summary

This project demonstrates that multi-agent systems can be:
- **Readable**: Each node has a single responsibility
- **Testable**: Nodes are pure functions of state
- **Maintainable**: Command routing keeps logic in nodes
- **Production-ready**: Checkpointing, error handling, iteration limits

Use this as a template for your own LangGraph projects.
