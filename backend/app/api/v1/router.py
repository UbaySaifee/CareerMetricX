"""Master API v1 router consolidating all domain route collections."""

from fastapi import APIRouter

from app.api.v1.endpoints.analysis import router as analysis_router
from app.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Core system endpoints
api_v1_router.include_router(health_router)

# Semantic Analysis & Verification Endpoints
api_v1_router.include_router(analysis_router, prefix="/analyzer", tags=["Analyzer"])
api_v1_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])

# Domain module routes will be attached here in subsequent phases:
# api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# api_v1_router.include_router(users_router, prefix="/users", tags=["Users"])
# api_v1_router.include_router(resumes_router, prefix="/resumes", tags=["Resumes"])
# api_v1_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
# api_v1_router.include_router(evidence_router, prefix="/evidence", tags=["Evidence"])
# api_v1_router.include_router(prep_router, prefix="/preparation", tags=["Preparation"])
# api_v1_router.include_router(interview_router, prefix="/interview", tags=["Interviews"])
# api_v1_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
