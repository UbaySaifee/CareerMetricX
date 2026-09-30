# CareerMetricX — System Architecture Document

**System Title:** CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform  
**Architecture Pattern:** Layered Modular Monolith (Clean Architecture)  
**Version:** 1.0.0  

---

## 1. Architectural Vision & Topology

CareerMetricX is designed as a **production-grade, layered modular monolith**. It combines high developer velocity, clear operational boundaries, and zero unnecessary microservice overhead while preserving strict separation of concerns.

### 1.1 High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Client Layer ["Client Tier (Browser)"]
        SPA["React 19 + TypeScript + Vite"]
        Tailwind["Tailwind CSS + Headless UI"]
        Recharts["Recharts Visualizations"]
    end

    subgraph Gateway ["Reverse Proxy & Ingress"]
        Nginx["Nginx Ingress / Docker Gateway"]
    end

    subgraph App Layer ["Backend Application Tier (FastAPI Modular Monolith)"]
        API["FastAPI REST Routing (/api/v1)"]
        AuthMiddleware["JWT Authentication & RBAC Guard"]
        
        subgraph Services ["Domain Service Layer"]
            AuthSvc["Auth & User Service"]
            ResumeSvc["Resume Processing Service"]
            JDSvc["Job Description Service"]
            OntologySvc["Skill Ontology & Normalizer"]
            EvidenceSvc["Evidence Classification Engine"]
            MatchingSvc["Multidimensional Matcher"]
            PrepSvc["Personalized Prep Generator"]
            InterviewSvc["Interview & Evaluation Engine"]
            AuditSvc["Audit & Telemetry Service"]
        end

        subgraph CoreAI ["AI & Intelligence Tier"]
            AIFactory["AI Provider Interface"]
            DetProvider["Deterministic Fallback Engine"]
            LLMProvider["OpenAI-Compatible LLM Client"]
        end

        subgraph Repositories ["Data Access Layer (Repository Pattern)"]
            UserRepo["User & Profile Repo"]
            ResumeRepo["Resume & Version Repo"]
            JDRepo["Job Requirement Repo"]
            EvidenceRepo["Evidence Item Repo"]
            AnalysisRepo["Analysis & Gap Repo"]
            InterviewRepo["Interview Session Repo"]
        end
    end

    subgraph Data Layer ["Persistence Tier"]
        MongoDB[(MongoDB 7.x Database)]
        FileStore[("File Storage / Local Volume")]
    end

    SPA -->|HTTPS / REST API| Nginx
    Nginx -->|Proxy Pass| API
    API --> AuthMiddleware
    AuthMiddleware --> Services
    Services --> AIFactory
    AIFactory --> DetProvider
    AIFactory --> LLMProvider
    Services --> Repositories
    Repositories --> MongoDB
    ResumeSvc --> FileStore
```

---

## 2. Layered Component Architecture

The backend strictly enforces unidirectional dependencies following Clean Architecture principles:

$$\text{API Routes (Presentation)} \longrightarrow \text{Schemas (DTOs)} \longrightarrow \text{Domain Services} \longrightarrow \text{Repositories} \longrightarrow \text{MongoDB Driver}$$

```
backend/
├── app/
│   ├── main.py              # Application entrypoint & lifespan
│   ├── core/                # Configuration, security, logging, exceptions
│   │   ├── config.py        # Pydantic v2 BaseSettings
│   │   ├── security.py      # Passwords, JWT encoding/decoding
│   │   ├── database.py      # Async Motor client management
│   │   └── logging.py       # Structured JSON logging
│   ├── api/                 # API routing layer
│   │   ├── deps.py          # FastApi Dependency injection (DB, Current User)
│   │   └── v1/              # Versioned API routes
│   │       ├── router.py    # Master router
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── resumes.py
│   │       ├── jobs.py
│   │       ├── analysis.py
│   │       ├── evidence.py
│   │       ├── preparation.py
│   │       ├── interviews.py
│   │       └── admin.py
│   ├── schemas/             # Pydantic models for request validation & response serialization
│   ├── services/            # Pure business logic isolated from HTTP concerns
│   ├── repositories/        # MongoDB query abstraction
│   ├── ai/                  # Abstract provider interface & implementations
│   │   ├── base.py          # Abstract BaseAIProvider
│   │   ├── deterministic.py # Zero-cost rule-based provider
│   │   ├── openai_client.py # OpenAI-compatible client
│   │   └── prompts.py       # Grounded system prompts
│   └── ontology/            # Canonical skill dictionary and graph
```

---

## 3. End-to-End Data Flow Pipeline

The end-to-end data processing follows an evidence-grounded workflow:

```mermaid
sequenceDiagram
    autonumber
    actor Candidate
    participant UI as Frontend (React)
    participant API as FastAPI Router
    participant ResumeSvc as Resume Service
    participant JDSvc as JD Service
    participant OntSvc as Ontology Engine
    participant EvSvc as Evidence Engine
    participant MatchSvc as Matching Engine
    participant DB as MongoDB

    Candidate->>UI: Uploads Resume (PDF/DOCX) & Enters Target JD
    UI->>API: POST /resumes/upload & POST /jobs
    API->>ResumeSvc: Extract text, segments, links
    API->>JDSvc: Parse role, must-have & preferred skills
    ResumeSvc->>OntSvc: Normalize detected skills & projects
    JDSvc->>OntSvc: Normalize required skills
    API->>EvSvc: Correlate claims against project descriptions
    EvSvc->>EvSvc: Classify (PROVEN, TRANSFERABLE, MENTIONED, MISSING)
    EvSvc->>MatchSvc: Compute multidimensional readiness vector
    MatchSvc->>DB: Persist Analysis & Gap Report
    DB-->>UI: Return Evidence Map, Readiness Scores, and Remediation Plan
