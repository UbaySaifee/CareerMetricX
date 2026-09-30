# CareerMetricX — Security Architecture & Threat Model

**System Title:** CareerMetricX — Evidence-Grounded Career Readiness & Interview Intelligence Platform  
**Compliance Standard:** OWASP Top 10 Mitigations & Secure Coding Guidelines  
**Version:** 1.0.0  

---

## 1. Security Architecture Principles

1. **Defense in Depth:** Security controls are implemented across multiple layers: reverse proxy (Nginx), application middleware (FastAPI), schema validation (Pydantic), and database constraints (MongoDB).
2. **Zero-Trust Input Validation:** All external input is treated as untrusted and strictly parsed using Pydantic v2 models before reaching business logic.
3. **Least Privilege:** Services, database accounts, and application roles operate with the minimum permissions necessary.
4. **Zero Hardcoded Secrets:** Configuration and secrets are exclusively ingested via environment variables validated on application startup.

---

## 2. Threat Modeling & OWASP Top 10 Mitigations

### 2.1 A01: Broken Access Control
- **Risk:** Candidate A accessing Candidate B's resume, analysis results, or interview transcripts by guessing document IDs.
- **Mitigation:**
  - Every resource query in the repository layer automatically injects the authenticated `user_id` from the decoded JWT:
    ```python
    # Secure ownership check
    doc = await db.resumes.find_one({"_id": ObjectId(resume_id), "user_id": current_user.id})
    if not doc:
        raise NotFoundException("Resume not found or access denied")
    ```
  - Role-Based Access Control (RBAC) enforced via FastAPI dependency guards (`@require_roles(RoleEnum.ADMIN)`).

### 2.2 A02: Cryptographic Failures & Credential Handling
- **Passwords:** Hashed using **Argon2id** (or BCrypt with cost factor 12). Plaintext passwords are never logged, serialized, or stored.
- **Tokens:** Short-lived JWT Access Tokens (60-minute expiry) signed using HMAC-SHA256 (`HS256`) with a cryptographically secure random key.
- **Refresh Tokens:** Opaque, single-use refresh tokens stored in the database with rotation on every refresh call.

### 2.3 A03: Injection (NoSQL / OS Injection)
- **MongoDB Injection:** Motor/PyMongo API treats queries as structured objects rather than raw concatenated strings. BSON deserialization strictly avoids `$where` JavaScript evaluation.
- **Input Sanitization:** All text inputs are validated against regex patterns and character length constraints.

### 2.4 A04: Insecure Design & File Upload Exploits
- **Threat:** Malicious executable files disguised as `.pdf` or zip-bombs targeting PyMuPDF / python-docx.
- **Mitigations:**
  1. **Extension Whitelist:** Strictly restricted to `.pdf`, `.docx`, and `.txt`.
  2. **Magic Byte Verification:** File header inspection confirms genuine MIME type prior to invoking parsers.
  3. **Size Clamping:** Hard limit of 10MB enforced at reverse proxy and FastAPI upload middleware.
  4. **Isolated Storage:** Files are stored in non-executable filesystem locations using randomized UUID filenames rather than user-provided names.

### 2.5 A05: Security Misconfiguration & Secret Management
- **Startup Secret Validation:** On application initialization, `app.core.config.Settings` validates that `SECRET_KEY` is not using the default placeholder in production environments.
- **CORS Policy:** Strict origin whitelisting configured via `BACKEND_CORS_ORIGINS`. Wildcards (`"*"`) are explicitly forbidden in production.

### 2.6 A07: Identification and Authentication Failures
- **Brute Force Protection:** IP-based and user-based rate limiting on `/auth/login` (maximum 5 attempts per minute).
- **Session Revocation:** Logout invalidates the active refresh token in the database.

### 2.7 A09: Security Logging and Monitoring Failures
- **Audit Logs:** Immutable audit records created for sensitive actions: authentication attempts, role modifications, document uploads, and profile deletions.
- **Sanitized Logs:** Credentials, tokens, and personal identifying information (PII) are scrubbed before writing to logs.

---

## 3. Data Privacy & User Deletion Rights

In alignment with modern data privacy frameworks (GDPR / Digital Personal Data Protection Act):
- **Right to Erasure (`DELETE /users/me`):** Cascading deletion removes user credentials, resumes, parsed texts, evidence items, analyses, and interview sessions from MongoDB and file storage.
