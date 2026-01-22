"""Node functions for the Pedagogical Article Writer graph.

This package contains the node implementations for the LangGraph workflow.
Each module contains a single node function for clarity and maintainability.

Nodes follow a critical contract:
- Receive full ArticleState as input
- Return ONLY the fields they want to update as a plain dict
- NEVER mutate the state parameter directly
- LangGraph handles merging the returned dict into the existing state
"""

from src.graph.nodes.topic_input import topic_input_node
from src.graph.nodes.approach_agent import approach_agent_node, APPROACH_AGENT_SYSTEM_PROMPT
from src.graph.nodes.approach_selection import approach_selection_node
from src.graph.nodes.writer_agent import writer_agent_node, WRITER_SYSTEM_PROMPT
from src.graph.nodes.critic_agent import critic_agent_node, CRITIC_SYSTEM_PROMPT, MAX_ITERATIONS
from src.graph.nodes.save_output import save_output_node

__all__ = [
    "topic_input_node",
    "approach_agent_node",
    "APPROACH_AGENT_SYSTEM_PROMPT",
    "approach_selection_node",
    "writer_agent_node",
    "WRITER_SYSTEM_PROMPT",
    "critic_agent_node",
    "CRITIC_SYSTEM_PROMPT",
    "MAX_ITERATIONS",
    "save_output_node",
]
