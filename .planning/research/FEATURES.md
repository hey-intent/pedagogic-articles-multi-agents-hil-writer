# Feature Landscape

**Domain:** LangGraph Multi-Agent Reference Implementation (Pedagogical Article Writer)
**Researched:** 2026-01-18
**Confidence:** HIGH (based on official LangGraph documentation and current API)

## Table Stakes

Features users expect from a LangGraph multi-agent reference implementation. Missing = example feels incomplete or unusable for learning.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **StateGraph with TypedDict** | Core LangGraph pattern; every tutorial starts here | Low | Use explicit TypedDict schema, not ad-hoc dicts |
| **Named nodes with clear functions** | Graph readability; learners need to see the structure | Low | One function per node, descriptive names |
| **Conditional edges** | Essential for any non-trivial workflow; demonstrates decision-making | Low | Show routing based on state (e.g., loop vs exit) |
| **START/END constants** | Standard LangGraph idiom for entry/exit points | Low | Always use these, not magic strings |
| **Compilation and invocation** | Basic execution pattern | Low | Show `graph.compile()` then `graph.invoke()` |
| **Human-in-the-loop via interrupt()** | Core project requirement; modern LangGraph pattern | Medium | Use `interrupt()` function (not deprecated `interrupt_before/after`). Requires checkpointer. |
| **Checkpointer for state persistence** | Required for interrupt/resume; enables HITL | Low | Use `MemorySaver` for tutorial (not production-grade but simple) |
| **Command object for resumption** | How to resume after interrupt | Low | `Command(resume=value)` pattern |
| **Thread ID configuration** | Enables state persistence across calls | Low | `config={"configurable": {"thread_id": "..."}}` |
| **Reflection loop (writer-critic)** | Core project requirement; key multi-agent pattern | Medium | Generate -> Reflect -> Conditional loop back |
| **Agent handoff via state transition** | Core project requirement; shows multi-agent coordination | Medium | State variable controls active agent; conditional edges route |
| **Clear state schema** | Learners need to understand what flows through the graph | Low | Document each field's purpose in TypedDict |
| **Print/log progress** | Visibility into what's happening | Low | Simple print statements showing workflow progress |

## Differentiators

Features that make this example particularly valuable as a learning resource. Not expected, but significantly increase pedagogical value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Explicit iteration counter** | Shows bounded loops; prevents infinite recursion | Low | `iteration_count` in state with max check |
| **Separate prompt templates** | Demonstrates prompt engineering patterns | Low | Keep prompts in constants or separate section |
| **Typed Message handling** | Shows proper LangChain message types | Low | Use `HumanMessage`, `AIMessage`, `SystemMessage` explicitly |
| **MessagesState pattern** | Built-in message list management with reducers | Medium | Shows `Annotated[list, add_messages]` pattern |
| **Graph visualization** | Generates diagram of the workflow | Low | `graph.get_graph().draw_mermaid()` or similar |
| **Streaming output** | Real-time feedback during LLM calls | Medium | `stream_mode="updates"` for progress visibility |
| **Approval/Reject pattern** | Full HITL pattern: not just input, but decision | Medium | Return "approve"/"reject" from interrupt, route accordingly |
| **State update commentary** | Inline comments explaining each state change | Low | Educational comments in node functions |
| **Multiple interrupt points** | Shows HITL can happen at various workflow stages | Medium | Topic selection + Approach selection (as planned) |
| **Validation of interrupt input** | Shows robust HITL patterns | Medium | Loop until valid input received |
| **LangSmith tracing setup** | Observability for learning/debugging | Low | Environment variable configuration |
| **Modular node functions** | Functions can be understood independently | Low | Each node self-contained, minimal coupling |

## Anti-Features

