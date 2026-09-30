"""Semantic Gap Analysis Engine powered by SentenceTransformers and cosine similarity."""

import math
import os
import re
from collections import Counter

import numpy as np

from app.core.logging import logger
from app.schemas.analysis import SkillGapResult

# Singleton holder for SentenceTransformer model
_embedding_model = None


def get_embedding_model():
    """Lazily load and return the SentenceTransformer singleton model with memory safety."""
    global _embedding_model

    # Check for explicit low-memory flag (e.g. on Render free tier to stay < 60 MB RAM)
    if os.getenv("LOW_MEMORY_MODE", "").strip().lower() in ("true", "1", "yes"):
        logger.info("LOW_MEMORY_MODE='true' set. Skipping SentenceTransformer load to run in <60 MB RAM.")
        return None

    if _embedding_model is None:
        try:
            import torch

            # Memory safety: restrict to 1 thread to prevent OOM and thread over-allocation on Render
            torch.set_num_threads(1)
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer (all-MiniLM-L6-v2) loaded successfully with torch.set_num_threads(1).")
        except (MemoryError, Exception) as e:
            logger.warning("Could not load SentenceTransformer (%s). Falling back to lightweight memory mode.", e)
            _embedding_model = None
    return _embedding_model


def _tokenize_text(text: str) -> list[str]:
    """Extract lowercased alphanumeric tokens preserving technology terms."""
    raw = re.findall(r"[a-z0-9+#]+(?:\.[a-z0-9+#]+)*", text.lower())
    return [t.strip(".") for t in raw if len(t.strip(".")) > 0]


def _compute_lightweight_similarities(
    required_skills: list[str],
    chunks: list[str],
    resume_text: str,
) -> dict[str, float]:
    """Fast, memory-efficient (<60 MB RAM) skill similarity using token-overlap and TF-IDF."""
    cleaned_resume_lower = resume_text.lower()
    resume_tokens = _tokenize_text(resume_text)
    resume_vocab = set(resume_tokens)

    # Documents for TF-IDF corpus: chunks + fallback
    docs = chunks if chunks else [resume_text]
    num_docs = len(docs)

    # Pre-tokenize all chunks
    doc_token_lists = [_tokenize_text(d) for d in docs]
    doc_word_sets = [set(t_list) for t_list in doc_token_lists]

    # Compute Document Frequency (DF) across chunks
    doc_freq: dict[str, int] = Counter()
    for word_set in doc_word_sets:
        for w in word_set:
            doc_freq[w] += 1

    # Smoothed Inverse Document Frequency (IDF)
    # IDF(w) = ln((num_docs + 1) / (DF(w) + 1)) + 1.0
    idf_cache: dict[str, float] = {}
    for w, df in doc_freq.items():
        idf_cache[w] = math.log((num_docs + 1.0) / (df + 1.0)) + 1.0
    default_idf = math.log(num_docs + 1.0) + 1.0

    # Compute normalized TF-IDF vectors for documents
    doc_vectors: list[dict[str, float]] = []
    for t_list, w_set in zip(doc_token_lists, doc_word_sets, strict=False):
        if not t_list:
            doc_vectors.append({})
            continue
        counts = Counter(t_list)
        total_tokens = float(len(t_list))
        vec: dict[str, float] = {}
        sq_sum = 0.0
        for w in w_set:
            tf = counts[w] / total_tokens
            tfidf = tf * idf_cache.get(w, default_idf)
            vec[w] = tfidf
            sq_sum += tfidf * tfidf
        norm = math.sqrt(sq_sum)
        if norm > 0:
            for w in vec:
                vec[w] /= norm
        doc_vectors.append(vec)

    skill_scores: dict[str, float] = {}

    for skill in required_skills:
        skill_clean = skill.lower().strip()
        skill_tokens = _tokenize_text(skill_clean)
        skill_words = set(skill_tokens)

        # 1. Exact verbatim regex boundary match override
        skill_pattern = r"\b" + re.escape(skill_clean) + r"\b"
        if re.search(skill_pattern, cleaned_resume_lower):
            skill_scores[skill] = 0.90
            continue

        if not skill_words:
            skill_scores[skill] = 0.0
            continue

        # Build skill TF-IDF vector
        skill_counts = Counter(skill_tokens)
        skill_total = float(len(skill_tokens))
        skill_vec: dict[str, float] = {}
        skill_sq_sum = 0.0
        skill_idf_sum = 0.0
        for w in skill_words:
            idf_val = idf_cache.get(w, default_idf)
            skill_idf_sum += idf_val
            tf = skill_counts[w] / skill_total
            tfidf = tf * idf_val
            skill_vec[w] = tfidf
            skill_sq_sum += tfidf * tfidf
        skill_norm = math.sqrt(skill_sq_sum)
        if skill_norm > 0:
            for w in skill_vec:
                skill_vec[w] /= skill_norm

        best_score = 0.0

        # 2. Check each chunk for co-occurrence, token overlap, and TF-IDF cosine similarity
        for d_words, d_vec in zip(doc_word_sets, doc_vectors, strict=False):
            if not d_words:
                continue

            matched_in_chunk = skill_words & d_words
            if not matched_in_chunk:
                continue

            # Fractional token overlap within this chunk
            token_overlap = len(matched_in_chunk) / len(skill_words)

            # IDF-weighted overlap (gives more weight to rare technical terms)
            matched_idf_sum = sum(idf_cache.get(w, default_idf) for w in matched_in_chunk)
            idf_overlap = matched_idf_sum / skill_idf_sum if skill_idf_sum > 0 else token_overlap

            # Cosine similarity with chunk TF-IDF vector
            cos_sim = sum(skill_vec[w] * d_vec.get(w, 0.0) for w in matched_in_chunk)

            # If all tokens of the skill are present in this chunk, high confidence match
            if token_overlap >= 1.0:
                chunk_score = 0.88
            else:
                chunk_score = 0.5 * token_overlap + 0.3 * idf_overlap + 0.2 * min(1.0, cos_sim * 2.0)

            if chunk_score > best_score:
                best_score = chunk_score

        # 3. Resume-wide token coverage if tokens appear across different chunks
        matched_resume = skill_words & resume_vocab
        if matched_resume:
            resume_overlap = len(matched_resume) / len(skill_words)
            matched_res_idf = sum(idf_cache.get(w, default_idf) for w in matched_resume)
            res_idf_overlap = matched_res_idf / skill_idf_sum if skill_idf_sum > 0 else resume_overlap

            if resume_overlap >= 1.0:
                res_score = 0.75
            elif resume_overlap >= 0.50:
                res_score = 0.55 * resume_overlap + 0.45 * res_idf_overlap
            else:
                res_score = 0.35 * resume_overlap

            if res_score > best_score:
                best_score = res_score

        # 4. Substring / stem heuristics for multi-word or compound skills
        if best_score < 0.50:
            if any(part in cleaned_resume_lower for part in skill_clean.split() if len(part) > 3):
                best_score = max(best_score, 0.52)

        skill_scores[skill] = best_score

    return skill_scores


