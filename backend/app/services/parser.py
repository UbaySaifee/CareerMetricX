"""Document parser and text normalizer for resume ingestion."""

import io
import re
from typing import Any, Optional


def clean_and_normalize_text(raw_text: str) -> str:
    """Normalize extracted text, clean bullet points, remove non-printable characters."""
    if not raw_text:
        return ""

    # Normalize null bytes and non-printable characters
    cleaned = raw_text.replace("\x00", "")

    # Standardize bullet characters
    cleaned = re.sub(r"[\u2022\u2023\u25e6\u2043\u2219\uf0a7\u25aa]", "• ", cleaned)

    # Standardize dashes and quotes
    cleaned = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015]", "-", cleaned)
    cleaned = re.sub(r"[\u2018\u2019]", "'", cleaned)
    cleaned = re.sub(r"[\u201c\u201d]", '"', cleaned)

    # Standardize multiple horizontal spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Standardize line breaks and trim excessive blank lines
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF (fitz) with pypdf fallback."""
    extracted_text = ""

    # Primary: PyMuPDF (fitz)
    try:
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except ImportError:
            import pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        extracted_text = "\n".join(pages).strip()
    except Exception:
        extracted_text = ""

    # Fallback: pypdf if PyMuPDF failed or yielded empty output
    if not extracted_text:
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            extracted_text = "\n".join(pages).strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF document: {e}") from e

    return extracted_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX document including paragraphs and tables."""
    try:
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        # Extract text from tables if present
        table_lines = []
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    table_lines.append(row_text)

        full_content = "\n".join(paragraphs + table_lines)
        return full_content.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX document: {e}") from e


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """Extract and normalize resume text from uploaded PDF, DOCX, or TXT."""
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext == "pdf":
        raw = extract_text_from_pdf(file_bytes)
    elif ext in ["docx", "doc"]:
        raw = extract_text_from_docx(file_bytes)
    elif ext in ["txt", "text"]:
        try:
            raw = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw = file_bytes.decode("latin-1", errors="replace")
    else:
        raise ValueError(f"Unsupported file format '.{ext}'. Supported formats: .pdf, .docx, .txt")

    normalized = clean_and_normalize_text(raw)
    if not normalized or len(normalized) < 20:
        raise ValueError("Document appears empty or contains no readable text.")

    return normalized


def extract_candidate_name(text: str) -> Optional[str]:
    """Heuristic extraction of candidate name from document header lines."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    # Check top 4 lines
    for line in lines[:4]:
        # Skip lines that look like emails, URLs, phones, or section titles
        if any(c in line for c in ["@", "http", "github.com", "linkedin.com", "|", "+1", "+91"]):
            continue
        cleaned_line = re.sub(r"[^a-zA-Z\s.-]", "", line).strip()
        words = cleaned_line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return cleaned_line

    return lines[0][:40].strip() if lines else None


SECTION_PATTERNS = {
    "summary": r"(?:professional\s+summary|summary|profile|about\s+me|objective)",
    "skills": r"(?:technical\s+skills|core\s+skills|skills\s+(&|and)\s+technologies|skills|technologies|competencies)",
    "experience": r"(?:work\s+experience|professional\s+experience|experience|employment\s+history|work\s+history)",
    "projects": r"(?:key\s+projects|academic\s+projects|personal\s+projects|projects|portfolio)",
    "education": r"(?:academic\s+background|education|qualifications)",
    "certifications": r"(?:certifications|certificates|licenses)"
}


def extract_sections(text: str) -> dict[str, str]:
    """Parse resume text into discrete semantic sections."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {k: [] for k in SECTION_PATTERNS}
    sections["other"] = []

    current_section = "other"

    # Compile regex pattern matching section headers
    header_regexes = {
        name: re.compile(rf"^\s*(?:#+\s*)?{pattern}\s*[:\-]?\s*$", re.IGNORECASE)
        for name, pattern in SECTION_PATTERNS.items()
    }

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        matched_section = None
        # Check if line acts as a section header
        if len(line_stripped) < 45:
            for sec_name, regex in header_regexes.items():
                if regex.match(line_stripped):
                    matched_section = sec_name
                    break

        if matched_section:
            current_section = matched_section
        else:
            sections[current_section].append(line_stripped)

    result: dict[str, str] = {}
    for k, v in sections.items():
        content = "\n".join(v).strip()
        result[k] = content
        result[k.capitalize()] = content
    return result


def extract_candidate_project_claims(text: str, sections: Optional[dict[str, str]] = None) -> list[str]:
    """Extract individual bullet points or project sentences for evidence interrogation."""
    if sections is None:
        sections = extract_sections(text)

    # Prefer projects and experience sections, fallback to raw text
    source_text = "\n".join([
        sections.get("projects", ""),
        sections.get("experience", "")
    ]).strip()

    if not source_text or len(source_text) < 50:
        source_text = text

    # Split into bullet points or sentences
    candidates: list[str] = []
    for line in source_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove bullet prefix if present
        clean_line = re.sub(r"^[•\-*]\s*", "", line).strip()
        if len(clean_line) > 25:
            candidates.append(clean_line)

    return candidates


