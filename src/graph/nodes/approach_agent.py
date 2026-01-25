"""Approach agent node - generates pedagogical approaches using LLM with tools."""

from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

from src.config import config, REASONING_MODEL
from src.graph.state import ArticleState
from src.schemas import ApproachList
from src.tools import web_search, read_webpage


APPROACH_AGENT_SYSTEM_PROMPT = """You are a pedagogical expert who creates teaching approaches.
Given a topic, research existing educational resources and create exactly 3 distinct
pedagogical approaches, each with a unique metaphor or analogy.

Use the web_search tool to find relevant teaching resources about the topic.
Use the read_webpage tool to read promising pages for detailed content.

After researching (typically 2-3 searches), provide your final answer with exactly 3 approaches.
Each approach must have:
- A clear, descriptive title
- A 2-3 sentence description of how to teach the topic using this approach
- A concrete metaphor or analogy that makes the concept intuitive
- An explanation of why this approach is effective for learners"""


def approach_agent_node(state: ArticleState) -> dict:
    """Generate 3 pedagogical approaches using LLM with web search tools.

    This node implements an inline tool-calling loop pattern. Rather than using
    a subgraph (like create_react_agent), it runs the tool loop directly within
    the node. This simpler approach works well for single-purpose agents that
    don't need complex state management.

    How it works:
    1. Get the topic from state
    2. Check for rejected approaches and add to prompt if present
    3. Create a model with tools bound via bind_tools()
       - bind_tools() enables the LLM to request tool calls in its response
    4. Send the topic to the LLM with system prompt
    5. If the LLM requests tool calls, execute them and feed results back
       - Tool results are wrapped in ToolMessage objects
       - The tool_call_id links each result to its corresponding call
    6. Repeat until the LLM stops requesting tools (max 10 iterations)
       - Max iterations prevents infinite loops from runaway agents
    7. Get structured output via with_structured_output(ApproachList)
       - with_structured_output() ensures the LLM returns exactly 3 approaches
       - Pydantic validation enforces the schema
    8. Convert the Pydantic models to dicts for state storage

    Args:
        state: Current graph state containing the topic and possibly rejected approaches.

    Returns:
        Dict with 'approaches' field - list of approach dicts, each containing
        title, description, metaphor, and why_effective.
    """
    topic = state["topic"]
    rejected = state.get("rejected_approaches") or []
    tools = [web_search, read_webpage]

    # Build system prompt, including rejection context if user rejected previous approaches.
    # This ensures the agent generates completely different approaches on retry.
    system_prompt = APPROACH_AGENT_SYSTEM_PROMPT

    if rejected:
        system_prompt += "\n\n--- IMPORTANT ---\n"
        system_prompt += "The user has REJECTED the following approaches. "
        system_prompt += "Do NOT repeat these. Generate completely DIFFERENT approaches:\n\n"
        for r in rejected:
            system_prompt += f"REJECTED: \"{r['title']}\"\n"
            system_prompt += f"  - Metaphor was: \"{r['metaphor']}\"\n\n"
        system_prompt += "Create 3 NEW approaches with different titles and metaphors.\n"

    # Create the base model using REASONING_MODEL from config
    # Uses OpenRouter (OpenAI-compatible API) as the provider
    model = ChatOpenAI(
        model=REASONING_MODEL,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    # bind_tools() enables tool calling by adding tool schemas to the model.
    # The LLM can then request tool calls in its response via tool_calls field.
    model_with_tools = model.bind_tools(tools)

    # with_structured_output() creates a model variant that returns typed output.
    # ApproachList is a Pydantic model that validates exactly 3 approaches.
    model_structured = model.with_structured_output(ApproachList)

    # Build the initial conversation with system prompt and user message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create 3 pedagogical approaches for teaching: {topic}"},
    ]

    # Tool-calling loop: let the agent research via tools before final output.
    # Max iterations prevents infinite loops if the agent keeps calling tools.
    max_iterations = 3
    for _ in range(max_iterations):
        # Invoke the model - may return tool calls or a text response
        response = model_with_tools.invoke(messages)
        messages.append(response)

        # If no tool calls, the agent is done researching
        if not response.tool_calls:
            break

        # Execute each requested tool call and add results to conversation
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Dispatch to the appropriate tool
            if tool_name == "web_search":
                result = web_search.invoke(tool_args)
            elif tool_name == "read_webpage":
                result = read_webpage.invoke(tool_args)
            else:
                result = f"Unknown tool: {tool_name}"

            # Wrap result in ToolMessage with the call ID to link it properly.
            # The tool_call_id is essential - it tells the LLM which call
            # this result corresponds to.
            messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
            ))

    # After research, get the structured final output.
    # This separate call ensures we get exactly 3 approaches in the right format.
    final_prompt = messages + [
        {"role": "user", "content": "Now provide exactly 3 pedagogical approaches based on your research."}
    ]
    structured_response = model_structured.invoke(final_prompt)

    # Convert Pydantic models to dicts for state storage.
    # State uses TypedDict with list[dict], not Pydantic models.
    approaches = [
        {
            "title": a.title,
            "description": a.description,
            "metaphor": a.metaphor,
            "why_effective": a.why_effective,
        }
        for a in structured_response.approaches
    ]

    return {"approaches": approaches}
