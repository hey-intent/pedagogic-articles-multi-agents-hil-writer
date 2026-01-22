# LangGraph Multi-Agent Pitfalls

**Domain:** LangGraph multi-agent systems (human-in-the-loop, agent handoffs, reflection loops)
**Researched:** 2026-01-18
**LangGraph Version Target:** 0.2.64+ (latest stable as of research date)

---

## Critical Pitfalls

Mistakes that cause rewrites, broken workflows, or fundamental architecture problems.

### Pitfall 1: Wrapping `interrupt()` in Try/Except

**What goes wrong:** The `interrupt()` function works by throwing a special exception. Wrapping it in a generic try/except catches this exception and prevents the graph from pausing properly.

**Why it happens:** Developers apply defensive error handling patterns without understanding LangGraph's interrupt mechanism.

**Consequences:**
- Human-in-the-loop workflow silently fails
- Graph continues execution without waiting for human input
- State corruption when workflow should have paused

**Warning signs:**
- Interrupt points seem to be "skipped"
- Human approval workflows complete instantly without prompting
- No `__interrupt__` field in graph output

**Prevention:**
```python
# BAD - catches the interrupt exception
try:
    response = interrupt("Approve this action?")
except Exception:
    print("Caught")  # This catches interrupts!

# GOOD - separate interrupt from error-prone code
response = interrupt("Approve this action?")
try:
    risky_operation(response)
except SpecificError as e:
    handle_error(e)
```

**Phase mapping:** Address in Phase 1 (scaffold) by establishing interrupt patterns from the start.

**Confidence:** HIGH (verified via official LangGraph documentation)

