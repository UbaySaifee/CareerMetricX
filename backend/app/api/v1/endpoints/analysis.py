"""API endpoints for resume analysis and semantic skill evaluation."""

import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.ai.base import BaseAIProvider
from app.api.deps import get_current_ai_provider
from app.core.config import settings
from app.core.database import db_manager
from app.schemas.analysis import AnalysisResponse, InterviewQuestion, JDCreate, SkillGapResult, StarRecommendation
from app.services.gap_engine import compute_skill_gaps
from app.services.parser import (
    detect_ats_manipulation,
    extract_candidate_name,
    extract_candidate_project_claims,
    extract_resume_text,
    extract_sections,
)

router = APIRouter()


@router.options("/evaluate", include_in_schema=False)
async def evaluate_options() -> Response:
    """Preflight OPTIONS handler ensuring /evaluate does not block CORS preflight."""
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


@router.post(
    "/evaluate",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate resume against job description",
    description="Extracts candidate text, categorizes skill gaps, audits claims, and synthesizes viva questions and preparation plan."
)
async def evaluate_resume(
    resume: UploadFile = File(..., description="Uploaded resume file (.pdf, .docx, .txt)"),
    jd_payload: str = Form(..., description="JSON serialized string matching the JDCreate schema"),
    ai_provider: BaseAIProvider = Depends(get_current_ai_provider),
) -> AnalysisResponse:
    """Analyze an uploaded candidate resume against a target job description."""
    # 1. Parse and validate Job Description JSON payload
    try:
        jd_dict = json.loads(jd_payload)
        jd = JDCreate(**jd_dict)
    except json.JSONDecodeError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format for 'jd_payload': {err}",
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema validation error in 'jd_payload': {err}",
        ) from err

    # 2. Validate file extension
    filename = resume.filename or "resume.pdf"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    allowed_extensions = [e.lower().lstrip(".") for e in settings.ALLOWED_EXTENSIONS]

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '.{ext}'. Allowed types: {settings.ALLOWED_EXTENSIONS}",
        )

    # 3. Read file bytes and validate size
    try:
        file_bytes = await resume.read()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {err}",
        ) from err

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # 4. Extract and clean resume text
    try:
        resume_text = extract_resume_text(file_bytes, filename)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # 5. Extract structural sections and candidate metadata
    candidate_name = extract_candidate_name(resume_text)
    sections = extract_sections(resume_text)
    claims = extract_candidate_project_claims(resume_text, sections)

    # 6. Execute semantic skill gap calculation
    gap_result = compute_skill_gaps(
        required_skills=jd.required_skills,
        resume_text=resume_text,
        preferred_skills=jd.preferred_skills,
        sections=sections,
    )

    # 7. LLM / Deterministic Claim Verification & ATS Manipulation Audit
    ats_flags = detect_ats_manipulation(resume_text)
    claim_flags = await ai_provider.verify_claims(
        project_claims=claims,
        resume_text=resume_text,
    )
    if ats_flags:
        filtered_claim_flags = [f for f in claim_flags if not f.startswith("All analyzed project assertions adhere")]
        verification_flags = ats_flags + filtered_claim_flags
    else:
        verification_flags = claim_flags

    # 8. Synthesize grounded viva questions
    targeted_questions = await ai_provider.generate_viva_questions(
        claims=claims,
        role=jd.title,
        required_skills=jd.required_skills,
        missing_skills=gap_result.missing_skills,
        experience_level=jd.experience_level,
        limit=5,
    )

    # 9. Generate 7-day preparation roadmap
    prep_plan = await ai_provider.generate_prep_plan(
        missing_skills=gap_result.missing_skills,
        role=jd.title,
        days=7,
    )

    # 10. Generate STAR Transferable Skill Rewrite Recommendations
    raw_star_recs = await ai_provider.generate_star_recommendations(
        transferable_skills=gap_result.transferable_skills,
        role=jd.title,
        resume_text=resume_text,
    )
    star_recommendations: list[StarRecommendation] = [
        StarRecommendation(**rec) if isinstance(rec, dict) else rec
        for rec in raw_star_recs
    ]

    # 11. Persist evaluation record via database manager
    evaluation_record = {
        "candidate_name": candidate_name,
        "role_applied": jd.title,
        "gap_analysis": gap_result.model_dump(),
        "verification_flags": verification_flags,
        "targeted_questions": [q.model_dump() for q in targeted_questions],
        "prep_plan": prep_plan,
        "star_recommendations": [r.model_dump() for r in star_recommendations],
        "job_description": jd.model_dump(),
    }
    evaluation_id = await db_manager.save_evaluation(evaluation_record)

    return AnalysisResponse(
        evaluation_id=evaluation_id,
        candidate_name=candidate_name,
        role_applied=jd.title,
        gap_analysis=gap_result,
        verification_flags=verification_flags,
        targeted_questions=targeted_questions,
        prep_plan=prep_plan,
        star_recommendations=star_recommendations,
        created_at=evaluation_record.get("created_at"),
    )

@router.options("/report/{report_id}", include_in_schema=False)
async def report_id_options(report_id: str) -> Response:
    """Preflight OPTIONS handler ensuring /report/{report_id} does not block CORS preflight."""
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


@router.options("/report", include_in_schema=False)
async def report_options() -> Response:
    """Preflight OPTIONS handler ensuring /report does not block CORS preflight."""
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


@router.get(
    "/report/{report_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch stored evaluation report",
    description="Retrieves a previously computed career evaluation report by report ID."
)
async def get_evaluation_report(report_id: str) -> AnalysisResponse:
    """Fetch stored evaluation analysis by report_id."""
    report_data = await db_manager.get_evaluation(report_id)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation report with ID '{report_id}' was not found.",
        )

    # Reconstruct SkillGapResult if stored as dict
    gap_data = report_data.get("gap_analysis")
    if isinstance(gap_data, dict):
        gap_analysis = SkillGapResult(**gap_data)
    elif isinstance(gap_data, SkillGapResult):
        gap_analysis = gap_data
    else:
        gap_analysis = SkillGapResult(
            match_percentage=0.0,
            radar_metrics={
                "Core Skills": 0.0,
                "Transferable": 0.0,
                "System Design": 0.0,
                "Tooling": 0.0,
                "Claim Credibility": 0.0,
            }
        )

    raw_questions = report_data.get("targeted_questions", [])
    targeted_questions: list[InterviewQuestion] = []
    for q in raw_questions:
        if isinstance(q, dict):
            targeted_questions.append(InterviewQuestion(**q))
        elif isinstance(q, InterviewQuestion):
            targeted_questions.append(q)

    raw_star = report_data.get("star_recommendations", [])
    star_recommendations: list[StarRecommendation] = []
    for r in raw_star:
        if isinstance(r, dict):
            star_recommendations.append(StarRecommendation(**r))
        elif isinstance(r, StarRecommendation):
            star_recommendations.append(r)

    return AnalysisResponse(
        evaluation_id=report_data.get("evaluation_id", report_id),
        candidate_name=report_data.get("candidate_name"),
        role_applied=report_data.get("role_applied", "Unknown Role"),
        gap_analysis=gap_analysis,
        verification_flags=report_data.get("verification_flags", []),
        targeted_questions=targeted_questions,
        prep_plan=report_data.get("prep_plan", []),
        star_recommendations=star_recommendations,
        created_at=report_data.get("created_at"),
    )

