"""Entry point for the Pedagogical Article Writer.

This module demonstrates the full workflow with:
1. Human-in-the-loop topic input (interrupt/resume pattern)
2. LLM-powered approach generation with web research
3. Approach selection with rejection loop (interrupt/resume pattern)
4. Command(goto=...) for routing based on user selection
5. Article generation using selected pedagogical approach (3Blue1Brown style)
6. File output for articles and Mermaid workflow visualization

Key LangGraph concepts demonstrated:
- interrupt(): Pauses graph execution to collect user input
- __interrupt__: Key in result that indicates graph is paused
- Command(resume=value): Provides user input and continues execution
- Command(update={...}, goto='node'): Atomic state update and routing
- thread_id: Enables resumption of the correct interrupted state
- Inline tool-calling loop: Agent uses web_search and read_webpage tools
- Structured output: LLM returns exactly 3 validated approaches
- Simple LLM node: Writer agent produces markdown from context in state
- draw_mermaid(): Exports workflow graph as Mermaid diagram

Required environment variables:
- OPENROUTER_API_KEY: For the LLM via OpenRouter (approach agent and writer agent)
- BRAVE_SEARCH_API_KEY: For web search (optional, agent works without it)
"""

from pathlib import Path

from langgraph.types import Command

from src.config import config as app_config
from src.graph.workflow import create_compiled_graph


def check_environment():
    """Check required environment variables and warn if missing.

    The approach agent requires OPENROUTER_API_KEY to function.
    BRAVE_SEARCH_API_KEY enables web search but is optional.
    """
    if not app_config.openrouter_api_key:
        print("WARNING: OPENROUTER_API_KEY not set.")
        print("The approach agent will fail without this key.")
        print("Get your key from: https://openrouter.ai/")
        print()

    if not app_config.brave_search_api_key:
        print("NOTE: BRAVE_SEARCH_API_KEY not set.")
        print("Web search will return errors, but agent will still work.")
        print("Get your key from: https://brave.com/search/api/")
        print()


