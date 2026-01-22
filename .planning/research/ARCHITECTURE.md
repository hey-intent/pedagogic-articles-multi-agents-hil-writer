# Architecture Patterns

**Domain:** LangGraph Multi-Agent Pedagogical Article Writer
**Researched:** 2026-01-18
**Confidence:** MEDIUM (WebSearch-verified against multiple 2025 sources; Claude training data used as hypothesis)

## Executive Summary

LangGraph (as of late 2025) provides a graph-based orchestration framework where **nodes** represent tasks/agents and **edges** represent control flow. The modern API emphasizes:

1. **`interrupt()` function** for human-in-the-loop (replacing older breakpoint patterns)
2. **`Command` type** for dynamic routing and agent handoffs (replacing rigid conditional edges)
3. **Checkpointers** for state persistence enabling pause/resume
4. **TypedDict state schemas** with reducer functions for robust state management

For this pedagogical article writer, the recommended architecture is a **sequential pipeline with reflection loop**, using the modern `Command`-based handoffs and `interrupt()` for human input.

---

## Recommended Architecture

```
+------------------+     +------------------+     +-------------------+
|  Topic Selection |---->|  Approach Agent  |---->|  Approach Select  |
|   (interrupt)    |     |  (generates 3)   |     |   (interrupt)     |
+------------------+     +------------------+     +-------------------+
                                                          |
                                                          v
+------------------+     +------------------+     +-------------------+
|      Save        |<----|  Critic Agent    |<----|   Writer Agent    |
|   (terminal)     |     |  (evaluates)     |     |   (drafts)        |
+------------------+     +------------------+     +-------------------+
                              |     ^
                              |     |
                              +-----+
                         (reflection loop)
```

### Architecture Type: Sequential Pipeline with Reflection

This architecture combines:
- **Pipeline pattern**: Sequential stages (topic -> approach -> writing)
- **Reflection pattern**: Writer-Critic feedback loop for iterative improvement
- **Human-in-the-loop**: Interrupts at decision points (topic, approach selection)

---

## Core Components

### 1. State Schema (TypedDict)

The graph state is the single source of truth, passed between all nodes.

```typescript
// Conceptual TypeScript representation
interface ArticleState {
  // User inputs (set via interrupt/resume)
  topic: string | null;
  selectedApproachIndex: number | null;

  // Agent outputs
  approaches: Approach[] | null;  // 3 generated approaches
  currentDraft: string | null;

  // Reflection loop state
  criticFeedback: string | null;
  isApproved: boolean;
  revisionCount: number;

  // Message history (for context)
  messages: Message[];
}

interface Approach {
  title: string;
  description: string;
  targetAudience: string;
  outline: string[];
}
```

**Key principle:** State is immutable between nodes. Each node receives state, returns updates. Reducers merge updates into state.

### 2. Nodes (Task Units)

| Node | Responsibility | Input State | Output State Updates |
|------|---------------|-------------|---------------------|
| `topic_input` | Pause for human topic input | (empty) | `topic` |
| `approach_agent` | Generate 3 pedagogical approaches | `topic` | `approaches` |
| `approach_select` | Pause for human selection | `approaches` | `selectedApproachIndex` |
| `writer_agent` | Draft article based on approach | `selectedApproachIndex`, `approaches`, `criticFeedback?` | `currentDraft`, `revisionCount++` |
| `critic_agent` | Evaluate draft, provide feedback | `currentDraft` | `criticFeedback`, `isApproved` |
| `save_output` | Persist final article | `currentDraft` | (terminal) |

### 3. Edges (Control Flow)

**Modern approach:** Use `Command` for dynamic routing instead of predefined conditional edges.

| From | To | Condition |
|------|----|-----------|
| `topic_input` | `approach_agent` | Always (after resume) |
| `approach_agent` | `approach_select` | Always |
| `approach_select` | `writer_agent` | Always (after resume) |
| `writer_agent` | `critic_agent` | Always |
| `critic_agent` | `writer_agent` | `isApproved === false` (loop) |
| `critic_agent` | `save_output` | `isApproved === true` (exit) |

---

## Key Patterns

### Pattern 1: Human-in-the-Loop with `interrupt()`

**What:** Pause execution, wait for external input, resume with provided value.

**When:** Topic input, approach selection - any point requiring human decision.

