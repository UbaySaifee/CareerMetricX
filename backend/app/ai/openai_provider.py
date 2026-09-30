"""OpenAI-compatible and Gemini LLM provider implementation with deterministic fallback."""

import json
from typing import Any
import httpx

from app.ai.base import BaseAIProvider
from app.ai.deterministic import DeterministicFallbackProvider
from app.core.config import settings
from app.core.logging import logger
from app.schemas.analysis import InterviewQuestion


class OpenAICompatibleProvider(BaseAIProvider):
    """LLM provider communicating with OpenAI-compatible / Gemini endpoints via asynchronous HTTP."""

    def __init__(self):
        self.fallback = DeterministicFallbackProvider()
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.model_name = settings.AI_MODEL_NAME
        self.timeout = settings.AI_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return f"llm-provider ({self.model_name})"

    async def _call_llm(self, messages: list[dict[str, str]], json_mode: bool = True) -> str | None:
        """Execute an asynchronous POST request to the completions endpoint."""
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": settings.AI_TEMPERATURE,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(
                        "LLM endpoint returned status %s: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return None
        except Exception as exc:
            logger.warning("Error communicating with LLM endpoint: %s. Using deterministic engine.", exc)
            return None

    async def extract_semantic_requirements(self, text: str) -> dict[str, Any]:
        """Extract requirements using LLM with deterministic fallback."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a technical recruitment parser. Return strict JSON with keys: "
                    "'seniority_level', 'must_have_skills' (array), 'preferred_skills' (array), 'responsibilities' (array)."
                ),
            },
            {"role": "user", "content": f"Extract technical requirements from this job description:\n\n{text}"},
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                parsed = json.loads(response_text)
                parsed["is_deterministic"] = False
                return parsed
            except Exception:
                pass
        return await self.fallback.extract_semantic_requirements(text)

    async def generate_interview_questions(
        self,
        resume_context: dict[str, Any],
        job_context: dict[str, Any],
        gaps: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Generate questions using LLM with deterministic fallback."""
        return await self.fallback.generate_interview_questions(resume_context, job_context, gaps, limit)

    async def evaluate_interview_answer(
        self,
        question: dict[str, Any],
        candidate_answer: str,
        claimed_context: str,
    ) -> dict[str, Any]:
        """Evaluate interview answer using LLM with deterministic fallback."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an evidence verifier evaluating a candidate technical answer. "
                    "Return strict JSON with keys: 'scores' (relevance, technical_correctness, completeness, specificity, clarity, resume_consistency between 1.0-10.0), "
                    "'strengths' (array of str), 'missing_points' (array of str), 'improvement_suggestion' (str)."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question.get('question_text')}\nAnswer: {candidate_answer}\nResume Context: {claimed_context}",
            },
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                data["is_advisory"] = True
                data["provider"] = self.provider_name
                return data
            except Exception:
                pass
        return await self.fallback.evaluate_interview_answer(question, candidate_answer, claimed_context)

    async def verify_claims(
        self,
        project_claims: list[str],
        resume_text: str,
    ) -> list[str]:
        """Verify project claims using LLM with deterministic fallback."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a technical audit engine. Review candidate claims for exaggerated metrics, "
                    "unbacked speedups (e.g. 100x without baseline or profiling tools), and vague claims. "
                    "Return strict JSON with key 'flags' containing an array of warning strings."
                ),
            },
            {
                "role": "user",
                "content": f"Project Claims:\n{json.dumps(project_claims)}\n\nFull Resume Context:\n{resume_text[:2000]}",
            },
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                if isinstance(data.get("flags"), list) and data["flags"]:
                    return data["flags"]
            except Exception:
                pass
        return await self.fallback.verify_claims(project_claims, resume_text)

    async def generate_viva_questions(
        self,
        claims: list[str],
        role: str,
        required_skills: list[str],
        missing_skills: list[str],
        experience_level: str = "Mid",
        limit: int = 5,
    ) -> list[InterviewQuestion]:
        """Synthesize viva questions using LLM with deterministic fallback."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an academic and engineering viva interrogator. Generate rigorous technical questions "
                    "testing candidate project claims and probing missing requirements. "
                    "Return strict JSON with key 'questions' containing an array of objects with keys: "
                    "'question' (str), 'target_claim' (str), 'rationale' (str), 'difficulty' ('Junior' | 'Mid' | 'Senior')."
                ),
            },
            {
                "role": "user",
                "content": f"Role: {role} ({experience_level})\nClaims: {json.dumps(claims[:5])}\nMissing Skills: {json.dumps(missing_skills)}\nRequired Skills: {json.dumps(required_skills)}\nLimit: {limit}",
            },
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                raw_qs = data.get("questions", [])
                if isinstance(raw_qs, list) and raw_qs:
                    result: list[InterviewQuestion] = []
                    for q in raw_qs[:limit]:
                        result.append(
                            InterviewQuestion(
                                question=q.get("question", ""),
                                target_claim=q.get("target_claim", ""),
                                rationale=q.get("rationale", ""),
                                difficulty=q.get("difficulty", experience_level),
                            )
                        )
                    return result
            except Exception:
                pass
        return await self.fallback.generate_viva_questions(
            claims, role, required_skills, missing_skills, experience_level, limit
        )

    async def generate_prep_plan(
        self,
        missing_skills: list[str],
        role: str,
        days: int = 7,
    ) -> list[str]:
        """Generate preparation plan with LLM and deterministic fallback."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a technical career coach. Generate a day-by-day 7-day engineering preparation plan "
                    "addressing detected missing skills for a job role. Return strict JSON with key 'prep_plan' (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": f"Target Role: {role}\nMissing Skills: {json.dumps(missing_skills)}\nDuration: {days} days",
            },
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                if isinstance(data.get("prep_plan"), list) and data["prep_plan"]:
                    return data["prep_plan"][:days]
            except Exception:
                pass
        return await self.fallback.generate_prep_plan(missing_skills, role, days)

    async def generate_star_recommendations(
        self,
        transferable_skills: list[str],
        role: str,
        resume_text: str = "",
    ) -> list[dict[str, str]]:
        """Generate STAR-format bullet point recommendations using LLM with deterministic fallback."""
        if not transferable_skills:
            return []

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an executive resume strategist. For each transferable skill, generate an actionable "
                    "STAR-format (Situation-Task-Action-Result) bullet point demonstrating how the candidate can reframe "
                    "their existing adjacent experience to satisfy the job description. "
                    "Return strict JSON with key 'recommendations' containing an array of objects with keys: "
                    "'skill' (str), 'current_gap' (str), 'suggested_bullet' (str)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Target Role: {role}\n"
                    f"Transferable Skills: {json.dumps(transferable_skills)}\n"
                    f"Resume Context: {resume_text[:2000]}"
                ),
            },
        ]
        response_text = await self._call_llm(messages, json_mode=True)
        if response_text:
            try:
                data = json.loads(response_text)
                recs = data.get("recommendations", [])
                if isinstance(recs, list) and recs:
                    validated: list[dict[str, str]] = []
                    for r in recs:
                        if isinstance(r, dict) and "skill" in r and "suggested_bullet" in r:
                            validated.append({
                                "skill": str(r["skill"]),
                                "current_gap": str(r.get("current_gap", f"Transferable competency in {r['skill']}")),
                                "suggested_bullet": str(r["suggested_bullet"]),
                            })
                    if validated:
                        return validated
            except Exception:
                pass
        return await self.fallback.generate_star_recommendations(transferable_skills, role, resume_text)

