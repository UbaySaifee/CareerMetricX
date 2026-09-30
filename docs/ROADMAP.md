# CareerMetricX — 11-Phase Implementation Roadmap

**Project Title:** CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform  
**Target Delivery:** High-Fidelity Portfolio & Academic Minor Project  
**Current Milestone:** Phase 1 (Foundation Baseline)  
**Version:** 1.0.0  

---

## 1. Roadmap Architecture & Execution Philosophy

Development proceeds through **strictly gated sequential phases**. Each phase must produce demonstrable, tested artifacts with zero fake data, no unverified claims, and comprehensive test coverage before advancing to the next phase.

```mermaid
gantt
    title CareerMetricX Phased Execution Plan
    dateFormat  YYYY-MM-DD
    section Baseline
    Phase 1: Foundation, Repo, CI, Docker       :active, 2026-09-27, 2d
    section Core Ingestion
    Phase 2: Authentication & Profile          :2026-09-29, 2d
    Phase 3: Resume Intelligence Engine        :2026-10-01, 3d
    Phase 4: Job Description Intelligence     :2026-10-04, 2d
    section Intelligence
    Phase 5: Evidence Extraction & Provenance  :2026-10-06, 3d
    Phase 6: Multidimensional Analysis & Gaps  :2026-10-09, 3d
    section Readiness & Practice
    Phase 7: Personalized Preparation Engine   :2026-10-12, 2d
    Phase 8: Interview Simulation & Evaluation :2026-10-14, 4d
    section Extensions & Production
    Phase 9: GitHub Corroboration Engine       :2026-10-18, 2d
    Phase 10: Hardening, Observability, Deploy :2026-10-20, 2d
    Phase 11: Academic Documentation & Polish  :2026-10-22, 2d
```

---

## 2. Phase-by-Phase Deliverables & Acceptance Criteria

### Phase 1: Foundation, Repository, CI & Docker (Current Phase)
- **Goal:** Establish clean monorepo architecture, Docker orchestration, CI workflows, and documentation baseline.
- **Deliverables:**
  - Standardized monorepo (`frontend/`, `backend/`, `docs/`, `tests/`, `infra/`, `scripts/`, `.github/`).
  - Architecture documentation suite (`PRD.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `AI_ENGINE.md`, `SECURITY.md`, `TEST_PLAN.md`, `DEPLOYMENT.md`, `ROADMAP.md`, `VIBE_CODING_GUIDE.md`).
  - Backend bootstrap with FastAPI, configuration management, health endpoint, and unit tests.
  - Frontend bootstrap with Vite, React 19, TypeScript, and Tailwind CSS.
  - Multi-stage Dockerfiles and `docker-compose.yml`.
  - GitHub Actions CI pipeline running lint, tests, and build.
- **Exit Criteria:** Backend and frontend build cleanly; health check returns 200 OK; CI passes without external mocks.

### Phase 2: Authentication, RBAC & Profile Management
- **Goal:** Secure user identity, role-based authorization, and persistent candidate profiles.
- **Deliverables:**
  - Password hashing via Argon2id.
  - JWT Access & Refresh token rotation mechanics.
  - User model & Profile schemas in MongoDB.
  - `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` endpoints.
  - Candidate profile editor in React frontend.
- **Exit Criteria:** Automated tests verifying registration, login, token expiry, and unauthorized request rejection.

### Phase 3: Resume Intelligence Engine
- **Goal:** Parse candidate documents and construct structured factual representations.
- **Deliverables:**
  - Multi-format ingestion (`.pdf`, `.docx`, `.txt`) using PyMuPDF and python-docx.
  - Section boundary detection (Summary, Education, Experience, Projects, Skills, Links).
  - Sentence-level entity and metric extraction.
  - Upload security validations (magic bytes, 10MB limit).
- **Exit Criteria:** Parsing fixtures extracting known section boundaries and entities from sample resumes.

### Phase 4: Job Description (JD) Intelligence Engine
- **Goal:** Ingest and decompose target job descriptions into structured requirements.
- **Deliverables:**
  - Plaintext and document ingestion for JDs.
  - Extraction of Must-Have Skills, Preferred Skills, Experience thresholds, and Key Responsibilities.
  - Skill normalization against canonical ontology.
- **Exit Criteria:** JD parser tests verifying mandatory vs preferred classification accuracy.

### Phase 5: Skill Ontology & Evidence Provenance Engine
- **Goal:** Differentiate between claims and substantiated capabilities.
- **Deliverables:**
  - Canonical skill dictionary with aliases, synonyms, and parent/child hierarchies.
  - 4-tier classification algorithm: `PROVEN`, `TRANSFERABLE`, `MENTIONED`, `MISSING`.
  - Strict rule enforcement: Skills listed in Skills section $\implies$ `MENTIONED`.
  - Provenance tagging (source document, section, verbatim snippet, confidence).
- **Exit Criteria:** Verification fixtures confirming the 4 evidence states.

### Phase 6: Multidimensional Analysis & Gap Detection
- **Goal:** Score candidate fit with transparent, explainable metrics.
- **Deliverables:**
  - Mathematical computation of $R_{cov}$, $E_{depth}$, $T_{factor}$, $D_{score}$, and composite CRI.
  - Critical vs moderate gap categorization.
  - Visual readiness radar and evidence map in React frontend.
- **Exit Criteria:** Scoring formula unit tests matching manual calculation benchmarks.

### Phase 7: Personalized Preparation Engine
- **Goal:** Transform capability gaps into actionable engineering remediation tasks.
- **Deliverables:**
  - Algorithmic generation of role-specific tasks, proof artifacts, and interview checkpoints.
  - Interactive preparation checklist with proof submission and tracking.
- **Exit Criteria:** Tests confirming every identified gap receives a structured remediation task.

### Phase 8: Interview Intelligence & Simulation Engine
- **Goal:** Test candidate defensibility through grounded technical questioning.
- **Deliverables:**
  - Multi-mode interview simulator: Technical Deep Dive, Resume Claim Verification, Gap Challenge.
  - Question synthesis grounded in candidate project snippets.
  - Answer evaluation across 6 dimensions with feedback and advisory indicators.
  - Deterministic fallback provider for zero-cost operation.
- **Exit Criteria:** End-to-end interview simulation runs successfully in deterministic mode.

### Phase 9: GitHub Evidence Corroboration (Optional Module)
- **Goal:** Provide supplemental corroboration from public candidate repositories.
- **Deliverables:**
  - Explicit candidate repository selection.
  - Metadata inspection (languages, tests, dockerfiles, commit recency).
  - Strict guardrail: Repo data corroborates, never solely proves mastery.
- **Exit Criteria:** Corroboration tests demonstrating adjusted evidence confidence.

### Phase 10: Security Hardening, Observability & Cloud Deployment
- **Goal:** Production-ready resilience and telemetry.
- **Deliverables:**
  - Rate limiting with SlowAPI.
  - Audit logging for administrative actions.
  - Sentry / Datadog integration points.
  - Production Docker Compose and deployment manifests.
- **Exit Criteria:** OWASP vulnerability scan clean; rate limiter throttles excessive requests.

### Phase 11: Academic Viva Documentation & UI Polish
- **Goal:** Complete project report, presentation materials, and responsive visual polish.
- **Deliverables:**
  - Final MCA Project Report and Viva Defense Guide.
  - Polished responsive UI with dark/light themes, animations, and zero broken states.
- **Exit Criteria:** Ready for flawless demonstration before academic review panel.