**Implementation (Python reference, adapt for JS/TS):**
```python
from langgraph.types import interrupt, Command

def topic_input_node(state):
    # Pause and request input
    user_topic = interrupt(
        value="Please provide a topic for the article"
    )
    # Execution resumes here with user's input
    return {"topic": user_topic}
```

**Resume pattern:**
```python
# From external code (CLI, API handler)
graph.invoke(
    Command(resume="Introduction to GraphQL"),
    config={"configurable": {"thread_id": thread_id}}
)
```

**Requirements:**
- **Checkpointer required** - State must persist across pause/resume
- Use `InMemorySaver` for development, `SqliteSaver` or cloud options for production

### Pattern 2: Reflection Loop (Writer-Critic)

**What:** Two agents iterate until quality threshold met.

**When:** Content generation requiring iterative refinement.

**Implementation:**
```python
def critic_agent_node(state):
    draft = state["currentDraft"]
    revision_count = state["revisionCount"]

    # LLM evaluates the draft
    evaluation = critic_llm.invoke(...)

    is_approved = evaluation.approved or revision_count >= MAX_REVISIONS

    # Use Command for dynamic routing
    if is_approved:
        return Command(
            update={"criticFeedback": evaluation.feedback, "isApproved": True},
            goto="save_output"
        )
    else:
        return Command(
            update={"criticFeedback": evaluation.feedback, "isApproved": False},
            goto="writer_agent"
        )
```

**Key considerations:**
- **Max revision cap** - Prevent infinite loops (recommend 3-5 iterations)
- **Feedback accumulation** - Pass critic feedback to writer for context
- **Clear approval criteria** - Define what "good enough" means

### Pattern 3: Agent Handoffs via Command

**What:** Nodes directly specify next node and state updates.

**When:** Dynamic routing based on runtime conditions (not fixed edges).

**Implementation:**
```python
from langgraph.types import Command

def my_node(state):
    # Do work...
    result = process(state)

    # Return Command to update state AND route
    return Command(
        update={"field": result},
        goto="next_node_name"
    )
```

**Advantages over conditional edges:**
- Node encapsulates its own routing logic
- No need to define edges upfront for dynamic flows
- Cleaner for multi-agent handoffs

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Global Mutable State

**What:** Modifying state outside the graph's state management.

**Why bad:** Breaks checkpointing, causes race conditions, loses auditability.

**Instead:** All state changes flow through node return values and reducers.

### Anti-Pattern 2: Unbounded Reflection Loops

**What:** Writer-Critic loop without exit condition.

**Why bad:** Infinite loops, runaway costs, no convergence.

**Instead:** Always cap iterations. `revisionCount >= MAX_REVISIONS` forces exit.

### Anti-Pattern 3: Mixing interrupt() with Complex Conditional Edges

**What:** Using old-style `interrupt_before`/`interrupt_after` with modern `Command` routing.

**Why bad:** Confusing control flow, harder to debug.

**Instead:** Use `interrupt()` function consistently. Use `Command` for all dynamic routing.

### Anti-Pattern 4: Fat Nodes

**What:** Single node doing multiple conceptually separate tasks.

**Why bad:** Hard to test, hard to resume from middle, poor observability.

**Instead:** One node = one clear responsibility. Compose via graph.

---

## Data Flow

```
1. INITIALIZATION
   State: { topic: null, approaches: null, ... }

2. TOPIC INPUT (interrupt)
   - Graph pauses
   - External: user provides topic
   - Resume with Command(resume="GraphQL Basics")
   State: { topic: "GraphQL Basics", ... }

3. APPROACH AGENT
   - LLM generates 3 approaches
   State: { topic: "GraphQL Basics", approaches: [A, B, C], ... }

4. APPROACH SELECT (interrupt)
   - Graph pauses, presents 3 options
   - External: user selects index
   - Resume with Command(resume=1)
   State: { ..., selectedApproachIndex: 1, ... }

5. WRITER AGENT
   - LLM drafts article using approaches[1]
   State: { ..., currentDraft: "...", revisionCount: 1, ... }

6. CRITIC AGENT
   - LLM evaluates draft
   - If not approved: Command(goto="writer_agent")
   - If approved: Command(goto="save_output")
   State: { ..., criticFeedback: "...", isApproved: true/false, ... }

7. LOOP (if not approved)
   - Back to WRITER with feedback
   - Increment revisionCount

8. SAVE OUTPUT (terminal)
   - Persist final article
   - Graph complete
```

---