```

---

## 4. Evidence Classification Pipeline

The hallmark of CareerMetricX is the strict separation between mere assertion and substantiated proof:

```mermaid
flowchart TD
    Start([Skill Detected in Resume]) --> CheckSection{Found in which section?}
    
    CheckSection -->|Skills / Keywords only| Mentioned[Tag as MENTIONED: Confidence 0.35]
    CheckSection -->|Projects / Experience / Certs| ExtractSnippet[Extract Contextual Sentence]
    
    ExtractSnippet --> CheckAction{Contains Action Verb, Tool & Outcome?}
    CheckAction -->|Yes with quantifiable metrics| ProvenHigh[Tag as PROVEN: High Confidence 0.90]
    CheckAction -->|Yes descriptive context| ProvenMed[Tag as PROVEN: Med Confidence 0.75]
    CheckAction -->|Passive or ambiguous claim| ClaimVerify[Route to Claim Verification]
    
    ClaimVerify -->|Lacks supporting metrics| NeedsConfirm[Tag as NEEDS_CONFIRMATION]
    ClaimVerify -->|Confirmed by Repo/Cert| ProvenMed
    
    Start --> CheckOntology{Exact match in Target JD?}
    CheckOntology -->|No, but direct parent/child exists| Transferable[Tag as TRANSFERABLE: Confidence 0.60]
    CheckOntology -->|Not found anywhere| Missing[Tag as MISSING: Block Gap]
```

---

## 5. Architectural Decision Records (ADRs)

### ADR-001: Modular Monolith vs Microservices
- **Decision:** Build CareerMetricX as a modular monolith within a single FastAPI backend service rather than decomposing into 5+ microservices.
- **Rationale:** Microservices introduce distributed transactions, network latency, serialization overhead, and deployment complexity that obscure business logic in an academic/portfolio setting. Modular monolith provides clean code boundaries with simple zero-network in-process communication.
- **Extension Path:** Because domain boundaries are enforced via service classes and repositories, any module (e.g., `InterviewEngine`) can be extracted into an independent microservice later if traffic warrants.

### ADR-002: MongoDB Document Database vs Relational SQL
- **Decision:** Utilize MongoDB with the Motor async driver for primary persistence.
- **Rationale:** Resumes and Job Descriptions possess deeply nested, semi-structured, and polymorphic schemas (sections, variable-length project bullet points, dynamic evidence provenance trees, flexible interview evaluations). Document modeling prevents dozens of complex relational joins while allowing rich indexing on nested fields.
- **Integrity Guarantee:** Schema integrity is enforced at the application boundary via strict Pydantic v2 models before any write operation.

### ADR-003: Abstract AI Provider with Deterministic Fallback
- **Decision:** Abstract all generative AI and semantic inference capabilities behind an abstract base class (`BaseAIProvider`).
- **Rationale:** External AI APIs introduce network flakiness, rate limits, latency, and subscription costs. By developing a deterministic rule-based fallback provider, the entire platform remains 100% runnable, testable, and demonstrable in offline environments and GitHub Actions CI.

### ADR-004: Evidence Categorization Hierarchy
- **Decision:** Reject binary "match / no match" ATS scores in favor of a 4-tier capability classification (`PROVEN`, `TRANSFERABLE`, `MENTIONED`, `MISSING`).
- **Rationale:** A candidate claiming "Docker" in a skills list has not demonstrated the same competency as a candidate who wrote "Configured multi-stage Docker builds reducing image size by 65%". CareerMetricX makes this qualitative difference visible and measurable.

---

## 6. Future Extensibility: Placement Cell / Institutional Role

To accommodate institutional deployment (e.g., University Placement Cells) without architectural refactoring:
1. **Tenant/Cohort Partitioning:** The `User` and `Analysis` collections include optional `institution_id` and `cohort_id` attributes.
2. **Role Enumeration:** The RBAC system is pre-architected with `RoleEnum.PLACEMENT_OFFICER` alongside `CANDIDATE` and `ADMIN`.
3. **Cohort Aggregation Queries:** The repository layer provides cohort-level aggregation methods (e.g., `get_cohort_skill_deficits(cohort_id)`).
