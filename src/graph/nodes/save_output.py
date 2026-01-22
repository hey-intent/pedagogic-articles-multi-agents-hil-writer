"""Save output node - writes final article to file."""

from datetime import datetime
from pathlib import Path

from src.graph.state import ArticleState


def save_output_node(state: ArticleState) -> dict:
    """Save the final approved article to a markdown file.

    This node writes the final article to the output/ directory with a
    timestamped filename to prevent overwrites. The filename includes
    the topic (sanitized) and a timestamp down to the minute.

    Args:
        state: Current graph state containing the final draft and topic.

    Returns:
        Dict with 'is_approved' set to True and 'output_path' containing
        the path where the article was saved.
    """
    current_draft = state["current_draft"]
    topic = state["topic"]

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Sanitize topic for filename: keep only alphanumeric, dash, underscore
    # Limit to 30 chars to avoid overly long filenames
    safe_topic = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in topic[:30]
    ).strip("_")

    # Generate timestamped filename to prevent overwrites
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"article_{safe_topic}_{timestamp}.md"
    output_path = output_dir / filename

    # Write the article content with UTF-8 encoding
    output_path.write_text(current_draft, encoding="utf-8")

    return {"is_approved": True, "output_path": str(output_path)}
