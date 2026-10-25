from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# VLM Finding
# ============================================================

class VLMFinding(BaseModel):
    """
    Represents one visual finding identified from a webpage screenshot.
    """

    model_config = ConfigDict(
        populate_by_name=True
    )

    id: str = Field(
        description="Unique identifier for the visual finding."
    )

    category: str = Field(
        description=(
            "Visual UX category such as visual_hierarchy, "
            "spacing, alignment, typography, navigation, "
            "clutter, consistency, or cognitive_load."
        )
    )

    severity: str = Field(
        description="Severity of the finding: critical, high, medium, or low."
    )

    element_description: Optional[str] = Field(
        default=None,
        validation_alias="element",
        description="Description of the webpage element involved."
    )

    problem: str = Field(
        description="The visual or UX problem observed."
    )

    evidence: str = Field(
        validation_alias="visual_evidence",
        description="Specific visual evidence supporting the finding."
    )

    recommendation: str = Field(
        description="Actionable recommendation for improving the issue."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence between 0 and 1."
    )

# ============================================================
# VLM Response
# ============================================================

class VLMResponse(BaseModel):
    """
    Complete structured response returned by the VLM.
    """

    findings: List[VLMFinding]


# ============================================================
# AI Critic Finding
# ============================================================

class CriticFinding(BaseModel):
    """
    Represents a finding after reasoning over crawler,
    HCI-rule, and visual evidence.
    """

    id: str = Field(
        description="Unique identifier for the final finding."
    )

    category: str = Field(
        description="Category of the usability or UX issue."
    )

    heuristic_id: Optional[str] = Field(
        default=None,
        description="Related Nielsen heuristic ID, if applicable."
    )

    severity: str = Field(
        description="Final severity: critical, high, medium, or low."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the finding is valid."
    )

    element: Optional[str] = Field(
        default=None,
        description="Element or component affected by the issue."
    )

    problem: str = Field(
        description="Clear explanation of the usability problem."
    )

    evidence: str = Field(
        description="Evidence supporting the finding."
    )

    user_impact: str = Field(
        description="How the problem can affect users."
    )

    recommendation: str = Field(
        description="Actionable recommendation to fix the problem."
    )


# ============================================================
# AI Critic Response
# ============================================================

class CriticResponse(BaseModel):
    """
    Complete structured response returned by the AI critic.
    """

    findings: List[CriticFinding]