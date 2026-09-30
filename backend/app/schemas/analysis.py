"""Pydantic v2 schemas for Job Description and Analysis/Evaluation."""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class JDCreate(BaseModel):
    """Schema for submitting a Job Description for analysis."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., description="Target job title or role name", min_length=1)
    experience_level: str = Field(..., description="Target experience level (e.g. Junior, Mid, Senior, Lead)")
    required_skills: list[str] = Field(..., description="Mandatory core skill requirements")
    preferred_skills: list[str] = Field(default_factory=list, description="Bonus/preferred skills")
    description: str = Field(..., description="Full text description of the target job position")


class SkillGapResult(BaseModel):
    """Categorized skill alignment results and multidimensional radar scores."""

    model_config = ConfigDict(extra="ignore")

    matched_skills: list[str] = Field(default_factory=list, description="Directly demonstrated skills (>= 0.70 match)")
    transferable_skills: list[str] = Field(default_factory=list, description="Adjacent foundational skills (0.50 - 0.69 match)")
    missing_skills: list[str] = Field(default_factory=list, description="Completely unaddressed requirements (< 0.50 match)")
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall weighted requirement match score")
    radar_metrics: dict[str, float] = Field(
        ...,
        description="5-dimension competency breakdown: Core Skills, Transferable, System Design, Tooling, Claim Credibility"
    )


class InterviewQuestion(BaseModel):
    """Targeted viva or technical interview question grounded in resume claims and gaps."""

    model_config = ConfigDict(extra="ignore")

    question: str = Field(..., description="The interrogation question text")
    target_claim: str = Field(..., description="Specific claim, project snippet, or missing skill being tested")
    rationale: str = Field(..., description="Technical justification for posing this question")
    difficulty: Literal["Junior", "Mid", "Senior"] | str = Field("Mid", description="Target difficulty tier")


class StarRecommendation(BaseModel):
    """Actionable STAR-format bullet recommendation to optimize transferable skills."""

    model_config = ConfigDict(extra="ignore")

    skill: str = Field(..., description="Target transferable skill")
    current_gap: str = Field(..., description="Description of current adjacent skill context or gap")
    suggested_bullet: str = Field(..., description="Recommended STAR-format resume bullet point")


class AnalysisResponse(BaseModel):
    """Complete candidate readiness and verification analysis response."""

    model_config = ConfigDict(extra="ignore")

    evaluation_id: Optional[str] = Field(None, description="Unique identifier for the persisted evaluation report")
    candidate_name: Optional[str] = Field(None, description="Extracted candidate name from document")
    role_applied: str = Field(..., description="Target job role applied for")
    gap_analysis: SkillGapResult = Field(..., description="Categorized skill analysis and radar metrics")
    verification_flags: list[str] = Field(
        default_factory=list,
        description="Audit warnings regarding unsubstantiated metrics, ATS anomalies, or exaggerated claims"
    )
    targeted_questions: list[InterviewQuestion] = Field(
        default_factory=list,
        description="Grounded interview questions challenging claims and testing gaps"
    )
    prep_plan: list[str] = Field(
        default_factory=list,
        description="7-day targeted engineering remediation roadmap"
    )
    star_recommendations: list[StarRecommendation] = Field(
        default_factory=list,
        description="Actionable STAR-format resume rewrite recommendations for transferable skills"
    )
    created_at: Optional[str] = Field(None, description="ISO timestamp of evaluation creation")
