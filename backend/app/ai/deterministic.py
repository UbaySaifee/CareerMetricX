"""Deterministic Rule-Based Intelligence Provider for offline execution, testing, and fallbacks."""

import re
from typing import Any

from app.ai.base import BaseAIProvider
from app.schemas.analysis import InterviewQuestion


COMMON_ACTION_VERBS = {
    "architected", "engineered", "developed", "built", "designed", "implemented",
    "spearheaded", "created", "maintained", "optimized", "scaled", "integrated",
    "configured", "deployed", "migrated", "delivered", "achieved", "authored",
    "established", "refactored", "automated", "managed", "constructed", "orchestrated",
    "improved", "reduced", "increased", "enhanced", "resolved", "conducted", "led",
    "spearheading", "building", "developing", "designing", "implementing",
    "in", "using", "with", "for", "by", "to", "from", "at", "on", "across", "the", "a", "an",
    "can", "senior", "junior", "lead", "software", "engineer", "developer"
}

KNOWN_TECH_KEYWORDS = [
    "Node.js", "Express", "MongoDB", "FastAPI", "PostgreSQL", "Docker", "Kubernetes",
    "Kafka", "Redis", "RabbitMQ", "Django", "Flask", "React", "Next.js", "TypeScript",
    "JavaScript", "Python", "Golang", "Go", "Rust", "Java", "C++", "C#", ".NET",
    "GraphQL", "REST", "gRPC", "AWS", "GCP", "Azure", "Terraform", "Elasticsearch",
    "Cassandra", "MySQL", "DynamoDB", "Celery", "Airflow", "PyTorch", "TensorFlow", "Spark"
]


def extract_technology_from_claim(claim: str) -> str | None:
    """Extract actual technology keyword from claim text, skipping leading action verbs."""
    # 1. Match known technical stacks (case-insensitive boundary match)
    for tech in KNOWN_TECH_KEYWORDS:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, claim, re.IGNORECASE):
            return tech

    # 2. Scan capitalized technical tokens that are not action verbs or stopwords
    tokens = re.findall(r"\b[A-Z][a-zA-Z0-9+#.-]+\b", claim)
    for token in tokens:
        if token.lower() not in COMMON_ACTION_VERBS and len(token) > 1:
            return token

    return None


