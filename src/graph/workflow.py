"""Graph construction and compilation for the Pedagogical Article Writer.

This module provides functions to build and compile the LangGraph workflow.
The graph defines the sequence of nodes and edges that form the article
writing pipeline with human-in-the-loop checkpoints and a reflection loop.

================================================================================
Key LangGraph Concepts Demonstrated
================================================================================

**StateGraph**
    The builder class that constructs a graph from a state schema (TypedDict).
    All nodes receive the full state and return partial updates (dict).
    Example: `StateGraph(ArticleState)` creates a builder using ArticleState.

**START / END**
    Special constants for graph entry and exit points.
    Every graph needs at least `add_edge(START, "first_node")`.
    The END constant signals workflow completion.

**Nodes**
    Functions registered with `add_node("name", function)`.
    Each node receives the full state, performs work, returns partial updates.
    NEVER mutate state directly - always return a dict with changed fields.

**Command Routing**
    Nodes can return `Command(goto="node_name", update={...})` for dynamic flow.
    This replaces conditional edges when routing depends on node logic.
    Type annotation `Command[Literal["a", "b"]]` is REQUIRED for validation.
    No explicit edge needed FROM nodes using Command - routing is dynamic.

**interrupt() for Human-in-the-Loop**
    The `interrupt("prompt")` function pauses execution and returns to caller.
    Caller resumes with `Command(resume=value)` to continue the workflow.
    Requires a checkpointer (InMemorySaver) to persist state during pause.

**InMemorySaver**
    Checkpointer that stores graph state in memory for HITL and state recovery.
    Pass to `builder.compile(checkpointer=saver)` to enable state persistence.
    For production: use PostgresSaver for durable storage across restarts.

================================================================================
Workflow Structure
================================================================================

    START -> topic_input -> approach_agent -> approach_selection
                                                      |
                          +---------------------------+
                          |                           |
                     (reject)                    (select)
                          |                           |
                          v                           v
                  approach_agent              writer_agent
                          |                           |
                          +---> approach_selection    v
                                                 critic_agent
                                                      |
                          +---------------------------+
                          |                           |
                     (revise)                   (approve)
                          |                           |
                          v                           v
                   writer_agent               save_output -> END

    Human-in-the-loop pauses:
    - topic_input: User provides article topic via interrupt()
    - approach_selection: User selects approach (1/2/3) or rejects via interrupt()

    Command-based routing:
    - approach_selection: Routes to writer_agent or approach_agent
    - critic_agent: Routes to writer_agent (revise) or save_output (approve)

================================================================================
See Also
================================================================================

- src/graph/state.py: ArticleState TypedDict defining graph state schema
- src/graph/nodes/: Individual node implementations with pattern documentation
- LangGraph docs: https://langchain-ai.github.io/langgraph/
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from src.graph.state import ArticleState
from src.graph.nodes import (
    topic_input_node,
    approach_agent_node,
    approach_selection_node,
    writer_agent_node,
    critic_agent_node,
    save_output_node,
)


def build_graph() -> StateGraph:
    """Construct the article writer graph with reflection loop.

    Creates a StateGraph using ArticleState as the schema, adds all nodes,
    and defines the flow with human-in-the-loop checkpoints.

    Current flow (Phase 6):
    START -> topic_input -> approach_agent -> approach_selection --(Command)--> writer_agent -> critic_agent --(Command)--> save_output -> END
                                                      |                              ^                |
                                                      +--- (reject) -----------------+                 |
                                                                  via approach_agent                   v
                                                                                        (revise) --> writer_agent

    Command-based routing:
    - approach_selection uses Command(goto=...) instead of explicit edges
    - When user selects an approach: Command(goto="writer_agent")
    - When user rejects all: Command(goto="approach_agent") to regenerate
    - No explicit edge needed FROM approach_selection - Command handles routing

    - critic_agent uses Command(goto=...) for reflection loop routing
    - When article approved (scores >= 7) or max iterations: Command(goto="save_output")
    - When revision needed: Command(goto="writer_agent") with feedback
    - No explicit edge needed FROM critic_agent - Command handles routing

    Returns:
        StateGraph builder ready for compilation.
    """
    # Create the graph builder with our state schema
    builder = StateGraph(ArticleState)

    # Add nodes with descriptive names
    # Each node is a function that receives state and returns partial updates
    builder.add_node("topic_input", topic_input_node)
    builder.add_node("approach_agent", approach_agent_node)
    builder.add_node("approach_selection", approach_selection_node)
    builder.add_node("writer_agent", writer_agent_node)
    builder.add_node("critic_agent", critic_agent_node)
    builder.add_node("save_output", save_output_node)

    # Define edges
    # START is a special constant representing the graph entry point
    builder.add_edge(START, "topic_input")
    builder.add_edge("topic_input", "approach_agent")
    # approach_agent flows to approach_selection for user decision
    builder.add_edge("approach_agent", "approach_selection")
    # NOTE: No edge FROM approach_selection - Command handles routing dynamically!
    # approach_selection returns Command(goto="writer_agent") or Command(goto="approach_agent")
    builder.add_edge("writer_agent", "critic_agent")
    # NOTE: No edge FROM critic_agent - Command handles routing dynamically!
    # critic_agent returns Command(goto="writer_agent") for revision
    # critic_agent returns Command(goto="save_output") for approval or max iterations
    # END is a special constant representing the graph exit point
    builder.add_edge("save_output", END)

    return builder


# Export the graph for LangGraph Server
# The server will compile it with its own checkpointer
graph = build_graph()


def create_compiled_graph():
    """Create an executable graph with state persistence.

    Builds the graph and compiles it with an InMemorySaver checkpointer.
    The checkpointer is essential for:
    - Human-in-the-loop workflows (interrupt/resume)
    - State persistence across invocations with same thread_id
    - Time-travel debugging (examining past states)

    Returns:
        Compiled graph ready for invoke() or stream() calls.
    """
    builder = build_graph()

    # InMemorySaver stores state in memory - perfect for development/learning
    # For production, use PostgresSaver for durable persistence
    checkpointer = InMemorySaver()

    # Compile the graph with the checkpointer
    # This creates an executable graph that can be invoked
    graph = builder.compile(checkpointer=checkpointer)

    return graph
