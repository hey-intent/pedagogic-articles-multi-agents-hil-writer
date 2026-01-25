"""Critic agent node - evaluates article drafts for the reflection loop."""

from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.types import Command

from src.config import config, REASONING_MODEL
from src.graph.state import ArticleState
from src.schemas import CriticEvaluation


# Maximum writer-critic iterations before forced approval (LOOP-03)
MAX_ITERATIONS = 3


CRITIC_SYSTEM_PROMPT = """You are a pedagogical content critic evaluating educational articles.
Your role is to ensure articles are BOTH technically accurate AND accessible to beginners.

## Evaluation Criteria

### 1. ACCURACY (Score 1-10)
Evaluate technical correctness:
- Are all facts and concepts correct?
- Are there any misleading simplifications?
- Would an expert find errors?

Score guide:
- 10: Perfectly accurate, no issues
- 7-9: Minor issues that don't mislead
- 4-6: Some errors that could confuse
- 1-3: Major factual errors

### 2. COMPREHENSIBILITY (Score 1-10)
Evaluate accessibility for beginners:
- Is the metaphor used effectively throughout?
- Are concepts introduced gradually?
- Would a curious beginner understand this?

Score guide:
- 10: Crystal clear, delightful to read
- 7-9: Clear with minor rough spots
- 4-6: Confusing in places
- 1-3: Incomprehensible to beginners

## Approval Decision

APPROVE (approved=True) ONLY IF:
- accuracy_score >= 7 AND comprehensibility_score >= 7

REJECT (approved=False) IF:
- Either score < 7

## Feedback Guidelines

When rejecting, provide:
1. Specific issues (quote problematic text)
2. Concrete suggestions for improvement
3. Priority: accuracy issues first, then comprehensibility

When approving:
- feedback should be empty string
- accuracy_issues and comprehensibility_issues should be empty strings"""


def critic_agent_node(state: ArticleState) -> Command[Literal["writer_agent", "save_output"]]:
    """Evaluate article draft and route to writer (revision) or save_output (approved).

    LangGraph Pattern: Reflection Loop with Command Routing
    =======================================================
    This node implements the critic side of a writer-critic reflection loop.
    The pattern:
    1. Evaluate the current draft against quality criteria
    2. If approved (both scores >= 7) OR max iterations reached:
       Return Command(goto="save_output") to complete workflow
    3. If revision needed:
       Return Command(goto="writer_agent", update={"critic_feedback": feedback})
       The update= parameter atomically sets state before routing

    Key insight: Checking iteration limit BEFORE LLM call avoids wasted
    API calls when we've already decided to terminate.

    This node implements the critic side of the reflection loop. It evaluates
    the current draft against accuracy and comprehensibility criteria, then
    routes based on approval status.

    Termination conditions (LOOP-02, LOOP-03):
    1. Critic approves (both scores >= 7) -> route to save_output
    2. Max iterations reached (revision_count >= 3) -> force approval, route to save_output

    The Command return type annotation specifies valid routing destinations
    and is REQUIRED for graph validation.

    Args:
        state: Current graph state with current_draft and revision_count.

    Returns:
        Command routing to writer_agent (for revision) or save_output (for completion).
    """
    current_draft = state["current_draft"]
    revision_count = state.get("revision_count", 0)

    # CRITICAL: Check iteration limit FIRST to prevent runaway loops (LOOP-03)
    if revision_count >= MAX_ITERATIONS:
        return Command(
            update={"is_approved": True},  # Force approval
            goto="save_output",
        )

    # Create model for evaluation using REASONING_MODEL from config
    model = ChatOpenAI(
        model=REASONING_MODEL,
        base_url=config.openrouter_base_url,
        api_key=config.openrouter_api_key,
    )

    # Use structured output for reliable evaluation parsing
    model_structured = model.with_structured_output(CriticEvaluation)

    messages = [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Evaluate this pedagogical article:\n\n{current_draft}"},
    ]

    evaluation = model_structured.invoke(messages)

    if evaluation.approved:
        # Article meets quality criteria - route to output
        return Command(
            update={
                "is_approved": True,
                "critic_feedback": None,
            },
            goto="save_output",
        )
    else:
        # Article needs revision - increment counter and route to writer (LOOP-04)
        return Command(
            update={
                "is_approved": False,
                "critic_feedback": evaluation.feedback,
                "revision_count": revision_count + 1,
            },
            goto="writer_agent",
        )
