# Pedagogical Article Writer

## What This Is

A Python/LangGraph reference implementation that demonstrates multi-agent patterns through a pedagogical article writing workflow. The system takes an AI topic, finds pedagogical approaches, writes an accessible article, and refines it through critique loops. It's primarily a learning resource for LangGraph patterns, not a production tool.

## Core Value

Clean, readable demonstration of LangGraph multi-agent patterns — agent handoffs and reflection loops — that developers can learn from and adapt.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Human-in-the-loop for topic selection (LangGraph interrupt)
- [ ] Approach agent finds 3 pedagogical approaches with metaphors
- [ ] Human-in-the-loop for approach selection (LangGraph interrupt)
- [ ] Writer agent drafts article using selected approach (3Blue1Brown style)
- [ ] Critic agent evaluates accuracy AND comprehensibility
- [ ] Writer-critic reflection loop (max 3 iterations)
- [ ] Final article saved as markdown
- [ ] Agent handoffs via LangGraph state transitions
- [ ] Clear, documented code that serves as a reference

### Out of Scope

- Production-ready error handling — this is a reference, not production code
- Web UI — CLI interaction only
- Multiple LLM provider support — pick one (likely OpenAI or Anthropic)
- Pattern article workflow — focusing on pedagogic workflow only
- Persistence/checkpointing — keep it simple for learning

## Context

This is a port/improvement of an existing TypeScript implementation using a custom orchestration framework. The goal is to replace the custom framework with LangGraph to leverage its built-in primitives for state management, interrupts, and agent coordination.

The TypeScript version has:
- Pattern article orchestrator (simpler)
- Pedagogic article orchestrator (richer, chosen for this port)
- Custom step/loop/human-input abstractions

The Python version should demonstrate LangGraph idioms rather than mirroring the TypeScript structure.

Key agents from TypeScript to port:
- `PedagogicApproachAgent` — searches for 3 pedagogical approaches
- `PedagogicWriterAgent` — writes articles with detailed pedagogy guidelines
- `PedagogicCriticAgent` — evaluates accuracy and comprehensibility

## Constraints

- **Stack**: Python, LangGraph, LangChain — the whole point is demonstrating these
- **Clarity over cleverness**: Code should be readable by someone learning LangGraph
- **Single file or minimal files**: Easy to follow, not over-architected

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LangGraph over custom orchestration | Leverage battle-tested primitives instead of homegrown | — Pending |
| Pedagogic workflow (not pattern) | Richer example with approach selection step | — Pending |
| Reference implementation focus | Optimizing for learning, not production features | — Pending |

---
*Last updated: 2025-01-18 after initialization*