def detect_ats_manipulation(raw_text: str) -> list[str]:
    """Audit resume text for ATS keyword-stuffing, prompt injection tokens, and excessive skill density."""
    flags: list[str] = []
    if not raw_text or not raw_text.strip():
        return flags

    lowered = raw_text.lower()

    # 1. Prompt Injection Tokens & Adversarial Directives
    injection_patterns = [
        (r"\b(?:ignore|disregard|forget|override)\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b", "Ignore Previous Instructions token"),
        (r"\b(?:system\s+prompt|developer\s+mode|jailbreak|dan\s+mode)\b", "System Prompt / Privilege Escalation token"),
        (r"\b(?:you\s+must\s+rate|give\s+(?:this\s+candidate\s+)?(?:a\s+)?100%|output\s+only\s+pass)\b", "Evaluation Override Directive"),
        (r"\b(?:act\s+as\s+an\s+unrestricted\s+evaluator|new\s+system\s+directive)\b", "System Role Override Directive"),
    ]
    for pattern, label in injection_patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            flags.append(
                f"Adversarial Prompt Injection Alert: Detected manipulation token '{match.group(0)}' ({label}) attempting to bias automated evaluation."
            )
            break

    # 2. Comma-separated keyword blocks exceeding 15 consecutive tech terms without verbs
    verb_indicator_set = {
        "built", "developed", "engineered", "designed", "architected", "implemented",
        "created", "optimized", "managed", "led", "scaled", "maintained", "configured",
        "tested", "deployed", "migrated", "automated", "spearheaded", "orchestrated",
        "collaborated", "analyzed", "reduced", "increased", "delivered", "integrated",
        "resolved", "facilitated", "improved", "wrote", "used", "utilized", "worked",
        "is", "was", "are", "were", "have", "had", "has", "do", "did", "can", "could", "will"
    }

    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    keyword_stuffing_flagged = False

    for line in lines:
        for delimiter in [",", "|", ";", "/"]:
            if line.count(delimiter) >= 14:
                items = [item.strip() for item in line.split(delimiter) if item.strip()]
                if len(items) >= 15:
                    verbs_found = sum(
                        1 for item in items
                        if any(re.search(r"\b" + re.escape(v) + r"\b", item.lower()) for v in verb_indicator_set)
                    )
                    if verbs_found == 0 or (verbs_found / len(items)) < 0.05:
                        sample_preview = ", ".join(items[:6])
                        flags.append(
                            f"Suspected ATS Keyword-Stuffing: Detected comma-separated keyword block of {len(items)} consecutive technical terms without verbs (e.g. '{sample_preview}...')."
                        )
                        keyword_stuffing_flagged = True
                        break
        if keyword_stuffing_flagged:
            break

    # If not caught by per-line check, inspect general text sequences with 15+ comma items without verbs
    if not keyword_stuffing_flagged:
        comma_blocks = re.findall(r"(?:[A-Za-z0-9+#.-]+(?:\s+[A-Za-z0-9+#.-]+)?\s*,\s*){14,}[A-Za-z0-9+#.-]+", raw_text)
        for block in comma_blocks:
            items = [item.strip() for item in block.split(",") if item.strip()]
            if len(items) >= 15:
                verbs_found = sum(
                    1 for item in items
                    if any(re.search(r"\b" + re.escape(v) + r"\b", item.lower()) for v in verb_indicator_set)
                )
                if verbs_found == 0:
                    sample_preview = ", ".join(items[:6])
                    flags.append(
                        f"Suspected ATS Keyword-Stuffing: Detected comma-separated keyword block of {len(items)} consecutive technical terms without verbs (e.g. '{sample_preview}...')."
                    )
                    keyword_stuffing_flagged = True
                    break

    # 3. Excessive skill density with zero narrative context
    words = [w for w in re.findall(r"\b[A-Za-z0-9+#.-]+\b", raw_text)]
    total_words = len(words)
    if total_words > 0:
        verbs_in_doc = sum(1 for w in words if w.lower() in verb_indicator_set)
        sections = extract_sections(raw_text)
        skills_text = sections.get("skills", "")
        exp_text = sections.get("experience", "")
        proj_text = sections.get("projects", "")

        narrative_text = f"{exp_text} {proj_text}".strip()
        narrative_words = len(narrative_text.split()) if narrative_text else 0
        skills_words = len(skills_text.split()) if skills_text else 0

        if skills_words >= 20 and narrative_words < 20 and verbs_in_doc < 4:
            flags.append(
                "Excessive Skill Density Alert: Document exhibits disproportionate keyword concentration with zero or negligible descriptive engineering narrative."
            )
        elif total_words >= 50 and (verbs_in_doc / total_words) < 0.02 and not keyword_stuffing_flagged:
            flags.append(
                "Excessive Skill Density Alert: Document contains overwhelming keyword density with negligible active verbs or technical context."
            )

    return flags

