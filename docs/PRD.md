# CareerMetricX — Product Requirements Document (PRD)

**Project Title:** CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform  
**Tagline:** Measure your skills. Prove your readiness.  
**Academic Context:** MCA 3rd-Semester Project (Portfolio-Grade Production Architecture)  
**Version:** 1.0.0-draft  
**Status:** Approved Architecture Baseline  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Industry Dilemma
Contemporary talent acquisition software relies heavily on traditional Applicant Tracking Systems (ATS) that perform lexical keyword matching against resumes. This creates acute failure modes on both sides of the hiring equation:

1. **Keyword Stuffing & Inflation:** Candidates add long comma-separated lists of tools, libraries, and frameworks into their "Skills" section without having ever applied them in production or academic projects.
2. **False Positives:** A candidate who pastes "Kubernetes, Apache Kafka, Distributed Systems" without real experience receives a superficial "95% ATS Match".
3. **False Negatives:** Qualified candidates who describe transferable engineering capabilities using distinct terminology are filtered out by rigid string matchers.
4. **Interview Disconnect:** Technical interviewers waste valuable interview loops discovering that a candidate cannot answer basic architectural questions about technologies claimed prominently on their resume.

### 1.2 The Innovation of CareerMetricX
**CareerMetricX** transforms career readiness from keyword matching into an **evidence-grounded capability mapping and interview verification loop**.

Instead of accepting resume claims at face value or generating generic AI chatbot feedback, CareerMetricX enforces the core axiom:

$$\text{CLAIM} \longrightarrow \text{EVIDENCE} \longrightarrow \text{INTERVIEW} \longrightarrow \text{IMPROVEMENT}$$

- **Claim Extraction:** Parses atomic assertions of competency from candidate resumes.
- **Evidence Provenance:** Inspects projects, work experiences, certifications, and source context to classify claims as `PROVEN`, `TRANSFERABLE`, `MENTIONED`, or `MISSING`.
- **Explainable Matching:** Compares candidate capabilities against structured Job Description (JD) requirements using exact, alias, ontological, and semantic similarity techniques.
- **Defensibility Verification:** Generates targeted interview inquiries directly grounded in the candidate's projects and identified capability gaps, evaluating whether the candidate can articulate and defend their assertions.
- **Actionable Remediation:** Prescribes concrete proof artifacts (e.g., repository setups, system designs) rather than generic reading lists.

---

## 2. Target Personas & User Stories

### 2.1 Personas

#### Primary Persona: The Candidate / Student (MCA / Engineering Graduate)
- **Goal:** Understand genuine readiness for specific target software roles (e.g., Backend Engineer, Full-Stack Developer, Data Engineer), identify verifiable gaps, and practice defending resume claims under realistic technical interview questioning.
- **Pain Point:** Frustrated by black-box ATS percentages and generic mock interview tools that don't know the specifics of their actual projects.

#### Secondary Persona: System Administrator
- **Goal:** Maintain system health, curate the canonical skill taxonomy, manage user accounts, and review audit/telemetry logs.
- **Pain Point:** Lack of visibility into automated classification biases and runaway external API token costs.

#### Future Extension Persona: Placement Cell Officer / Recruiter
- **Goal:** Batch-evaluate candidate readiness cohorts, inspect evidence distribution across batches, and identify systemic curriculum gaps.
- **Architectural Requirement:** Architecture and database schema must support tenant-aware cohort partitioning without core refactoring.

---

## 3. Non-Negotiable Engineering Principles

1. **No Fake Functionality:** Every button, calculation, and workflow must execute real deterministic or AI-backed logic.
2. **No Hard-Coded Analysis Results:** Scores, evidence states, and questions must be computed dynamically from genuine inputs.
3. **No Fabricated Achievements:** The system will never hallucinate metrics or achievements not present in the user's uploaded materials.
4. **Skills Listed $\neq$ Demonstrated Experience:** A skill merely declared in a "Skills" list is strictly categorized as `MENTIONED` (low confidence), never `PROVEN`.
5. **Strict Evidence Provenance:** Every evidence item must preserve its source document, page/section, and exact snippet text.
6. **Explainable Classifications:** Every match score, gap, and claim verdict must present transparent reasoning to the user.
7. **AI as an Augmentation, Not a Crutch:** Deterministic parsing, regular expressions, and ontology graphs handle structure; LLMs are utilized for semantic summarization and nuanced conversational probing.
8. **Pluggable AI Interface:** External LLM APIs must sit behind an abstract interface with a zero-cost deterministic fallback for offline development and CI.
9. **Zero-Secret Leakage:** Strictly no credentials, API keys, or private tokens committed to source control.
10. **Test-Driven Verification:** Core logic, edge cases, and evidence boundaries must be covered by automated test suites.

---

## 4. End-to-End Functional Requirements

### 4.1 Module 1: Identity & Profile Management
- **FR-1.1:** User registration with email validation, password hashing (Argon2 / BCrypt), and JWT token pair issuance (access + refresh).
- **FR-1.2:** Profile creation with career objectives, educational background, and preferred technical tracks.
- **FR-1.3:** Role-Based Access Control (RBAC) supporting `CANDIDATE`, `ADMIN`, and future `PLACEMENT_OFFICER`.

### 4.2 Module 2: Resume Ingestion & Intelligence
- **FR-2.1:** Support document ingestion for `.pdf`, `.docx`, and `.txt` up to 10MB.
- **FR-2.2:** Robust section extraction (Contact, Summary, Education, Experience, Projects, Skills, Certifications, Publications).
- **FR-2.3:** Sentence-level entity recognition extracting technologies, tools, metrics, timeframes, and responsibilities.
- **FR-2.4:** Extraction of verifiable external links (GitHub, LinkedIn, live demo URLs).