class DeterministicFallbackProvider(BaseAIProvider):
    """Zero-cost, fully reproducible deterministic intelligence engine."""

    @property
    def provider_name(self) -> str:
        return "deterministic-rule-engine"

    async def extract_semantic_requirements(self, text: str) -> dict[str, Any]:
        """Rule-based extraction of requirements from JD text."""
        lowered = text.lower()

        # Common skill keywords
        known_skills = [
            "python", "fastapi", "django", "flask", "docker", "kubernetes",
            "postgresql", "mysql", "mongodb", "redis", "kafka", "aws",
            "react", "typescript", "javascript", "graphql", "rest", "ci/cd", "git"
        ]

        detected = [skill.title() for skill in known_skills if re.search(r'\b' + re.escape(skill) + r'\b', lowered)]
        must_haves = detected[:max(1, len(detected) // 2)]
        preferred = detected[len(must_haves):]

        # Seniority heuristic
        seniority = "Mid-Level"
        if any(w in lowered for w in ["lead", "principal", "architect", "senior", "5+ years", "7+ years"]):
            seniority = "Senior"
        elif any(w in lowered for w in ["junior", "intern", "graduate", "fresher", "entry"]):
            seniority = "Junior / Entry-Level"

        return {
            "seniority_level": seniority,
            "must_have_skills": must_haves,
            "preferred_skills": preferred,
            "responsibilities": [
                line.strip("-•* ").capitalize()
                for line in text.split("\n")
                if any(k in line.lower() for k in ["build", "develop", "design", "maintain", "architect"])
            ][:5],
            "is_deterministic": True
        }

    async def generate_interview_questions(
        self,
        resume_context: dict[str, Any],
        job_context: dict[str, Any],
        gaps: list[dict[str, Any]],
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Synthesize questions grounded in candidate projects and identified gaps."""
        questions: list[dict[str, Any]] = []
        projects = resume_context.get("projects", [])

        # Grounded in projects
        for idx, proj in enumerate(projects):
            name = proj.get("name", f"Project {idx+1}")
            techs = ", ".join(proj.get("technologies", ["core engineering"]))
            questions.append({
                "question_id": f"det-q-proj-{idx+1}",
                "type": "PROJECT_DEEP_DIVE",
                "targeted_skill": techs.split(",")[0] if techs else "Architecture",
                "question_text": f"In your project '{name}', you utilized {techs}. What were the primary architectural trade-offs you faced, and how did you validate system performance under load?",
                "evaluation_criteria": ["Architectural rationale", "Concrete trade-off analysis", "Consistency with claims"]
            })
            if len(questions) >= limit:
                break

        # Grounded in gaps
        for idx, gap in enumerate(gaps):
            if len(questions) >= limit:
                break
            skill = gap.get("skill", "Required Technology")
            questions.append({
                "question_id": f"det-q-gap-{idx+1}",
                "type": "GAP_CHALLENGE",
                "targeted_skill": skill,
                "question_text": f"The target role requires {skill}, which was not prominently demonstrated in your recent projects. How would you apply your existing engineering experience to ramp up and deliver production work in {skill}?",
                "evaluation_criteria": ["Transferable knowledge", "Learning agility", "Foundational understanding"]
            })

        # Baseline fallback question if empty
        if not questions:
            questions.append({
                "question_id": "det-q-default-1",
                "type": "TECHNICAL_ARCHITECTURE",
                "targeted_skill": "System Design",
                "question_text": "Walk through the architectural design of the most complex backend service you have engineered. How did you structure data persistence and handle network failures?",
                "evaluation_criteria": ["Clarity", "System boundary comprehension", "Fault tolerance"]
            })

        return questions[:limit]

    async def evaluate_interview_answer(
        self,
        question: dict[str, Any],
        candidate_answer: str,
        claimed_context: str
    ) -> dict[str, Any]:
        """Heuristic answer evaluation across the 6 dimensions."""
        ans_len = len(candidate_answer.strip().split())
        lowered = candidate_answer.lower()

        # Scoring heuristics based on length, specificity, and technical vocabulary
        relevance = 8.0 if ans_len >= 30 else (5.0 if ans_len >= 10 else 3.0)
        tech_words = ["async", "database", "latency", "scale", "cache", "query", "thread", "api", "docker", "pipeline"]
        tech_count = sum(1 for word in tech_words if word in lowered)

        tech_score = min(10.0, 5.0 + (tech_count * 1.0))
        completeness = min(10.0, 4.0 + (ans_len / 20.0))
        specificity = min(10.0, 5.0 + (1.5 if any(char.isdigit() for char in candidate_answer) else 0.0) + (tech_count * 0.5))
        clarity = 8.0 if ans_len >= 20 else 6.0
        resume_consistency = 8.5

        return {
            "scores": {
                "relevance": round(relevance, 1),
                "technical_correctness": round(tech_score, 1),
                "completeness": round(completeness, 1),
                "specificity": round(specificity, 1),
                "clarity": round(clarity, 1),
                "resume_consistency": round(resume_consistency, 1)
            },
            "strengths": [
                "Answer directly addresses the stated problem statement.",
                f"Identified {tech_count} relevant engineering domain concepts."
            ],
            "missing_points": [
                "Could be enhanced by detailing specific monitoring/telemetry metrics.",
                "Consider articulating edge cases and error handling paths."
            ],
            "improvement_suggestion": "Quantify outcomes where possible and explain failure recovery mechanisms.",
            "is_advisory": True,
            "provider": self.provider_name
        }

    async def verify_claims(
        self,
        project_claims: list[str],
        resume_text: str,
    ) -> list[str]:
        """Audit project claims and detect exaggerated metrics, unbacked speedups, or vague assertions."""
        flags: list[str] = []
        full_text_lower = resume_text.lower()

        for claim in project_claims:
            claim_lower = claim.lower()

            # 1. Multipliers (e.g. 10x, 100x, 50x)
            multiplier_match = re.search(r"\b(\d{2,}|[5-9])x\b", claim_lower)
            if multiplier_match:
                mult_val = multiplier_match.group(0)
                # Check if baseline profiling / benchmarking / caching was mentioned
                if not any(k in claim_lower or k in full_text_lower for k in ["profil", "benchmark", "redis", "cache", "index", "asyn"]):
                    flags.append(
                        f"Unsubstantiated speedup metric '{mult_val}' in claim: \"{claim[:90]}...\" — lacks documented baseline benchmarks or profiling tools."
                    )

            # 2. Extreme availability or test coverage (e.g. 99.999% or 100% test coverage)
            if re.search(r"\b(?:99\.999%|100% (?:coverage|uptime|test))\b", claim_lower):
                flags.append(
                    f"Extreme availability/coverage claim in \"{claim[:90]}...\" requires verifiable telemetry logs or CI pipeline reports."
                )

            # 3. Vague unquantified assertions
            vague_match = re.search(r"\b(drastically improved|infinitely scalable|massive performance boost|huge improvement)\b", claim_lower)
            if vague_match:
                flags.append(
                    f"Vague assertion '{vague_match.group(0)}' in \"{claim[:90]}...\" — recommend replacing with concrete latency (ms) or throughput (RPS) metrics."
                )

            # 4. Enormous scale claims without architectural backing
            scale_match = re.search(r"\b(millions of users|billions of requests|10m\+ requests)\b", claim_lower)
            if scale_match:
                if not any(k in full_text_lower for k in ["kafka", "kubernetes", "k8s", "shard", "load balancer", "distributed", "cluster"]):
                    flags.append(
                        f"High-scale assertion '{scale_match.group(0)}' in \"{claim[:90]}...\" is not backed by distributed infrastructure in the tech stack."
                    )

        if not flags:
            flags.append("All analyzed project assertions adhere to realistic software engineering constraints.")

        # Deduplicate while preserving order
        unique_flags = list(dict.fromkeys(flags))
        return unique_flags

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
        questions: list[InterviewQuestion] = []
        difficulty_tier = "Senior" if "Senior" in experience_level or "Lead" in experience_level else ("Junior" if "Junior" in experience_level else "Mid")

        # 1. Questions challenging specific project claims
        for claim in claims[:3]:
            short_claim = claim[:80] + "..." if len(claim) > 80 else claim
            tech = extract_technology_from_claim(claim)
            tech_ref = f" using {tech}" if tech else ""

            questions.append(
                InterviewQuestion(
                    question=f"In your project narrative, you stated: \"{short_claim}\". Can you explain the underlying architecture{tech_ref}, what baseline you measured against, and what design trade-offs you evaluated?",
                    target_claim=claim,
                    rationale="Evaluates engineering rigor, baseline profiling practices, and empirical defensibility during viva defense.",
                    difficulty=difficulty_tier,
                )
            )
            if len(questions) >= limit:
                break

        # 2. Questions probing identified skill gaps
        for gap in missing_skills:
            if len(questions) >= limit:
                break
            questions.append(
                InterviewQuestion(
                    question=f"The {role} role requires production proficiency in {gap}, which is not evidenced in your current projects. How would you design a production-ready service utilizing {gap}, and how does your existing technical experience bridge this gap?",
                    target_claim=f"Requirement Gap: {gap}",
                    rationale=f"Evaluates technical adaptability and foundational transferability to meet the mandatory requirement for {gap}.",
                    difficulty=difficulty_tier,
                )
            )

        # 3. Fallback technical questions if list is below limit
        if len(questions) < limit:
            fallback_topics = required_skills or ["FastAPI", "MongoDB", "Distributed Systems"]
            for topic in fallback_topics:
                if len(questions) >= limit:
                    break
                questions.append(
                    InterviewQuestion(
                        question=f"How do you approach database transaction management, connection pooling, and connection leak prevention in high-concurrency {topic} environments?",
                        target_claim=f"Core Competency: {topic}",
                        rationale=f"Probes deep system design and data persistence failure handling in {topic}.",
                        difficulty=difficulty_tier,
                    )
                )

        return questions[:limit]

    async def generate_prep_plan(
        self,
        missing_skills: list[str],
        role: str,
        days: int = 7,
    ) -> list[str]:
        """Generate a structured day-by-day preparation checklist targeting identified skill gaps."""
        primary_gap = missing_skills[0] if missing_skills else "Core Architecture"
        secondary_gap = missing_skills[1] if len(missing_skills) > 1 else (missing_skills[0] if missing_skills else "System Design")
        all_gaps_str = ", ".join(missing_skills[:3]) if missing_skills else f"{role} Core Patterns"

        plan = [
            f"Day 1 — Architectural Foundations: Study official documentation and core design paradigms for {all_gaps_str}.",
            f"Day 2 — Containerized Sandbox Setup: Configure a local Dockerized sandbox environment running {primary_gap} with healthchecks.",
            f"Day 3 — Prototype Implementation: Construct a minimal end-to-end service demonstrating {primary_gap} and {secondary_gap}.",
            f"Day 4 — Resilience & Error Handling: Implement structured logging, circuit breakers, and explicit exception boundaries.",
            f"Day 5 — Automated Test Suites: Write unit and integration test fixtures using pytest, ensuring regression resistance.",
            f"Day 6 — Performance & Profiling: Benchmark endpoint latencies under simulated concurrent load; tune queries and connection pools.",
            f"Day 7 — Viva Defense & Artifact Documentation: Produce an Architecture Decision Record (ADR) and rehearse verbal defense of design trade-offs.",
        ]
        return plan[:days]

    async def generate_star_recommendations(
        self,
        transferable_skills: list[str],
        role: str,
        resume_text: str = "",
    ) -> list[dict[str, str]]:
        """Generate actionable STAR-format bullet point recommendations for transferable skills."""
        recommendations: list[dict[str, str]] = []

        for skill in transferable_skills:
            skill_lower = skill.lower()

            # Message Brokers / Event Streaming
            if any(term in skill_lower for term in ["kafka", "rabbitmq", "pubsub", "sqs", "event"]):
                current_gap = (
                    f"Demonstrates asynchronous processing foundations but lacks direct {skill} cluster operational evidence in current projects."
                )
                suggested_bullet = (
                    f"Architected asynchronous event-driven messaging pipelines utilizing {skill}: implemented consumer group partitioning, "
                    f"schema registry validation, and dead-letter queues (DLQ), reducing inter-service request latency by 42% across 15k+ events/sec."
                )
            # Caching & In-Memory Storage
            elif any(term in skill_lower for term in ["redis", "memcached"]):
                current_gap = (
                    f"Strong database query optimization background; reframe in-memory caching ({skill}) to demonstrate latency reduction."
                )
                suggested_bullet = (
                    f"Engineered distributed caching and session state tier leveraging {skill} with cache-aside patterns and TTL expiration policies, "
                    f"slashing primary database query contention and lowering P99 endpoint response time from 180ms to 24ms."
                )
            # Container Orchestration & Cloud DevOps
            elif any(term in skill_lower for term in ["kubernetes", "k8s", "docker", "terraform", "helm"]):
                current_gap = (
                    f"Demonstrates containerization knowledge; elevate to declarative container orchestration ({skill}) for {role} role."
                )
                suggested_bullet = (
                    f"Standardized container deployment lifecycle by authoring declarative {skill} manifests and Helm charts: configured horizontal "
                    f"pod autoscaling (HPA) and liveness/readiness probes, achieving 99.95% service availability under spiky production traffic."
                )
            # Cloud Infrastructure
            elif any(term in skill_lower for term in ["aws", "gcp", "azure", "cloud"]):
                current_gap = (
                    f"Solid backend system architecture experience; reframe on-prem/local infrastructure to cloud-native ({skill}) paradigms."
                )
                suggested_bullet = (
                    f"Provisioned and managed cloud-native microservices infrastructure on {skill}: utilized managed database instances and serverless triggers, "
                    f"automating CI/CD deployment pipelines and reducing monthly operational compute expenses by 28%."
                )
            # Relational & NoSQL Databases
            elif any(term in skill_lower for term in ["postgres", "postgresql", "mysql", "mongodb", "cassandra", "elasticsearch"]):
                current_gap = (
                    f"General persistence layer exposure demonstrated; highlights deep {skill} schema design, query planning, and indexing."
                )
                suggested_bullet = (
                    f"Engineered high-performance data persistence layer in {skill}: designed normalized schemas, compound B-tree indexes, "
                    f"and asynchronous connection pooling, eliminating full table scans and accelerating heavy aggregation queries by 3.8x."
                )
            # Modern Web & Backend Frameworks
            elif any(term in skill_lower for term in ["fastapi", "django", "flask", "express", "react", "next", "graphql"]):
                current_gap = (
                    f"Core programming proficiency evidenced; reframe adjacent API development into production {skill} patterns."
                )
                suggested_bullet = (
                    f"Engineered high-concurrency microservices platform in {skill}: implemented strict schema serialization, JWT authentication, "
                    f"and asynchronous I/O handlers, scaling throughput to 8,500 RPS while cutting memory footprint by 35%."
                )
            # Generic / Universal STAR Template
            else:
                current_gap = (
                    f"Adjacent transferable requirement identified for {role}; candidate can bridge foundational skills with applied {skill} outcomes."
                )
                suggested_bullet = (
                    f"Spearheaded technical adoption of {skill} to address core {role} system requirements: designed robust interfaces, "
                    f"conducted benchmark stress tests against legacy architecture, and successfully deployed production modules with zero regression bugs."
                )

            recommendations.append({
                "skill": skill,
                "current_gap": current_gap,
                "suggested_bullet": suggested_bullet,
            })

        return recommendations

