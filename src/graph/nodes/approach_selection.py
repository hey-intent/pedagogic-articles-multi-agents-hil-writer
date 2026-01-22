"""Approach selection node - user selects or rejects generated approaches."""

from typing import Literal

from langgraph.types import interrupt, Command

from src.graph.state import ArticleState


def approach_selection_node(state: ArticleState) -> Command[Literal["writer_agent", "approach_agent"]]:
    """Pause for user to select an approach or reject all to regenerate.

    LangGraph Pattern: Command for Dynamic Routing
    ==============================================
    Command(goto="node_name") lets a node control where the graph goes next.
    - User selects approach (1, 2, or 3) -> go to writer_agent
    - User types "reject" -> go back to approach_agent

    Args:
        state: Current graph state containing generated approaches.

    Returns:
        Command routing to writer_agent (if selected) or approach_agent (if rejected).
    """
    approaches = state["approaches"]

    # Build selection prompt showing the 3 approaches
    prompt = "Select an approach (1, 2, or 3) or type 'reject' to regenerate:\n\n"
    for i, approach in enumerate(approaches, 1):
        prompt += f"{i}. {approach['title']}\n"
        prompt += f"   Metaphor: {approach['metaphor']}\n\n"

    # Pause and wait for user input
    user_input = interrupt(prompt)

    # Handle rejection - routes back to approach_agent
    if str(user_input).lower() == "reject":
        rejected = state.get("rejected_approaches") or []
        rejected = rejected + approaches
        return Command(
            update={"rejected_approaches": rejected},
            goto="approach_agent"
        )

    # Handle selection (expecting "1", "2", or "3")
    try:
        index = int(user_input) - 1
        if 0 <= index < len(approaches):
            return Command(
                update={"selected_approach_index": index},
                goto="writer_agent"
            )
    except (ValueError, TypeError):
        pass

    # Invalid input - treat as rejection
    rejected = state.get("rejected_approaches") or []
    rejected = rejected + approaches
    return Command(
        update={"rejected_approaches": rejected},
        goto="approach_agent"
    )
