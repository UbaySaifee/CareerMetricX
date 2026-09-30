"""Abstract AI Provider interface for CareerMetricX."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.analysis import InterviewQuestion


class BaseAIProvider(ABC):
    """Abstract interface defining required intelligence operations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the intelligence provider."""
        pass

    @abstractmethod
    async def extract_semantic_requirements(self, text: str) -> dict[str, Any]:
        """Extract structured requirements from job description text."""
        pass

    @abstractmethod
    async def generate_interview_questions(
        self,
        resume_context: dict[str, Any],
        job_context: dict[str, Any],
        gaps: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate targeted, grounded technical interview questions."""
        pass

    @abstractmethod
    async def evaluate_interview_answer(
        self,
        question: dict[str, Any],
        candidate_answer: str,
        claimed_context: str,
    ) -> dict[str, Any]:
        """Evaluate candidate response across relevance, technical correctness, completeness, specificity, clarity, and resume consistency."""
        pass

    @abstractmethod
    async def verify_claims(
        self,
        project_claims: list[str],
        resume_text: str,
    ) -> list[str]:
        """Audit project claims and detect exaggerated metrics, unbacked speedups, or vague assertions."""
        pass

    @abstractmethod
    async def generate_viva_questions(
        self,
        claims: list[str],
        role: str,
        required_skills: list[str],
        missing_skills: list[str],
        experience_level: str = "Mid",
        limit: int = 5,
    ) -> list[InterviewQuestion]:
        """Synthesize viva-targeted interview questions challenging claims and testing missing skills."""
        pass

    @abstractmethod
    async def generate_prep_plan(
        self,
        missing_skills: list[str],
        role: str,
        days: int = 7,
    ) -> list[str]:
        """Generate a structured day-by-day preparation checklist targeting identified skill gaps."""
        pass

    @abstractmethod
    async def generate_star_recommendations(
        self,
        transferable_skills: list[str],
        role: str,
        resume_text: str = "",
    ) -> list[dict[str, str]]:
        """Generate STAR-format bullet point rewrite recommendations for transferable skills."""
        pass