### 4.3 Module 3: Job Description (JD) Intelligence
- **FR-3.1:** Input via plain text paste or document upload.
- **FR-3.2:** Automated breakdown of requirements into:
  - Role metadata (Title, Department, Seniority).
  - Must-Have Technical Skills (Hard requirements).
  - Nice-to-Have / Preferred Skills.
  - Experience / Education Thresholds.
  - Architectural / Domain Responsibilities.
  - Soft Skills / Collaboration Competencies.
- **FR-3.3:** Extraction of source context and confidence rating per requirement.

### 4.4 Module 4: Skill Ontology & Normalization
- **FR-4.1:** Canonical mapping of surface variations (e.g., `React.js`, `ReactJS`, `react` $\to$ `React`).
- **FR-4.2:** Hierarchical taxonomy linking frameworks to underlying languages (e.g., `FastAPI` $\to$ `Python` $\to$ `Backend Development`).
- **FR-4.3:** Relationship awareness (Parent/Child, Complementary, Sibling/Alternative like `PostgreSQL` $\leftrightarrow$ `MySQL`).

### 4.5 Module 5: Evidence & Capability Engine
- **FR-5.1:** Classification of every candidate capability into one of four states:
  - **`PROVEN`**: Supported by concrete project implementation, employment metrics, or verified repository artifact.
  - **`TRANSFERABLE`**: The candidate lacks the exact tool but exhibits deep proficiency in a direct sibling or foundational capability (e.g., expert in Django evaluated for FastAPI).
  - **`MENTIONED`**: Claimed in a summary or keyword list without verifiable project narrative.
  - **`MISSING`**: Zero presence found across all submitted documents.
- **FR-5.2:** Claim verification engine flagging quantitative statements that lack contextual backing.

### 4.6 Module 6: Explainable Matching Engine
- **FR-6.1:** Multidimensional capability scoring:
  - **Requirement Coverage Ratio ($R_{cov}$):** Fraction of mandatory JD requirements addressed.
  - **Evidence Depth Index ($E_{depth}$):** Weighted score reflecting `PROVEN` vs `MENTIONED` backing.
  - **Transferability Factor ($T_{factor}$):** Credit awarded for adjacent proficiencies.
  - **Interview Defensibility Score ($D_{score}$):** Candidate's track record answering technical checkpoints.
- **FR-6.2:** Comprehensive Gap Analysis highlighting critical blockers vs easily acquired skills.

### 4.7 Module 7: Personalized Preparation Engine
- **FR-7.1:** Algorithmic generation of targeted remediation tasks for each identified gap.
- **FR-7.2:** Each task requires:
  - Rationale (Why this skill matters for the target role).
  - Action item (Concrete engineering implementation).
  - Proof Artifact requirement (e.g., PR, Dockerfile, benchmark script).
  - Technical Checkpoint (Core conceptual questions candidate must be able to articulate).

### 4.8 Module 8: Interview Intelligence & Simulation
- **FR-8.1:** Simulation tracks:
  - Technical Architecture & Deep Dive.
  - Resume Claim Verification (challenging specific resume assertions).
  - Gap Challenge (evaluating adaptability on missing technologies).
  - Behavioral / HR.
- **FR-8.2:** Dynamic question synthesis utilizing project context (e.g., "In project X, you mentioned reducing latency by 40% using Redis. How did you handle cache invalidation?").
- **FR-8.3:** Answer Evaluation across 6 dimensions:
  - Relevance & Directness.
  - Technical Accuracy.
  - Depth & Completeness.
  - Architectural Specificity.
  - Clarity & Articulation.
  - Resume Consistency (detecting contradictions with submitted claims).

### 4.9 Module 9: Optional GitHub Verification
- **FR-9.1:** User-consented connection to public GitHub repositories.
- **FR-9.2:** Inspection of repo metadata: primary languages, commit history recency, presence of CI configurations, test suites, and documentation.
- **FR-9.3:** Strictly treats repository data as supplementary corroboration, never as sole proof of individual mastery.

---

## 5. Non-Functional Requirements (NFRs)

| Metric | Target Standard | Rationale |
| :--- | :--- | :--- |
| **Response Latency (Deterministic)** | $< 350\text{ ms}$ for parsing & scoring | High UI responsiveness during analysis |
| **Response Latency (AI-Assisted)** | $< 4.0\text{ s}$ with streaming feedback | Prevents UI freezing during interview interaction |
| **Availability** | 99.5% uptime target | Reliable academic evaluation and student access |
| **Security** | Zero hard-coded credentials; Argon2/Bcrypt | OWASP ASVS Level 1 compliance |
| **Accessibility** | WCAG 2.1 Level AA compliant UI | Inclusive design standard |
| **Data Privacy** | Full user account and document purge on demand | GDPR/DPDP alignment |

---

## 6. Project Scope & Phased Milestones

- **In Scope (Academic Release):** Monorepo architecture, FastAPI backend, React/Vite/Tailwind frontend, MongoDB persistence, PyMuPDF parsing, canonical skill taxonomy, 4-tier evidence engine, multidimensional scoring, interview simulator with deterministic fallback, Docker Compose, automated CI test suite.
- **Out of Scope (Current Release):** Audio/Video speech recognition streams (handled via text input in MVP), paid cloud ATS integrations (Workday, Greenhouse API sync), enterprise multi-tenant billing.
