---
created: 2026-01-19T12:45
title: Extract nodes to separate files
area: tooling
files:
  - src/graph/nodes.py
---

## Problem

`src/graph/nodes.py` has grown to 373 lines containing all node implementations:
- `topic_input_node`
- `approach_agent_node` (with tool-calling loop)
- `approach_selection_node`
- `writer_agent_node`
- `critic_agent_node` (placeholder)
- `output_node` (placeholder)

Plus system prompts (`APPROACH_AGENT_SYSTEM_PROMPT`, `WRITER_SYSTEM_PROMPT`).

This will grow further with Phase 6 (critic agent) and makes the file harder to navigate as a learning reference.

## Solution

Split into `src/graph/nodes/` package:
- `__init__.py` - re-exports all nodes
- `topic_input.py`
- `approach_agent.py` (includes its system prompt)
- `approach_selection.py`
- `writer_agent.py` (includes WRITER_SYSTEM_PROMPT)
- `critic_agent.py` (Phase 6)
- `output.py` (Phase 7)

Consider doing this as part of Phase 7 (Output & Polish) since CODE-01 requires "readable code suitable as reference".
