"""Pydantic models for pedagogical approach output.

This module defines the structured output schemas used by the approach agent
to return exactly 3 pedagogical approaches. These models are used with
ChatAnthropic.with_structured_output() to ensure validated responses.
"""

from pydantic import BaseModel, Field


class PedagogicalApproach(BaseModel):
    """A single pedagogical approach for teaching a topic."""

    title: str = Field(
        description="A concise, descriptive title for this teaching approach"
    )
    description: str = Field(
        description="2-3 sentences explaining how this approach teaches the topic"
    )
    metaphor: str = Field(
        description="A concrete metaphor or analogy that makes the concept intuitive. "
        "Should relate the topic to something familiar and tangible."
    )
    why_effective: str = Field(
        description="1-2 sentences explaining why this approach is effective for learners"
    )


class ApproachList(BaseModel):
    """Container for exactly 3 pedagogical approaches."""

    approaches: list[PedagogicalApproach] = Field(
        description="Exactly 3 distinct pedagogical approaches for teaching the topic",
        min_length=3,
        max_length=3,
    )