**Source:** [LangGraph Interrupts Documentation](https://docs.langchain.com/oss/python/langgraph/interrupts)

---

### Pitfall 2: Reordering or Conditionally Skipping Interrupt Calls

**What goes wrong:** When a node resumes, LangGraph matches resume values to interrupts by **index position**. If the order of interrupt calls changes between executions, resume values get mismatched.

**Why it happens:** Developers add conditional logic that changes which interrupts execute, or refactor node code between runs.

**Consequences:**
- Wrong data passed to wrong interrupt
- Unpredictable workflow behavior
- Silent data corruption

**Warning signs:**
- "Name" field contains age value
- Workflow behaves differently after code changes
- Resume values appear in wrong places

**Prevention:**
```python
# BAD - conditional skipping breaks index matching
name = interrupt("Name?")
if state.get("needs_age"):
    age = interrupt("Age?")  # Sometimes skipped!
city = interrupt("City?")

# GOOD - consistent order every execution
name = interrupt("Name?")
age = interrupt("Age?")  # Always called, even if not needed
city = interrupt("City?")
# Filter out unneeded values after collection
```

**Alternative approach:** Use separate nodes for conditional interrupts rather than multiple interrupts in one node.

**Phase mapping:** Address in human-in-the-loop implementation phase with explicit design rules.

**Confidence:** HIGH (verified via official documentation)

**Source:** [LangGraph Interrupts Documentation](https://docs.langchain.com/oss/python/langgraph/interrupts)

---

### Pitfall 3: Non-Idempotent Operations Before Interrupt

**What goes wrong:** When a graph resumes, the entire node re-executes from the beginning. Any side effects before the interrupt run again.

**Why it happens:** Developers don't realize that resume means "restart node, skip interrupts that have resume values."

**Consequences:**
- Duplicate database records
- Duplicate API calls (charges, notifications)
- Audit log pollution

**Warning signs:**
- Multiple audit entries for single action
- Duplicate emails or notifications
- Database constraint violations on resume

**Prevention:**
```python
# BAD - creates duplicate on every resume
audit_id = db.create_audit_log(action="started")
approved = interrupt("Approve?")
db.update_audit_log(audit_id, approved=approved)

# GOOD - idempotent with upsert pattern
audit_id = db.upsert_audit_log(
    thread_id=config["thread_id"],
    action="started"
)
approved = interrupt("Approve?")
db.update_audit_log(audit_id, approved=approved)

# BETTER - side effects AFTER interrupt
approved = interrupt("Approve?")
audit_id = db.create_audit_log(action="started", approved=approved)
```

**Phase mapping:** Address in human-in-the-loop phase; establish patterns before implementing interrupt nodes.

**Confidence:** HIGH (verified via official documentation)

**Source:** [LangGraph Interrupts Documentation](https://docs.langchain.com/oss/python/langgraph/interrupts)

---

### Pitfall 4: Missing Termination Condition in Reflection Loops

**What goes wrong:** Writer-critic loops run indefinitely because there's no exit condition, hitting `GraphRecursionError`.

**Why it happens:** Developers implement the loop but forget to define when the critic "approves" and stops the cycle.

**Consequences:**
- `GraphRecursionError` crashes workflow
- Runaway token costs
- User-facing timeout errors

**Warning signs:**
- Graph consistently hits recursion limit
- Critic always finds something to criticize
- Loops run exactly to the limit (25 by default)

**Prevention:**
```python
# Define clear termination protocol
class CritiqueResult(TypedDict):
    approved: bool
    feedback: Optional[str]

def critic_node(state: State) -> Command:
    result = llm.invoke(critic_prompt)

    if result.approved:
        # CRITICAL: Return empty messages to signal approval
        return Command(goto=END)
    else:
        # Return feedback for another iteration
        return Command(
            goto="writer",
            update={"feedback": result.feedback}
        )

# Also set explicit iteration limit
MAX_ITERATIONS = 3

def writer_node(state: State) -> dict:
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        # Force exit even if not approved
        return {"final_output": state["draft"], "forced_exit": True}
    # ... normal writing logic
```

**Phase mapping:** Address in reflection loop phase with explicit loop control design.

**Confidence:** HIGH (multiple sources confirm pattern)

**Sources:**
- [LangGraph Reflection Repository](https://github.com/langchain-ai/langgraph-reflection)
- [GraphRecursionError Documentation](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)

---

### Pitfall 5: Using MemorySaver in Production

**What goes wrong:** `MemorySaver` (in-memory checkpointer) loses all state on process restart. Human-in-the-loop workflows cannot resume.

**Why it happens:** `MemorySaver` is easy to set up and works in development. Developers forget to switch for production.

**Consequences:**
- All conversation state lost on restart
- Human approval workflows cannot resume after deployment
- Data loss during scaling events

**Warning signs:**
- Workflows work locally but fail in production
- "Thread not found" errors after deployment
- Users must restart workflows after any service restart

**Prevention:**
```python
# DEVELOPMENT ONLY
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()  # Fine for testing

# PRODUCTION - use PostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(
    conn_string=os.environ["POSTGRES_URI"]
)
```

**For pedagogical project:** MemorySaver is acceptable since it's a learning resource, but document the production alternative.

**Phase mapping:** Address in scaffold phase; choose checkpointer strategy upfront.

**Confidence:** HIGH (official documentation recommends PostgresSaver for production)

**Source:** [LangGraph Checkpointing Best Practices](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)

---

### Pitfall 6: Mutating State Objects Instead of Returning New State

**What goes wrong:** LangGraph uses reducers to merge state updates. Mutating the input state object causes confusing merge behavior.

**Why it happens:** Python dictionaries are mutable; it's natural to modify in place.

**Consequences:**
- Unpredictable reducer behavior
- State updates not properly tracked
- Debugging nightmares with parallel execution

**Warning signs:**
- State contains unexpected values
- Parallel branches produce wrong results
- "Time travel" debugging shows inconsistent states

**Prevention:**
```python
# BAD - mutating input state
def my_node(state: State) -> State:
    state["messages"].append(new_message)  # Mutation!
    return state

# GOOD - return new state object
def my_node(state: State) -> dict:
    return {
        "messages": [new_message]  # Reducer handles merge
    }
```

**Phase mapping:** Establish as coding convention in Phase 1 (scaffold).

**Confidence:** HIGH (verified best practice from multiple sources)

**Source:** [LangGraph Best Practices](https://www.swarnendu.de/blog/langgraph-best-practices/)

---

## Moderate Pitfalls

Mistakes that cause delays, debugging pain, or technical debt.

### Pitfall 7: Overusing Conditional Edges for Complex Routing

**What goes wrong:** Complex multi-agent handoffs become a tangled web of conditional edges that's hard to understand and modify.

**Why it happens:** Conditional edges are the "classic" approach and work for simple flows. Developers keep adding them as complexity grows.

**Consequences:**
- Graph becomes hard to visualize
- Routing logic scattered across multiple functions
- Difficult to add new agents

**Warning signs:**
- 10+ conditional edge definitions
- Routing functions with many if/elif branches
- Difficulty explaining the flow to others

**Prevention:** Use `Command` for dynamic routing in multi-agent systems:

```python
# Instead of many conditional edges:
# graph.add_conditional_edges("router", route_fn, {...})

# Use Command inside nodes:
def agent_node(state: State) -> Command:
    # Agent determines next step
    if needs_handoff:
        return Command(
            goto="specialist_agent",
            update={"context": handoff_context}
        )
    else:
        return Command(goto=END)
```

**Phase mapping:** Decide routing strategy in scaffold phase; use Command for handoffs.

**Confidence:** MEDIUM (recommended in recent documentation, but conditional edges still valid for simple cases)

**Source:** [How Agent Handoffs Work](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/)

---

### Pitfall 8: Missing Reducers for List Fields

**What goes wrong:** Multiple nodes return list fragments, but without a reducer, later updates overwrite earlier ones.

**Why it happens:** Default behavior is "last write wins." Developers expect automatic merging.

**Consequences:**
- Lost messages in conversation history
- Missing data from parallel execution branches
- Intermittent data loss (depends on execution order)

**Warning signs:**
- Messages randomly disappearing
- Parallel tasks only produce partial results
- Data loss varies between runs

**Prevention:**
```python
from typing import Annotated
from langgraph.graph import add_messages

class State(TypedDict):
    # BAD - no reducer, last write wins
    messages: list[BaseMessage]

    # GOOD - explicit reducer for merging
    messages: Annotated[list[BaseMessage], add_messages]
```

**Phase mapping:** Define state schema with reducers in Phase 1 (scaffold).

**Confidence:** HIGH (fundamental LangGraph pattern)

**Source:** [LangGraph State Management Guide](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025)

---

### Pitfall 9: Side Effects in Routing Functions

**What goes wrong:** Routing functions with side effects (logging, incrementing counters, API calls) produce unpredictable behavior because routing functions may be evaluated multiple times.

**Why it happens:** It seems convenient to put logging or metrics in routing functions.

**Consequences:**
- Duplicate log entries
- Incorrect metrics
- Inconsistent routing decisions

**Warning signs:**
- Log shows route evaluated multiple times
- Metrics don't match actual node executions
- Route changes between evaluations

**Prevention:**
```python
# BAD - side effect in routing
def route_fn(state: State) -> str:
    log.info(f"Routing with {state['topic']}")  # Side effect!
    counter.increment()  # Side effect!
    return "next_node"

# GOOD - pure routing function
def route_fn(state: State) -> str:
    # Deterministic, no side effects
    if state.get("approved"):
        return "approved_path"
    return "review_path"
```

**Phase mapping:** Establish as coding convention in scaffold phase.

**Confidence:** HIGH (documented requirement)

**Source:** [LangGraph Patterns and Conventions](https://www.prasanna.dev/posts/langgraph-patterns-and-conventions)

---

### Pitfall 10: Vague Critic Prompts in Reflection Loops

**What goes wrong:** The critic agent either approves everything (too lenient) or never approves (too strict), making the reflection loop ineffective.

**Why it happens:** Prompts are too generic: "Is this good?" or "Find any problems."

**Consequences:**
- Reflection loop adds latency without improving quality
- Loop hits iteration limit without meaningful improvement
- Trivial or repetitive critiques

**Warning signs:**
- Critic always says "looks good" after one iteration
- Critic finds the same issue every iteration
- Output quality doesn't improve with more iterations

**Prevention:**
```python
# BAD - vague prompt
critic_prompt = "Review this content and provide feedback."

# GOOD - specific criteria
critic_prompt = """Review this pedagogical article against these criteria:

1. ACCURACY: Are all technical claims correct?
2. CLARITY: Would a beginner understand this?
3. COMPLETENESS: Are there gaps in the explanation?
4. EXAMPLES: Are examples relevant and correct?

If ALL criteria are satisfied, respond with {"approved": true}.
If ANY criterion fails, respond with:
{
  "approved": false,
  "criterion": "<which failed>",
  "issue": "<specific problem>",
  "suggestion": "<concrete improvement>"
}
"""
```

**Phase mapping:** Address in reflection loop phase with explicit prompt design.

**Confidence:** MEDIUM (best practice from reflection pattern guides)

**Source:** [Reflection Agents Guide](https://www.cloudtechtwitter.com/2025/11/reflection-agents-in-langchain-and-langgraph-ultimate-guide.html)

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable without major refactoring.

### Pitfall 11: Not Setting recursion_limit Appropriately

**What goes wrong:** Default recursion limit (25) may be too low for complex workflows or too high for simple ones (wasting resources on runaway loops).

**Why it happens:** Developers use defaults without considering their specific workflow depth.

**Consequences:**
- `GraphRecursionError` for legitimate deep workflows
- Delayed detection of infinite loops

**Prevention:**
```python
# Calculate expected max depth + buffer
# For writer-critic with 3 iterations:
# topic -> approach -> writer -> critic -> writer -> critic -> ... -> save
# Roughly 3-4 nodes per iteration * 3 iterations + setup = ~15-20

config = {"recursion_limit": 50}  # Set explicit limit
result = graph.invoke(input, config)
```

**Phase mapping:** Set in scaffold phase based on expected workflow depth.

**Confidence:** HIGH

---

### Pitfall 12: Forgetting Checkpointer for Human-in-the-Loop

**What goes wrong:** `interrupt()` is called but no checkpointer is configured. The state isn't saved, and the workflow can't resume.

**Why it happens:** Developers test interrupt logic without the persistence layer.

**Consequences:**
- Graph pauses but can't resume
- State lost between interrupt and resume
- Confusing errors about missing thread state

**Warning signs:**
- Resume fails with "thread not found"
- State is empty after resume
- Works in streaming mode but not invoke

**Prevention:**
```python
# Always include checkpointer when using interrupts
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# And always include thread_id in config
config = {"configurable": {"thread_id": "unique-id"}}
```

**Phase mapping:** Include in scaffold phase; checkpointer setup is prerequisite for interrupt work.

**Confidence:** HIGH (documented requirement)

---

### Pitfall 13: Using Pydantic for Internal State Validation

**What goes wrong:** Pydantic validation adds runtime overhead and has quirks with LangGraph:
- Validation only on first node input
- No useful traceback on validation errors
- Slow recursive validation

**Why it happens:** Pydantic is popular for validation, so developers reach for it.

**Consequences:**
- Hidden validation errors (poor tracebacks)
- Performance overhead
- False sense of security (only validates first node)

**Prevention:**
```python
# For internal state: use TypedDict (lightweight)
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    draft: str
    iteration: int

# For external boundaries (API input/output): use Pydantic
class APIInput(BaseModel):
    topic: str
    style: Literal["technical", "beginner"]
```

**Phase mapping:** Establish state schema conventions in scaffold phase.

**Confidence:** MEDIUM (tradeoffs exist; TypedDict recommended for internal state)

**Source:** [Type Safety in LangGraph](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Scaffold/Setup | Missing checkpointer | Configure checkpointer before any interrupt work |
| Scaffold/Setup | No recursion limit planning | Calculate expected depth, set explicit limit |
| State Design | Mutating state, missing reducers | Establish immutable patterns, annotate collections |
| Human-in-the-Loop | Wrapping interrupt in try/except | Separate interrupt from error handling |
| Human-in-the-Loop | Non-idempotent pre-interrupt ops | Move side effects after interrupt or use idempotent patterns |
| Agent Handoffs | Tangled conditional edges | Use Command for dynamic routing |
| Reflection Loops | Missing termination condition | Define explicit approval criteria + max iterations |
| Reflection Loops | Vague critic prompts | Specific criteria with structured output |

---

## Checklist for Project Implementation

Before starting each phase:

**Scaffold Phase:**
- [ ] Checkpointer configured (MemorySaver for learning, note production alternative)
- [ ] State schema defined with appropriate reducers
- [ ] Recursion limit calculated and set
- [ ] Coding conventions established (no mutation, pure routing functions)

**Human-in-the-Loop Phase:**
- [ ] Interrupt patterns reviewed (no try/except wrapping)
- [ ] Resume behavior understood (node restarts from beginning)
- [ ] Side effects are idempotent or placed after interrupt
- [ ] Thread ID management planned

**Agent Handoffs Phase:**
- [ ] Routing strategy chosen (Command vs conditional edges)
- [ ] State transformation defined if subgraphs have different schemas
- [ ] Handoff context clearly defined

**Reflection Loop Phase:**
- [ ] Termination condition explicitly defined
- [ ] Maximum iterations set (recommend 3)
- [ ] Critic prompts have specific criteria
- [ ] Graceful degradation for forced exit

---

## Sources Summary

**Official Documentation (HIGH confidence):**
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [LangGraph Errors Reference](https://reference.langchain.com/python/langgraph/errors/)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

**LangGraph Repositories (HIGH confidence):**
- [langgraph-reflection](https://github.com/langchain-ai/langgraph-reflection)

**Community Guides (MEDIUM confidence):**
- [LangGraph Best Practices](https://www.swarnendu.de/blog/langgraph-best-practices/)
- [LangGraph State Management 2025](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025)
- [LangGraph Checkpointing 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)
- [Type Safety in LangGraph](https://shazaali.substack.com/p/type-safety-in-langgraph-when-to)
- [Reflection Agents Guide](https://www.cloudtechtwitter.com/2025/11/reflection-agents-in-langchain-and-langgraph-ultimate-guide.html)
- [Agent Handoffs in Multi-Agent Systems](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/)
