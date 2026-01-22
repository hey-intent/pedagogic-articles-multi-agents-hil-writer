---
phase: 04-approach-selection-hitl
plan: 01
subsystem: graph-hitl
tags: [langgraph, command-routing, interrupt, hitl, state-management]

# Dependency graph
requires:
  - phase: 03-02
    provides: approach_agent_node generates 3 approaches
provides:
  - approach_selection_node with Command-based routing
  - rejected_approaches tracking in state
  - Modified approach_agent_node with rejection context
affects: [05-writer-agent]

# Tech tracking
tech-stack:
  added: []  # Using existing langgraph
  patterns: [command-routing, interrupt-resume, rejection-tracking]

key-files:
  created: []
  modified:
    - src/graph/state.py
    - src/graph/nodes.py
    - src/graph/workflow.py

key-decisions:
  - "Command[Literal[...]] for type-safe routing instead of conditional edges"
  - "Invalid input treated as rejection for simplicity"
  - "Rejected approaches accumulated in list (not mutated) for retry context"

patterns-established:
  - "Command routing: Command(update={...}, goto='node_name') for atomic state update + routing"
  - "Rejection tracking: state field accumulates rejected items, passed to agent to avoid repetition"
  - "Type annotation on Command: Command[Literal['a', 'b']] required for graph validation"

# Metrics
duration: 6min
completed: 2026-01-19
---

# Phase 4 Plan 1: Approach Selection HITL Implementation Summary

**Command-based approach selection node with interrupt, routing to writer (selection) or approach_agent (rejection) with rejected approaches tracking**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-19T15:00:00Z
- **Completed:** 2026-01-19T15:06:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added rejected_approaches field to ArticleState for tracking user rejections
- Created approach_selection_node with interrupt() for user input and Command routing
- Modified approach_agent_node to include rejected approaches in prompt
- Updated workflow graph with new node and Command-based routing
- All existing unit tests pass (4 passed, 7 skipped, 4 deselected)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add rejected_approaches field and create approach_selection_node** - `a6ef003` (feat)
2. **Task 2: Update workflow graph with approach_selection node** - `07c8244` (feat)
3. **Task 3: Verify core functionality** - No commit (verification only)

## Files Created/Modified
- `src/graph/state.py` - Added rejected_approaches field to ArticleState
- `src/graph/nodes.py` - New approach_selection_node, modified approach_agent_node
- `src/graph/workflow.py` - Added approach_selection node, updated edges

## Technical Details

### Command Routing Pattern

The approach_selection_node uses LangGraph's Command object for combined state update and routing:

```python
# Selection routes to writer
return Command(update={"selected_approach_index": index}, goto="writer_agent")

# Rejection routes back to approach_agent
return Command(update={"rejected_approaches": rejected}, goto="approach_agent")
```

### Graph Flow

```
START -> topic_input -> approach_agent -> approach_selection --(Command)--> writer_agent -> save_output -> END
                                                  |
                                                  +--- (reject via Command) ---> approach_agent (loop)
```

### Rejection Tracking

When user rejects all approaches:
1. Current approaches added to rejected_approaches list
2. approach_agent_node reads rejected list and adds to system prompt
3. New prompt instructs LLM to generate completely different approaches

## Decisions Made
- **Command vs conditional edges:** Command keeps routing logic in node, cleaner than separate edge functions
- **Invalid input handling:** Treat as rejection (simple approach) rather than strict validation loop
- **List accumulation:** Use `rejected + approaches` (new list) instead of mutation

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verifications passed:
- Graph compiles without errors
- State has rejected_approaches field
- approach_selection_node exists with proper type annotation
- Workflow imports new node
- Graph has all 5 expected nodes
- Unit tests pass

## Next Phase Readiness
- Approach selection HITL working with Command-based routing
- Ready for Phase 5: Writer agent implementation
- Integration tests can be added in Plan 02 to verify full selection/rejection flows with LLM

---
*Phase: 04-approach-selection-hitl*
*Completed: 2026-01-19*