def _chunk_resume_text(resume_text: str, sections: dict[str, str] | None = None) -> list[str]:
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
    preferred_skills: list[str] | None = None,
    sections: dict[str, str] | None = None,
) -> SkillGapResult:
    """Analyze skill coverage using semantic embeddings, categorization thresholds, and 5-dimension radar scoring."""
    preferred_skills = preferred_skills or []
    cleaned_resume_lower = resume_text.lower()

    matched: list[str] = []
    transferable: list[str] = []
    missing: list[str] = []

    chunks = _chunk_resume_text(resume_text, sections)
    model = get_embedding_model()

    used_transformer = False
    if model is not None and chunks:
        try:
            import torch

            # Memory-safe inference: wrap in torch.no_grad()
            with torch.no_grad():
                skill_embeddings = model.encode(required_skills, normalize_embeddings=True)
                chunk_embeddings = model.encode(chunks, normalize_embeddings=True)
                similarity_matrix = np.dot(skill_embeddings, chunk_embeddings.T)

            for idx, skill in enumerate(required_skills):
                max_sim = float(np.max(similarity_matrix[idx])) if similarity_matrix.size > 0 else 0.0

                # Exact keyword override: If verbatim skill exists in resume, ensure minimum 0.88 match
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

            used_transformer = True
        except (MemoryError, Exception) as e:
            logger.warning("Transformer inference error (%s); falling back to lightweight similarity.", e)
            used_transformer = False

    if not used_transformer:
        # Lightweight memory fallback: Fast token-overlap and TF-IDF calculation (<60 MB RAM)
        sim_scores = _compute_lightweight_similarities(required_skills, chunks, resume_text)
        for skill in required_skills:
            sim = sim_scores.get(skill, 0.0)
            if sim >= 0.70:
                matched.append(skill)
            elif sim >= 0.50:
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
