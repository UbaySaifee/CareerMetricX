# CareerMetricX — RESTful API Specification

**System Title:** CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform  
**Base URL:** `/api/v1`  
**Protocol:** HTTPS / JSON REST  
**Authentication:** HTTP Authorization Header with Bearer JWT  
**Version:** 1.0.0  

---

## 1. Global Conventions & Standards

### 1.1 Headers
- `Content-Type: application/json` (or `multipart/form-data` for file uploads)
- `Authorization: Bearer <access_token>`

### 1.2 Unified Error Envelope
All error responses adhere to the standard schema:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resume version does not exist.",
    "status_code": 404,
    "timestamp": "2026-09-27T12:00:00Z",
    "details": null
  }
}
```

### 1.3 Pagination Standard
Endpoints returning collections support:
- `page`: Integer $\ge 1$ (default: `1`)
- `page_size`: Integer $1 \dots 100$ (default: `20`)

Pagination response format:
```json
{
  "items": [],
  "pagination": {
    "total_count": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### 1.4 System Health & Baseline Endpoints (Active in Phase 1)

#### `GET /`
Root discovery endpoint providing service title, status, and API links.
- **Authentication:** None
- **Response (200 OK):**
  ```json
  {
    "title": "CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform",
    "tagline": "Measure your skills. Prove your readiness.",
    "version": "0.1.0",
    "status": "online",
    "docs_url": "/docs",
    "api_prefix": "/api/v1"
  }
  ```

#### `GET /api/v1/health`
System liveness and subsystem diagnostics endpoint.
- **Authentication:** None
- **Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "app_name": "CareerMetricX",
    "version": "0.1.0",
    "environment": "development",
    "database": {
      "connected": true,
      "database_name": "careermetricx_dev",
      "host": "localhost:27017"
    },
    "ai_provider": {
      "active_provider": "deterministic-rule-engine",
      "configured_mode": "deterministic",
      "deterministic_fallback_available": true
    }
  }
  ```

> **Implementation Note:** Sections 2 through 8 below define the target RESTful domain contracts to be implemented sequentially across Phase 2 through Phase 11 per [ROADMAP.md](ROADMAP.md).

---

## 2. Authentication & Profile Endpoints

### 2.1 `POST /auth/register`
Register a new candidate account.
- **Request Body:**
  ```json
  {
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
    "full_name": "Ada Lovelace"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "user_id": "673f8a1...",
    "email": "candidate@example.com",
    "full_name": "Ada Lovelace",
    "role": "CANDIDATE",
    "created_at": "2026-09-27T12:00:00Z"
  }
  ```

### 2.2 `POST /auth/login`
Authenticate with email and password to receive JWT tokens.
- **Request Body:**
  ```json
  {
    "username": "candidate@example.com",
    "password": "StrongPassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in_seconds": 3600
  }
  ```

### 2.3 `POST /auth/refresh`
Rotate refresh token and issue a fresh access token.

### 2.4 `GET /auth/me`
Retrieve currently authenticated identity and role.

---

## 3. Resume Management Endpoints

### 3.1 `POST /resumes/upload`
Upload a resume file for validation and automated structured extraction.
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: Binary file (`.pdf`, `.docx`, `.txt`, max 10MB)
  - `title`: String (e.g., "Software Engineer Resume 2026")
- **Response (201 Created):**
  ```json
  {
    "resume_id": "673f8a2...",
    "version_id": "673f8a3...",
    "version_number": 1,
    "status": "PROCESSED",
    "extracted_summary": {
      "sections_found": ["Summary", "Education", "Projects", "Skills"],
      "skills_count": 14,
      "projects_count": 3
    }
  }
  ```

### 3.2 `GET /resumes`
List candidate's uploaded resumes with version counts.

### 3.3 `GET /resumes/{resume_id}/versions/{version_id}`
Retrieve raw extracted text, sections, and structured metadata.

---

## 4. Job Description Endpoints

### 4.1 `POST /jobs`
Create and parse a target job description.
- **Request Body:**
  ```json
  {
    "title": "Backend Software Engineer",
    "company_name": "Tech Corp",
    "raw_text": "We are seeking a Python/FastAPI engineer with experience in Docker and PostgreSQL..."
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "job_id": "673f8a4...",
    "title": "Backend Software Engineer",
    "must_have_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
    "preferred_skills": ["Redis", "Kubernetes"],
    "responsibilities": ["Design high-throughput APIs..."],
    "seniority_level": "Mid-Level"
  }
  ```

---

## 5. Evidence & Analysis Endpoints

### 5.1 `POST /analysis`
Run multidimensional readiness evaluation matching a resume version against a job description.
- **Request Body:**
  ```json
  {
    "resume_version_id": "673f8a3...",
    "job_description_id": "673f8a4..."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "analysis_id": "673f8a5...",
    "metrics": {
      "requirement_coverage": 0.85,
      "evidence_depth": 0.78,
      "transferability_factor": 0.60,
      "interview_defensibility": 0.82,
      "overall_readiness_score": 0.79
    },
    "evidence_distribution": {
      "proven": 6,
      "transferable": 2,
      "mentioned": 3,
      "missing": 1
    },
    "critical_gaps": [
      {
        "skill": "Docker",
        "gap_type": "WEAK_EVIDENCE",
        "remediation_priority": "HIGH"
      }
    ],
    "explanation": "High coverage of core Python/FastAPI backend logic with direct project backing; Docker is mentioned in skills list without supporting containerized deployment evidence."
  }
  ```

### 5.2 `GET /evidence/{resume_version_id}`
Fetch granular evidence provenance items categorized by skill and status (`PROVEN`, `TRANSFERABLE`, `MENTIONED`, `MISSING`).

---

## 6. Personalized Preparation Endpoints

### 6.1 `GET /preparation/{analysis_id}`
Fetch the generated actionable remediation plan for identified capability gaps.
- **Response (200 OK):**
  ```json
  {
    "plan_id": "673f8a6...",
    "analysis_id": "673f8a5...",
    "tasks": [
      {
        "task_id": "673f8a7...",
        "skill": "Docker",
        "title": "Containerize existing FastAPI project with Docker Compose",
        "proof_artifact": "Dockerfile and compose file pushed to public Git repository",
        "interview_checkpoint": "Explain layer caching and container network isolation",
        "is_completed": false
      }
    ]
  }
  ```

### 6.2 `PATCH /preparation/tasks/{task_id}`
Update task completion status and attach proof URL.

---

## 7. Interview Engine Endpoints

### 7.1 `POST /interview/start`
Initialize a grounded interview simulation.
- **Request Body:**
  ```json
  {
    "analysis_id": "673f8a5...",
    "mode": "TECHNICAL_DEEP_DIVE"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "session_id": "673f8a8...",
    "current_question_index": 1,
    "total_questions": 5,
    "first_question": {
      "question_id": "673f8a9...",
      "targeted_skill": "FastAPI",
      "question_text": "In your telemetry project, you handled 10,000 events/sec with FastAPI. How did you prevent CPU-bound tasks from blocking the async event loop?"
    }
  }
  ```

### 7.2 `POST /interview/{session_id}/answer`
Submit a technical answer and receive multidimensional, grounded evaluation.
- **Request Body:**
  ```json
  {
    "question_id": "673f8a9...",
    "answer_text": "I used run_in_threadpool and background tasks for non-async calculations..."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "evaluation": {
      "scores": {
        "relevance": 9.0,
        "technical_correctness": 8.5,
        "completeness": 8.0,
        "specificity": 8.5,
        "clarity": 8.0,
        "resume_consistency": 9.0
      },
      "strengths": ["Accurately highlighted threadpool offloading"],
      "missing_points": ["Did not discuss ProcessPoolExecutor for heavy CPU bound tasks"],
      "improvement_suggestion": "Note that CPU-bound operations in Python still contend with the GIL in threads.",
      "is_advisory": true
    },
    "next_question": { ... }
  }
  ```

---

## 8. Admin & System Health Endpoints

### 8.1 `GET /health`
Returns system liveness, MongoDB connection status, and active AI provider state.

### 8.2 `GET /admin/audit-logs`
Retrieve paginated administrative security and activity audit logs (Admin only).
