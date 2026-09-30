"""Semantic Gap Analysis Engine powered by SentenceTransformers and cosine similarity."""

import re
from typing import Optional
import numpy as np

from app.schemas.analysis import SkillGapResult

# Singleton holder for SentenceTransformer model
_embedding_model = None


def get_embedding_model():
    """Lazily load and return the SentenceTransformer singleton model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            _embedding_model = None
    return _embedding_model


def _chunk_resume_text(resume_text: str, sections: Optional[dict[str, str]] = None) -> list[str]:
    """Break resume into meaningful semantic chunks for similarity comparison."""
    chunks: list[str] = []

    # Priority sections for technical claims
    if sections:
        source_texts = [
            sections.get("skills", ""),
            sections.get("projects", ""),
            sections.get("experience", ""),
            sections.get("summary", ""),
        ]
        combined = "\n".join(t for t in source_texts if t).strip()
    else:
        combined = resume_text

    if not combined:
        combined = resume_text

    # Split by lines and sentence boundaries
    raw_lines = combined.split("\n")
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # Clean bullet indicators
        cleaned = re.sub(r"^[•\-*]\s*", "", line).strip()
        if len(cleaned) >= 10:
            chunks.append(cleaned)

    # If chunks are too few, split whole text by sentences
    if len(chunks) < 5:
        sentences = re.split(r"(?<=[.!?])\s+", resume_text)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) >= 15:
                chunks.append(s_clean)

    return chunks if chunks else [resume_text]


def compute_skill_gaps(
    required_skills: list[str],
    resume_text: str,
    preferred_skills: Optional[list[str]] = None,
    sections: Optional[dict[str, str]] = None,
) -> SkillGapResult:
    """Analyze skill coverage using semantic embeddings, categorization thresholds, and 5-dimension radar scoring."""
    preferred_skills = preferred_skills or []
    cleaned_resume_lower = resume_text.lower()

    matched: list[str] = []
    transferable: list[str] = []
    missing: list[str] = []

    chunks = _chunk_resume_text(resume_text, sections)
    model = get_embedding_model()

    if model is not None and chunks:
        # Encode skills and resume chunks
        skill_embeddings = model.encode(required_skills, normalize_embeddings=True)
        chunk_embeddings = model.encode(chunks, normalize_embeddings=True)

        # Compute cosine similarity matrix: (num_skills, num_chunks)
        similarity_matrix = np.dot(skill_embeddings, chunk_embeddings.T)

        for idx, skill in enumerate(required_skills):
            max_sim = float(np.max(similarity_matrix[idx])) if similarity_matrix.size > 0 else 0.0

            # Exact keyword override: If verbatim skill exists in resume, ensure minimum 0.85 match
            skill_pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(skill_pattern, cleaned_resume_lower):
                max_sim = max(max_sim, 0.88)

            # Categorize based on strict rubric
            if max_sim >= 0.70:
                matched.append(skill)
            elif max_sim >= 0.50:
                transferable.append(skill)
            else:
                missing.append(skill)
    else:
        # Graceful heuristic fallback if model could not be loaded
        for skill in required_skills:
            skill_clean = skill.lower().strip()
            pattern = r"\b" + re.escape(skill_clean) + r"\b"
            if re.search(pattern, cleaned_resume_lower):
                matched.append(skill)
            elif any(part in cleaned_resume_lower for part in skill_clean.split() if len(part) > 3):
                transferable.append(skill)
            else:
                missing.append(skill)

    # Calculate overall requirement match percentage
    total_reqs = len(required_skills)
    if total_reqs == 0:
        match_percentage = 100.0
    else:
        # Weighting: 1.0 for matched, 0.70 for transferable
        weighted_score = (len(matched) * 1.0) + (len(transferable) * 0.70)
        match_percentage = round(min(100.0, (weighted_score / total_reqs) * 100.0), 1)

    # 5-Dimension Radar Metrics
    radar_metrics = _compute_radar_metrics(
        matched=matched,
        transferable=transferable,
        total_reqs=total_reqs,
        resume_text=resume_text,
    )

    return SkillGapResult(
        matched_skills=matched,
        transferable_skills=transferable,
        missing_skills=missing,
        match_percentage=match_percentage,
        radar_metrics=radar_metrics,
    )


def _compute_radar_metrics(
    matched: list[str],
    transferable: list[str],
    total_reqs: int,
    resume_text: str,
) -> dict[str, float]:
    """Compute 5-dimension competency breakdown scores (0.0 to 100.0)."""
    lowered = resume_text.lower()

    # 1. Core Skills Score
    core_score = round(min(100.0, (len(matched) / max(1, total_reqs)) * 100.0), 1)

    # 2. Transferable Skills Score
    trans_score = round(min(100.0, (len(transferable) / max(1, total_reqs)) * 100.0 * 1.5), 1)
    if not transferable:
        trans_score = min(50.0, core_score * 0.5)

    # 3. System Design Dimensions
    sys_design_keywords = [
        "microservices", "system design", "architecture", "distributed", "scalab",
        "load balanc", "cache", "redis", "kafka", "latency", "throughput",
        "concurrency", "async", "event-driven", "fault tolerant", "sharding", "database"
    ]
    sys_count = sum(1 for kw in sys_design_keywords if kw in lowered)
    sys_design_score = round(min(100.0, 30.0 + (sys_count * 8.0)), 1)

    # 4. Tooling & DevOps Dimensions
    tooling_keywords = [
        "docker", "kubernetes", "git", "ci/cd", "pipeline", "linux", "pytest",
        "unit test", "aws", "gcp", "azure", "terraform", "prometheus", "grafana",
        "nginx", "monitoring", "postman"
    ]
    tool_count = sum(1 for kw in tooling_keywords if kw in lowered)
    tooling_score = round(min(100.0, 35.0 + (tool_count * 7.5)), 1)

    # 5. Claim Credibility (Presence of verifiable quantitative metrics)
    metric_patterns = [
        r"\b\d+%\b",               # Percentages (e.g. 40%)
        r"\b\d+x\b",               # Multipliers (e.g. 10x)
        r"\b\d+\s*ms\b",           # Latencies (e.g. 50ms)
        r"\b\d+k\b",               # Volumes (e.g. 100k)
        r"\b\d+\s*users\b",        # User scale
        r"\b\d+\s*requests?\b",    # Request volume
    ]
    metric_hits = sum(len(re.findall(pat, lowered)) for pat in metric_patterns)
    credibility_base = 50.0
    credibility_score = round(min(95.0, credibility_base + (metric_hits * 6.5)), 1)

    return {
        "Core Skills": float(core_score),
        "Transferable": float(trans_score),
        "System Design": float(sys_design_score),
        "Tooling": float(tooling_score),
        "Claim Credibility": float(credibility_score),
    }
