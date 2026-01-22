"""Critic evaluation schema for the reflection loop.

This module defines the CriticEvaluation Pydantic model used for structured
output when the critic agent evaluates article drafts.
"""

from pydantic import BaseModel, Field


class CriticEvaluation(BaseModel):
    """Structured output for critic agent evaluation.

    The critic evaluates articles on two dimensions (AGNT-05):
    1. Accuracy: Technical correctness of the content
    2. Comprehensibility: Accessibility for beginners

    Approval threshold: Both scores >= 7 (out of 10).

    When approved, feedback and issue fields should be empty strings.
    When rejected, feedback provides specific, actionable improvements.
    """

    accuracy_score: int = Field(
        ge=1,
        le=10,
        description="Score 1-10 for technical accuracy. 10=perfectly accurate, 1=major errors.",
    )
    accuracy_issues: str = Field(
        description="Specific accuracy issues found. Empty string if score >= 7.",
    )
    comprehensibility_score: int = Field(
        ge=1,
        le=10,
        description="Score 1-10 for beginner accessibility. 10=crystal clear, 1=incomprehensible.",
    )
    comprehensibility_issues: str = Field(
        description="Specific comprehensibility issues found. Empty string if score >= 7.",
    )
    approved: bool = Field(
        description="True ONLY if BOTH accuracy_score >= 7 AND comprehensibility_score >= 7.",
    )
    feedback: str = Field(
        description="Combined actionable feedback for the writer. Lists specific improvements needed. Empty string if approved.",
    )