Features to explicitly NOT build. These add complexity that obscures the learning objectives or are production concerns that distract from pedagogical goals.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **PostgresSaver or production checkpointer** | Adds infrastructure complexity; requires database setup | Use `MemorySaver` with comment noting production alternative |
| **Comprehensive error handling/retries** | Obscures the happy path; production concern | Minimal try/except; let errors surface for learning |
| **Multiple LLM providers** | Configuration complexity; not relevant to LangGraph patterns | Pick one provider (OpenAI or Anthropic); hardcode or simple env var |
| **Web UI or REST API** | Significant additional complexity; separate concern | CLI interaction only; focus on graph patterns |
| **Tool use / function calling** | Adds complexity beyond core patterns; not in requirements | Keep agents as simple LLM + prompt; no external tool bindings |
| **Subgraphs or nested graphs** | Advanced pattern that complicates understanding | Flat graph with all nodes visible; add subgraph comments for "next steps" |
| **Parallel execution** | Adds complexity; not needed for sequential workflow | Sequential node execution; note parallelism as advanced topic |
| **Long-term memory store** | Production feature beyond scope | Short-term state in graph only; note long-term memory as extension |
| **Rate limiting / cost monitoring** | Production operations concern | Note as production consideration in comments |
| **LangGraph Platform deployment** | Infrastructure complexity | Local execution only; note platform for "production" |
| **Dynamic tool selection** | Over-engineering for this use case | Fixed agent behaviors; handoff is via state, not tools |
| **Time-travel debugging** | Studio feature; external dependency | Print-based debugging; note Studio for advanced use |
| **Custom streaming modes** | Complexity beyond basic patterns | Use default streaming or simple `stream_mode="updates"` |
| **Async patterns throughout** | Complicates code for marginal benefit in tutorial | Sync code for clarity; note async exists for production |
| **Environment-based config injection** | Production pattern that obscures the example | Hardcode or simple `.env` for API keys only |

## Feature Dependencies

Understanding what must come before what, both in implementation and learning.

```
Core Foundation (must be first):
  StateGraph + TypedDict schema
        |
        v
  Nodes + Edges + Compile
        |
        v
  Checkpointer (MemorySaver)
        |
        +------------------+
        |                  |
        v                  v
  Human-in-the-Loop    Conditional Edges
  (interrupt/resume)   (routing logic)
        |                  |
        +------------------+
                |
                v
        Agent Handoff Pattern
        (state-driven routing)
                |
                v
        Reflection Loop
        (writer-critic with bounded iterations)
                |
                v
        Full Workflow Integration
```

### Implementation Order Recommendation

1. **Phase 1: Skeleton** - StateGraph, basic nodes, compile/invoke
2. **Phase 2: Checkpointing** - Add MemorySaver, thread_id
3. **Phase 3: HITL** - interrupt() + Command(resume=), first interrupt point
4. **Phase 4: Agents** - Approach, Writer, Critic nodes with LLM calls
5. **Phase 5: Handoffs** - State-based routing between agents
6. **Phase 6: Reflection** - Writer-critic loop with iteration limit
7. **Phase 7: Polish** - Second HITL point, output formatting, comments

## MVP Recommendation

For an MVP that demonstrates core patterns while remaining learnable:

### Must Include (Phase 1 MVP)

1. **StateGraph with typed state schema** - Foundation
2. **Human-in-the-loop for topic input** - Core requirement, simplest HITL
3. **Single approach agent** - One LLM-powered node
4. **Human-in-the-loop for approach selection** - Second HITL point
5. **Writer agent** - Second LLM-powered node
6. **Critic agent with approval** - Third LLM-powered node
7. **Writer-critic reflection loop** - Max 3 iterations with state counter
8. **Conditional edges** - For loop control and handoffs
9. **Final output save** - Markdown file output

### Defer to Post-MVP

| Feature | Reason to Defer |
|---------|-----------------|
| Streaming output | Nice UX but not essential for pattern demonstration |
| Graph visualization | Can be added as enhancement; not core |
| Validation of HITL input | Robustness feature; simple version first |
| LangSmith integration | Observability is bonus, not core pattern |
| Detailed prompt templates | Start with inline prompts; extract later |