## Component Boundaries

| Component | Owns | Does NOT Own |
|-----------|------|--------------|
| **State Schema** | Data structure, types, defaults | Business logic |
| **Nodes** | Single task execution, state updates | Routing decisions (use Command) |
| **Edges** | Fixed routing (if any) | Dynamic routing (use Command) |
| **Checkpointer** | Persistence, resume capability | State shape |
| **LLM Calls** | Content generation | State management |

### Separation of Concerns

```
+-----------------+
|   Graph Config  |  <- Checkpointer, thread config
+-----------------+
        |
+-----------------+
|   StateGraph    |  <- Node registration, edge definitions
+-----------------+
        |
+-----------------+
|     Nodes       |  <- Business logic, LLM calls
+-----------------+
        |
+-----------------+
|   State Schema  |  <- TypedDict, reducers
+-----------------+
```

---

## Suggested Build Order

Based on dependencies and learning progression:

### Phase 1: Foundation
**Build first - everything else depends on this**

1. **State schema definition** - Define TypedDict with all fields
2. **Checkpointer setup** - InMemorySaver for development
3. **Basic graph skeleton** - Empty nodes, simple edges
4. **Single interrupt test** - Verify pause/resume works

**Milestone:** Can pause at a node, resume with input, see state update.

### Phase 2: Happy Path
**Linear flow without loops**

1. **Topic input node** - interrupt() for topic
2. **Approach agent node** - LLM generates 3 approaches
3. **Approach select node** - interrupt() for selection
4. **Writer agent node** - LLM drafts article
5. **Save output node** - Simple file write

**Milestone:** Can run topic -> approaches -> select -> draft -> save (no critic).

### Phase 3: Reflection Loop
**Add iterative improvement**

1. **Critic agent node** - LLM evaluates draft
2. **Command-based routing** - Approved vs loop back
3. **Revision counter** - Track iterations, cap maximum
4. **Feedback passing** - Critic feedback informs next draft

**Milestone:** Writer-Critic loops until approved or max revisions.

### Phase 4: Polish
**Production readiness (if needed)**

1. **Error handling** - Graceful failures, retry logic
2. **Observability** - Logging, state inspection
3. **Configuration** - Max revisions, LLM params as config

---

## Technology Decisions

### LangGraph Version

**Use:** Latest stable (post-0.2.31 for `interrupt()` function support)

**Rationale:** The `interrupt()` function (introduced 0.2.31) is the recommended approach for human-in-the-loop. Older patterns (`interrupt_before`, `NodeInterrupt` exception) are deprecated.

### Language

**Decision needed:** Python vs TypeScript/JavaScript

| Factor | Python | TypeScript |
|--------|--------|------------|
| LangGraph maturity | Primary, most examples | Supported, fewer examples |
| Documentation | Comprehensive | Good but less |
| Ecosystem | LangChain native | langgraph.js |

**Recommendation:** Python for learning (more examples/docs), TypeScript if team preference.

### Checkpointer

**Development:** `InMemorySaver` - Zero setup, sufficient for learning

**Production:** `SqliteSaver` or cloud options - Persistence across restarts

---

## Sources

Research based on:
- [LangGraph Multi-Agent Orchestration Guide 2025](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-multi-agent-orchestration-complete-framework-guide-architecture-analysis-2025) - Architecture patterns overview
- [LangGraph: Multi-Agent Workflows (LangChain Blog)](https://www.blog.langchain.com/langgraph-multi-agent-workflows/) - Official multi-agent guidance
- [Human-in-the-loop Concepts (LangGraph Docs)](https://langchain-ai.github.io/langgraphjs/concepts/human_in_the_loop/) - interrupt() function documentation
- [Command: A new tool for multi-agent architectures (LangChain Blog)](https://blog.langchain.com/command-a-new-tool-for-multi-agent-architectures-in-langgraph/) - Command type introduction
- [How Agent Handoffs Work (Towards Data Science)](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/) - Handoff patterns
- [Mastering LangGraph State Management 2025](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025) - State management patterns
- [Interrupts and Commands in LangGraph (DEV Community)](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl) - Implementation guide

**Confidence notes:**
- `interrupt()` and `Command` patterns: HIGH confidence (multiple official sources agree)
- Specific API signatures: MEDIUM confidence (verify against current docs when implementing)
- TypeScript API parity: MEDIUM confidence (JS/TS docs less comprehensive than Python)