def save_workflow_diagram(graph) -> str:
    """Save the workflow graph as a Mermaid diagram.

    Generates a Mermaid diagram of the workflow graph and saves it to
    output/workflow_diagram.mmd. The diagram can be viewed at mermaid.live
    or in VSCode with the Mermaid extension.

    Args:
        graph: The compiled LangGraph workflow.

    Returns:
        Path to the saved diagram file.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Get Mermaid code from the graph
    mermaid_code = graph.get_graph().draw_mermaid()

    # Write to file
    diagram_path = output_dir / "workflow_diagram.mmd"
    diagram_path.write_text(mermaid_code, encoding="utf-8")

    return str(diagram_path)


def main():
    """Demonstrate the full pedagogical article writer workflow.

    This function shows:
    1. Human-in-the-loop topic input (interrupt/resume pattern)
    2. LLM-powered approach generation with web research
    3. Approach selection with rejection loop
    4. Article generation in 3Blue1Brown pedagogical style

    The workflow:
    - User provides a topic via interrupt/resume
    - Approach agent researches the topic with web search
    - Agent generates exactly 3 pedagogical approaches
    - User selects an approach (or rejects to regenerate)
    - Writer agent creates article using selected approach
    - Full markdown article is displayed
    """
    # Check and warn about missing environment variables
    # Config automatically loads from .env via pydantic-settings
    check_environment()

    # Create the compiled graph with InMemorySaver checkpointer
    # The checkpointer is REQUIRED for interrupt/resume to work
    graph = create_compiled_graph()

    # Thread configuration: identifies the conversation/session
    # The thread_id is essential - it tells LangGraph which interrupted
    # state to resume when we call invoke() with Command(resume=...)
    config = {
        "configurable": {
            "thread_id": "article-session-1"
        }
    }

    # Initial state: all fields set to their starting values
    # topic is None because user will provide it via interrupt
    initial_state = {
        "topic": None,           # Will be set via interrupt/resume cycle
        "approaches": None,      # Will be set by approach_agent_node
        "rejected_approaches": None,  # Will accumulate if user rejects
        "selected_approach_index": None,  # Will be set by user selection (Phase 4)
        "current_draft": None,   # Will be set by writer_agent_node
        "is_approved": False,    # Will be set by critic or save_output_node
        "revision_count": 0,     # Will be incremented by writer-critic loop (Phase 6)
    }

    # Step 1: Initial invocation - will pause at topic_input_node
    # When interrupt() is called, the graph pauses and invoke() returns
    # with __interrupt__ containing the prompt from interrupt()
    print("Starting Pedagogical Article Writer...")
    print("=" * 50)
    result = graph.invoke(initial_state, config)

    # Step 2: Check if graph is interrupted (waiting for user input)
    # The __interrupt__ key contains a list of Interrupt objects
    # Each has: value (the prompt), id, resumable (always True for interrupt())
    if "__interrupt__" in result:
        # Get the prompt message passed to interrupt()
        prompt = result["__interrupt__"][0].value
        print(f"\n{prompt}")

        # Collect user input
        user_topic = input("> ")

        # Step 3: Resume with user input using Command(resume=...)
        # The value passed to resume becomes the return value of interrupt()
        # in topic_input_node, which then stores it in state["topic"]
        # IMPORTANT: Use the same config (thread_id) to resume the right thread
        print(f"\nResearching and generating approaches for: {user_topic}")
        print("(This may take 30-60 seconds as the agent searches the web...)")
        result = graph.invoke(Command(resume=user_topic), config)

    # Step 4: Handle approach selection interrupt (may loop on rejection)
    # The graph pauses at approach_selection_node after approach_agent completes
    while "__interrupt__" in result:
        prompt = result["__interrupt__"][0].value
        print(f"\n{prompt}")

        user_selection = input("> ")

        if user_selection.lower() == "reject":
            print("\nRegenerating approaches (avoiding previously rejected ones)...")
            print("(This may take 30-60 seconds...)")
        else:
            print(f"\nSelected approach {user_selection}, generating article...")
            print("(This may take 30-60 seconds as the writer creates your article...)")

        result = graph.invoke(Command(resume=user_selection), config)

    # Step 5: Display the selected approach
    print("\n" + "=" * 50)
    print("SELECTED PEDAGOGICAL APPROACH")
    print("=" * 50)

    print(f"\nTopic: {result['topic']}")

    # Display the selected approach (using index from state)
    selected_idx = result["selected_approach_index"]
    if selected_idx is not None and result["approaches"]:
        approach = result["approaches"][selected_idx]
        print(f"\n--- Selected Approach {selected_idx + 1}: {approach['title']} ---")
        print(f"\nDescription: {approach['description']}")
        print(f"\nMetaphor: {approach['metaphor']}")
        print(f"\nWhy Effective: {approach['why_effective']}")
    elif result["approaches"]:
        # Fallback: show all approaches if no selection made
        for i, approach in enumerate(result["approaches"], 1):
            print(f"\n--- Approach {i}: {approach['title']} ---")
            print(f"\nDescription: {approach['description']}")
            print(f"\nMetaphor: {approach['metaphor']}")
            print(f"\nWhy Effective: {approach['why_effective']}")
    else:
        print("\nNo approaches generated. Check API key configuration.")

    # Step 6: Display the generated article
    if result.get("current_draft"):
        print("\n" + "=" * 50)
        print("--- GENERATED ARTICLE ---")
        print("=" * 50)
        print(result["current_draft"])
        print("\n" + "=" * 50)
        print("--- END ARTICLE ---")
        print("=" * 50)

    # Additional state information
    print("\n" + "=" * 50)
    print("WORKFLOW STATE")
    print("=" * 50)
    rejected_count = len(result.get("rejected_approaches") or [])
    print(f"Rejected approaches: {rejected_count}")
    print(f"Selected approach: {result['selected_approach_index'] + 1 if result['selected_approach_index'] is not None else 'None'}")
    draft_preview = result['current_draft'][:100] + "..." if result.get('current_draft') and len(result['current_draft']) > 100 else result.get('current_draft')
    print(f"Draft length: {len(result['current_draft']) if result.get('current_draft') else 0} characters")
    print(f"Approved: {result['is_approved']}")
    print(f"Revisions: {result['revision_count']}")

    # Demonstrate state persistence by retrieving checkpoint
    # Shows that the user-provided topic was persisted
    state_snapshot = graph.get_state(config)
    print(f"\nCheckpoint persisted: {state_snapshot.values['topic'] == result['topic']}")

    # Output files section: show where artifacts were saved
    print("\n" + "=" * 50)
    print("OUTPUT FILES")
    print("=" * 50)
    if result.get("output_path"):
        print(f"Article saved to: {result['output_path']}")
    diagram_path = save_workflow_diagram(graph)
    print(f"Workflow diagram saved to: {diagram_path}")
    print("View diagram at: https://mermaid.live or in VSCode with Mermaid extension")


if __name__ == "__main__":
    main()
