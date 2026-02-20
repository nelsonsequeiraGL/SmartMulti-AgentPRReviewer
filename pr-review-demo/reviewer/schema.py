from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class IssueSeverity(str, Enum):
    high = "high"
    med = "med"
    low = "low"


class ReviewerType(str, Enum):
    security = "security"
    performance = "performance"
    maintainability = "maintainability"


class Issue(BaseModel):
    """A single finding from a review (e.g. file/line range, title, details, suggestion)."""

    model_config = ConfigDict(extra="forbid")

    severity: IssueSeverity
    file: str = Field(..., min_length=1)
    lines: str = Field(..., min_length=1, description='Line range, e.g. "12-18" or "L12-L18"')
    title: str = Field(..., min_length=1)
    details: str = Field(..., min_length=1)
    suggestion: str = Field(..., min_length=1)


class AgentReview(BaseModel):
    """Review output from one agent (reviewer type, summary, list of issues)."""

    model_config = ConfigDict(extra="forbid")

    reviewer: ReviewerType
    summary: str = Field(..., min_length=1)
    issues: list[Issue]
