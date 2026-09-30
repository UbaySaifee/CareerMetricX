"""Unit tests verifying the Deterministic AI Provider."""

import asyncio

from app.ai.deterministic import DeterministicFallbackProvider


def test_deterministic_requirement_extraction():
    """Verify deterministic fallback parses tech skills and seniority."""
    provider = DeterministicFallbackProvider()
    sample_jd = """
    Senior Backend Engineer
    We are seeking an experienced engineer to build high-scale microservices.
    Requirements:
    - 5+ years experience in Python and FastAPI.
    - Deep knowledge of Docker and PostgreSQL.
    - Experience with Redis and Kafka preferred.
    """
    result = asyncio.run(provider.extract_semantic_requirements(sample_jd))
    assert result["seniority_level"] == "Senior"
    assert "Python" in result["must_have_skills"] or "Fastapi" in result["must_have_skills"]
    assert result["is_deterministic"] is True


def test_deterministic_question_generation():
    """Verify questions are grounded in candidate project context and gaps."""
    provider = DeterministicFallbackProvider()
    resume_context = {
        "projects": [
            {
                "name": "CloudMetric",
                "technologies": ["FastAPI", "PostgreSQL", "Docker"]
            }
        ]
    }
    gaps = [{"skill": "Kafka", "severity": "CRITICAL"}]

    questions = asyncio.run(provider.generate_interview_questions(resume_context, {}, gaps, limit=2))
    assert len(questions) == 2
    assert any("CloudMetric" in q["question_text"] for q in questions)
    assert any("Kafka" in q["question_text"] for q in questions)


def test_deterministic_answer_evaluation():
    """Verify answer evaluation scores across 6 dimensions and flags advisory status."""
    provider = DeterministicFallbackProvider()
    question = {
        "question_id": "q1",
        "question_text": "How did you manage database connection pooling in your async FastAPI service?"
    }
    answer = "I configured asyncpg connection pool with minimum 10 and maximum 50 connections to reduce query latency and prevent pool exhaustion under load."

    eval_result = asyncio.run(provider.evaluate_interview_answer(question, answer, ""))
    assert "scores" in eval_result
    scores = eval_result["scores"]
    assert scores["relevance"] >= 5.0
    assert scores["technical_correctness"] >= 5.0
    assert eval_result["is_advisory"] is True
    assert len(eval_result["strengths"]) > 0


def test_viva_question_template_skips_leading_verbs():
    """Verify viva questions do not use leading action verbs (Architected, Engineered) as tool names."""
    from app.ai.deterministic import extract_technology_from_claim

    # 1. Claims with leading action verbs and real technologies
    assert extract_technology_from_claim("Architected high-throughput REST APIs in FastAPI.") == "FastAPI"
    assert extract_technology_from_claim("Engineered backend services with Node.js and MongoDB.") in ["Node.js", "MongoDB"]
    assert extract_technology_from_claim("Developed microservices using Express and Redis.") in ["Express", "Redis"]

    # 2. Claim with only leading verb and no known technology
    assert extract_technology_from_claim("Delivered 100% test coverage with zero downtime.") is None

    # 3. Test question phrasing via generate_viva_questions
    provider = DeterministicFallbackProvider()
    claims = [
        "Architected async event loop in FastAPI processing 12k concurrent connections.",
        "Engineered real-time notification engine with Node.js and MongoDB.",
        "Delivered zero downtime deployment across cloud clusters."
    ]
    questions = asyncio.run(
        provider.generate_viva_questions(
            claims=claims,
            role="Backend Engineer",
            required_skills=["FastAPI", "Node.js"],
            missing_skills=[],
            experience_level="Senior",
            limit=3
        )
    )

    # Must NOT have "using Architected" or "using Engineered" or "using Delivered"
    for q in questions:
        assert "using Architected" not in q.question
        assert "using Engineered" not in q.question
        assert "using Delivered" not in q.question
        assert "what design trade-offs you evaluated?" in q.question

    # First question should use FastAPI
    assert "using FastAPI" in questions[0].question
    # Second question should use Node.js
    assert "using Node.js" in questions[1].question
    # Third question has no tool, should have clean phrasing:
    assert "Can you explain the underlying architecture, what baseline" in questions[2].question