## Pedagogical Design Principles

Based on research into what makes LangGraph tutorials effective:

### 1. Show the Graph Structure Visually

Include a diagram (Mermaid or ASCII) at the top of the code showing the flow:

```
[START] -> [topic_input] -> [approach_agent] -> [approach_selection]
                                                        |
                                                        v
[END] <- [save_article] <- [critic_decision] <- [critic_agent]
                                    |                  ^
                                    |                  |
                                    +-- [writer_agent]-+
                                         (loop if rejected)
```

### 2. One Concept Per Node

Each node should demonstrate exactly one thing:
- `topic_input` - interrupt for HITL
- `approach_agent` - LLM call returning structured output
- `approach_selection` - interrupt for HITL with choices
- `writer_agent` - LLM call with context from state
- `critic_agent` - LLM call with evaluation
- `critic_decision` - conditional routing (loop or continue)
- `save_article` - side effect (file write)

### 3. State Schema Documents the Workflow

The TypedDict should read like a workflow description:

```python
class ArticleState(TypedDict):
    topic: str                    # From first HITL
    approaches: list[str]         # From approach agent
    selected_approach: str        # From second HITL
    draft: str                    # From writer agent
    critique: str                 # From critic agent
    is_approved: bool             # Critic's verdict
    iteration_count: int          # Loop counter
    final_article: str            # Final output
```

### 4. Comments Explain "Why", Not "What"

```python
# Use interrupt() - the modern LangGraph pattern (as of v0.2.31+)
# This pauses execution and persists state until Command(resume=) is called
value = interrupt({"prompt": "Enter topic:"})
```

### 5. Explicit Over Implicit

- Name conditional edge functions clearly: `should_continue_writing()`
- Use string literals for node names that match function names
- Show the full config dictionary, not abbreviated versions

## Sources

### Official Documentation (HIGH confidence)
- [LangGraph Human-in-the-Loop Concepts](https://docs.langchain.com/oss/python/langgraph/interrupts) - interrupt() function, Command object
- [LangGraph Multi-Agent Docs](https://docs.langchain.com/oss/python/langchain/multi-agent) - Handoff patterns
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api) - StateGraph, nodes, edges
- [LangGraph Reflection Tutorial](https://langchain-ai.github.io/langgraph/tutorials/reflection/reflection/) - Generate-reflect loop pattern
- [PyPI LangGraph](https://pypi.org/project/langgraph/) - Current version: 1.0.6 (Jan 2026)

### LangGraph Libraries (HIGH confidence)
- [langgraph-reflection](https://github.com/langchain-ai/langgraph-reflection) - Pre-built reflection architecture
- [langgraph-checkpoint](https://pypi.org/project/langgraph-checkpoint/) - MemorySaver and base checkpointer

### Tutorial/Educational Sources (MEDIUM confidence)
- [LangChain Academy - Intro to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph) - Official course structure
- [Analytics Vidhya LangGraph Tutorial](https://www.analyticsvidhya.com/blog/2025/05/langgraph-tutorial-for-beginners/) - Beginner patterns
- [DataCamp LangGraph Tutorial](https://www.datacamp.com/tutorial/langgraph-agents) - Educational approach

### Best Practices (MEDIUM confidence)
- [LangGraph Best Practices](https://www.swarnendu.de/blog/langgraph-best-practices/) - Production vs tutorial patterns
- [LangGraph Checkpointing Best Practices](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025/) - MemorySaver vs PostgresSaver
- [LangGraph Error Handling](https://sparkco.ai/blog/advanced-error-handling-strategies-in-langgraph-applications/) - What to include/omit

---
*Research completed: 2026-01-18*
*Confidence: HIGH - Based on official LangGraph 1.0.6 documentation and verified patterns*
