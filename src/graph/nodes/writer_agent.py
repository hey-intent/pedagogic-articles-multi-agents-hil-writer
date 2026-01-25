"""Writer agent node - drafts articles using 3Blue1Brown pedagogical style."""

from langchain_openai import ChatOpenAI

from src.config import config, WRITING_MODEL
from src.graph.state import ArticleState


WRITER_SYSTEM_PROMPT = """You are a pedagogical writer creating accessible, engaging articles in the style of 3Blue1Brown. Your goal is to make complex topics intuitive and enjoyable.

## Core Principles

1. **Build intuition first**: Start with concrete examples before definitions. Help readers feel they "could have discovered this themselves."

2. **Use the metaphor throughout**: The approach includes a metaphor - weave it as a recurring thread, referring back when introducing new concepts.

3. **Create "aha!" moments**: Structure explanations so readers experience that satisfying shift in perspective when everything clicks.

4. **Ground abstractions in experience**: Connect every abstract concept to something tangible. Use "Imagine..." and "Think of it like..."

5. **Be conversational but precise**: Write as if explaining to a curious friend. Introduce technical terms naturally with clear context.

## Article Structure

Write a well-structured markdown article with:
- An engaging title that hints at the core insight
- An introduction that poses an intriguing question
- Body sections that progressively build understanding using the metaphor
- A conclusion that ties everything together

Aim for approximately 800-1200 words - substantial enough to build real understanding.

## Output Format

Return clean markdown:
- `#` for the title
- `##` for major sections
- Clear paragraph breaks
- *Emphasis* for key insights"""


def writer_agent_node(state: ArticleState) -> dict:
    """Draft or revise article using selected pedagogical approach.

    This node operates in two modes:
    1. Initial draft: No critic_feedback -> write fresh article
    2. Revision: critic_feedback present -> revise based on feedback

    Mode is detected by checking critic_feedback field in state.

    The node uses WRITER_SYSTEM_PROMPT which establishes the 3Blue1Brown
    pedagogical style: building intuition before formalism, using the provided
    metaphor throughout, creating "aha!" moments, and being conversational
    but precise.

    Args:
        state: Current graph state with topic, approaches, selected_approach_index,
               and optionally critic_feedback and current_draft for revisions.

    Returns:
        Dict with 'current_draft' field containing the (revised) markdown article.
    """
    topic = state["topic"]
    approaches = state["approaches"]
    selected_idx = state["selected_approach_index"]
    approach = approaches[selected_idx]

    # Check for revision mode
    critic_feedback = state.get("critic_feedback")
    current_draft = state.get("current_draft")

    # Create model using WRITING_MODEL from config
    # max_tokens=4096 ensures full article generation without truncation
    # Uses OpenRouter (OpenAI-compatible API) as the provider
    model = ChatOpenAI(
        model=WRITING_MODEL,
        max_tokens=4096,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    if critic_feedback and current_draft:
        # REVISION MODE: Incorporate critic feedback
        user_content = f"""Revise this article based on the critic's feedback.

CURRENT ARTICLE:
{current_draft}

CRITIC FEEDBACK TO ADDRESS:
{critic_feedback}

ORIGINAL CONTEXT:
- Topic: {topic}
- Pedagogical approach: {approach['title']}
- Core metaphor: {approach['metaphor']}

INSTRUCTIONS:
1. Address ALL points raised in the critic feedback
2. Maintain the pedagogical approach and weave the metaphor throughout
3. Keep the 3Blue1Brown style: intuition first, concrete examples, "aha!" moments
4. Provide the COMPLETE revised article (not just the changes)"""
    else:
        # INITIAL DRAFT MODE
        approach_text = f"""Title: {approach['title']}

Description: {approach['description']}

Core Metaphor: {approach['metaphor']}

Why This Works: {approach['why_effective']}"""

        user_content = f"""Write an educational article about: {topic}

Use this pedagogical approach throughout the article:

{approach_text}

Remember to weave the metaphor throughout your explanation, returning to it when introducing new concepts."""

    messages = [
        {"role": "system", "content": WRITER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    response = model.invoke(messages)

    return {"current_draft": response.content}
