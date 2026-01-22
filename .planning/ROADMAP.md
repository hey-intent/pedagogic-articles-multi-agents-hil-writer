# Roadmap: Pedagogical Article Writer

## Overview

This roadmap delivers a LangGraph reference implementation in 7 phases, building from foundational state management through human-in-the-loop patterns to the complete writer-critic reflection loop. Each phase produces a working, testable increment that demonstrates specific LangGraph patterns. The HITL patterns are split across two phases to model the actual workflow: topic input first, then approach selection with loop-back capability after the approach agent generates options.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - State schema, checkpointer, basic graph skeleton
- [x] **Phase 2: Topic Input (HITL)** - User provides topic via interrupt/resume
- [x] **Phase 3: Approach Agent** - LLM generates 3 pedagogical approaches
- [x] **Phase 4: Approach Selection (HITL)** - User picks approach or rejects all (loops back)
- [x] **Phase 5: Writer Agent** - Article drafting agent
- [x] **Phase 6: Reflection Loop** - Critic agent and writer-critic iteration cycle
- [x] **Phase 7: Output & Polish** - File output, visualization, code quality

## Phase Details

### Phase 1: Foundation
**Goal**: Working graph skeleton that can compile and execute with placeholder nodes
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Success Criteria** (what must be TRUE):
  1. Graph compiles without errors and can be invoked
  2. State flows through placeholder nodes with TypedDict schema
  3. Checkpointer is configured and state persists across invocations with same thread ID
  4. Graph has clear START to END flow with named nodes
**Plans:** 1 plan

Plans:
- [x] 01-01-PLAN.md — Create graph skeleton with TypedDict state, placeholder nodes, and checkpointer

### Phase 2: Topic Input (HITL)
**Goal**: User can provide topic via interrupt/resume cycle with thread persistence
**Depends on**: Phase 1
**Requirements**: HITL-01, HITL-03, HITL-04
**Success Criteria** (what must be TRUE):
  1. Graph pauses at topic input node via interrupt()
  2. Command(resume=...) correctly passes user-provided topic into state
  3. Thread ID enables multiple independent conversations
  4. Graph resumes and continues to next node after topic provided
**Plans:** 1 plan

Plans:
- [x] 02-01-PLAN.md — Implement interrupt/resume topic input with tests

### Phase 3: Approach Agent
**Goal**: LLM generates 3 pedagogical approaches with metaphors, using web search for research
**Depends on**: Phase 2
**Requirements**: TOOL-01, TOOL-02, AGNT-01, AGNT-02
**Success Criteria** (what must be TRUE):
  1. Web search tool (Brave API) is implemented and callable by agent
  2. Web page reader tool is implemented and callable by agent
  3. Agent receives topic from state and generates exactly 3 approaches
  4. Each approach includes a pedagogical metaphor or analogy
  5. Agent uses web tools to research existing pedagogical resources
  6. Approaches are stored in state for subsequent selection
**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md — Create web tools (search, reader) and Pydantic schemas for approaches
- [x] 03-02-PLAN.md — Transform approach_agent_node to LLM-powered with tool calling

### Phase 4: Approach Selection (HITL)
**Goal**: User selects one of 3 approaches OR rejects all to regenerate (with context)
**Depends on**: Phase 3
**Requirements**: HITL-02, HITL-03, AGNT-03
**Success Criteria** (what must be TRUE):
  1. Graph pauses at approach selection node via interrupt()
  2. User can select approach by index (1, 2, or 3)
  3. User can reject all approaches triggering loop back to approach agent
  4. Rejected approaches are stored and passed to retry prompt (agent won't repeat them)
  5. Command(resume=...) correctly passes selection or rejection into state
  6. Graph routes to writer agent (selection) or approach agent (rejection)
**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md — Implement approach_selection_node with Command routing and state updates
- [x] 04-02-PLAN.md — Update main.py demo and add comprehensive selection/rejection tests

### Phase 5: Writer Agent
**Goal**: LLM drafts article using selected pedagogical approach
**Depends on**: Phase 4
**Requirements**: AGNT-04
**Success Criteria** (what must be TRUE):
  1. Agent receives topic and selected approach from state
  2. Agent produces markdown article in 3Blue1Brown pedagogical style
  3. Draft is stored in state for critic evaluation
  4. Agent can incorporate critic feedback on subsequent iterations
**Plans:** 1 plan

Plans:
- [x] 05-01-PLAN.md — Transform writer_agent_node to LLM-powered with 3Blue1Brown style

### Phase 6: Reflection Loop
**Goal**: Critic evaluates articles and writer iterates until approval or max iterations
**Depends on**: Phase 5
**Requirements**: AGNT-05, AGNT-06, LOOP-01, LOOP-02, LOOP-03, LOOP-04
**Success Criteria** (what must be TRUE):
  1. Critic agent evaluates article for accuracy AND comprehensibility
  2. Critic routes to writer (revision needed) or output (approved) via Command
  3. Iteration counter increments each cycle and is visible in state
  4. Loop terminates after critic approval or 3 iterations (whichever first)
  5. Agent prompts are clear, documented, and demonstrate good patterns
**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md — Create critic agent node and writer revision support
- [x] 06-02-PLAN.md — Wire reflection loop in graph and add tests

### Phase 7: Output & Polish
**Goal**: Complete working example with file output, visualization, and educational code
**Depends on**: Phase 6
**Requirements**: OUTP-01, OUTP-02, CODE-01, CODE-02, CODE-03
**Success Criteria** (what must be TRUE):
  1. Final article is saved as markdown file to disk
  2. Graph visualization (Mermaid diagram) is generated
  3. Code is readable and suitable as a learning reference
  4. Comments explain LangGraph patterns at key points
  5. Implementation fits in minimal files (easy to navigate)
**Plans:** 2 plans

Plans:
- [x] 07-01-PLAN.md — Implement file output for articles and Mermaid visualization
- [x] 07-02-PLAN.md — Polish code documentation for educational value

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 1/1 | ✓ Complete | 2026-01-18 |
| 2. Topic Input (HITL) | 1/1 | ✓ Complete | 2026-01-19 |
| 3. Approach Agent | 2/2 | ✓ Complete | 2026-01-19 |
| 4. Approach Selection (HITL) | 2/2 | ✓ Complete | 2026-01-19 |
| 5. Writer Agent | 1/1 | ✓ Complete | 2026-01-19 |
| 6. Reflection Loop | 2/2 | ✓ Complete | 2026-01-19 |
| 7. Output & Polish | 2/2 | ✓ Complete | 2026-01-19 |

---
*Roadmap created: 2026-01-18*
*Last updated: 2026-01-19 - Phase 7 complete, milestone complete*
