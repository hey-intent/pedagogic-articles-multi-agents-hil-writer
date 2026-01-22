"""Topic input node - collects article topic via human-in-the-loop."""

from typing import Literal

from langgraph.types import interrupt, Command

from src.graph.state import ArticleState


def topic_input_node(state: ArticleState) -> Command[Literal["approach_agent"]]:
    """Collect article topic from user via human-in-the-loop interrupt.

    LangGraph Pattern: interrupt() for Human-in-the-Loop
    =====================================================
    The interrupt() function pauses execution and waits for user input.
    The graph resumes when invoked with Command(resume=value).

    Args:
        state: Current graph state.

    Returns:
        Command with topic update, routing to approach_agent.
    """
    topic = interrupt("Please provide a topic for the article:")
    return Command(
        update={"topic": topic},
        goto="approach_agent"
    )
