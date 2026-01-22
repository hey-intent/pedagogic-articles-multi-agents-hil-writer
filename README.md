# Pedagogical Article Writer

A **learning project** to understand LangGraph patterns through a practical example: an AI agent that generates educational articles in the 3Blue1Brown style.

## What You'll Learn

This project demonstrates essential LangGraph concepts:

| Concept | What It Does | Where to Look |
|---------|--------------|---------------|
| **Human-in-the-Loop** | Pause execution for user input | `interrupt()` / `Command(resume=...)` |
| **Command Routing** | Dynamic flow control | `Command(goto="node_name")` |
| **Tool-Calling Agent** | LLM uses tools in a loop | `approach_agent.py` |
| **Structured Output** | Validate LLM responses with Pydantic | `schemas/approach.py` |
| **Reflection Loop** | Writer-Critic feedback cycle | `critic_agent.py` → `writer_agent.py` |
| **State Management** | TypedDict flowing through nodes | `state.py` |

## How It Works

```
User provides topic
       ↓
Agent researches the web
       ↓
Generates 3 pedagogical approaches
       ↓
User selects one (or rejects all)
       ↓
Writer drafts article
       ↓
Critic reviews → loops back if needed
       ↓
Article saved to output/
```

## Installation

**Prerequisites:** Python 3.12+ and [uv](https://github.com/astral-sh/uv)

```bash
# Clone and enter the project
git clone <repo-url>
cd pedagogical-article-writer

# Install dependencies
uv sync

# Configure API keys
cp .env.example .env
# Edit .env with your keys
```

### Required API Keys

| Variable | Where to Get It | Required |
|----------|-----------------|----------|
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai/) | Yes |
| `BRAVE_SEARCH_API_KEY` | [brave.com/search/api](https://brave.com/search/api/) | No (works without) |

## Run

```bash
uv run python -m src.main
```

Example session:

```
Starting Pedagogical Article Writer...
==================================================

Please enter a topic for your pedagogical article:
> how neural networks learn

Researching and generating approaches...

Generated Approaches:
1. "The Student Learning Analogy" - Neural networks as students
2. "The Sculptor's Marble" - Gradient descent as sculpting
3. "The Recipe Refinement" - Training as improving a recipe

Enter 1, 2, or 3 (or 'reject' to regenerate):
> 2

Generating article...

--- GENERATED ARTICLE ---
# How Neural Networks Learn: The Sculptor's Marble
...
```

## Project Structure

```
src/
├── main.py                 # Entry point - run this
├── config.py               # Environment configuration
├── graph/
│   ├── workflow.py         # Graph definition
│   ├── state.py            # State schema
│   └── nodes/
│       ├── topic_input.py          # HITL: get topic
│       ├── approach_agent.py       # Research + generate approaches
│       ├── approach_selection.py   # HITL: user picks approach
│       ├── writer_agent.py         # Write the article
│       ├── critic_agent.py         # Review and score
│       └── save_output.py          # Save to file
├── tools/
│   └── web_search.py       # Web search + page reader
└── schemas/
    └── approach.py         # Pydantic models
```

## Key Code Examples

### Human-in-the-Loop Pattern

```python
# topic_input.py - Pause for user input
user_topic = interrupt("Please enter a topic:")
return {"topic": user_topic}

# main.py - Handle the pause
result = graph.invoke(initial_state, config)
if "__interrupt__" in result:
    user_input = input("> ")
    result = graph.invoke(Command(resume=user_input), config)
```

### Command Routing

```python
# approach_selection.py - Route based on user choice
if user_choice == "reject":
    return Command(goto="approach_agent", update={"rejected_approaches": ...})
else:
    return Command(goto="writer_agent", update={"selected_approach_index": idx})
```

### Reflection Loop

```python
# critic_agent.py - Loop until quality passes
if score >= 7 or revision_count >= MAX_REVISIONS:
    return Command(goto="save_output", update={"is_approved": True})
else:
    return Command(goto="writer_agent", update={"critic_feedback": feedback})
```

## LangGraph Server (Optional)

Run as an API service with LangGraph Studio UI:

```bash
langgraph dev
```

Opens at `http://localhost:8123` with visual debugging.

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Human-in-the-Loop Guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)
- [OpenRouter Models](https://openrouter.ai/models)
