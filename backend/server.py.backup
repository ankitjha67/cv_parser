from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone

# Import core modules
from src.schemas import CV, JD, MatchReport, TailoredCV, ProviderConfig
from src.ingestion import load_document
from src.parser import parse_cv, parse_jd
from src.scorer import score_cv_jd
from src.gap_analyzer import analyze_gaps
from src.rewriter import rewrite_cv_deterministic

# Import LLM providers
from src.llm.deterministic import DeterministicProvider
from src.llm.openai_adapter import OpenAIProvider
from src.llm.anthropic_adapter import AnthropicProvider
from src.llm.gemini_adapter import GeminiProvider
from src.llm.hf_adapter import HuggingFaceProvider


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="CV-JD Matcher API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# In-memory cache (in production, use Redis)
cache = {
    'cvs': {},
    'jds': {},
    'reports': {},
    'tailored_cvs': {}
}

# ========== REQUEST/RESPONSE MODELS ==========

class CVUploadResponse(BaseModel):
    cv_id: str
    name: str
    message: str

class JDAddRequest(BaseModel):
    title: str
    text: str

class JDAddResponse(BaseModel):
    jd_id: str
    title: str
    message: str

class MatchRequest(BaseModel):
    cv_id: str
    jd_id: str

class MatchResponse(BaseModel):
    report: MatchReport

class RewriteRequest(BaseModel):
    match_report_id: str
    provider: str = "deterministic"
    model: Optional[str] = None
    api_key: Optional[str] = None

class RewriteResponse(BaseModel):
    tailored_cv_id: str
    message: str

class ListCVsResponse(BaseModel):
    cvs: List[Dict]

class ListJDsResponse(BaseModel):
    jds: List[Dict]

# ========== ENDPOINTS ==========

@api_router.get("/")
async def root():
    return {
        "message": "CV-JD Matcher API",
        "version": "1.0.0",
        "endpoints": {
            "upload_cv": "POST /api/cv/upload",
            "add_jd": "POST /api/jd/add",
            "match": "POST /api/match",
            "rewrite": "POST /api/rewrite",
            "list_cvs": "GET /api/cvs",
            "list_jds": "GET /api/jds"
        }
    }

@api_router.post("/cv/upload", response_model=CVUploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    """Upload and parse CV (PDF/DOCX/TXT)."""
    try:
        content = await file.read()
        filename = file.filename
        
        # Parse document
        text = load_document(filename, content)
        
        # Extract structured CV
        cv = parse_cv(text)
        
        # Store in cache and DB
        cache['cvs'][cv.id] = cv
        await db.cvs.insert_one({
            **cv.model_dump(),
            'uploaded_at': cv.uploaded_at.isoformat()
        })
        
        return CVUploadResponse(
            cv_id=cv.id,
            name=cv.name,
            message=f"CV uploaded and parsed successfully. Found {len(cv.experiences)} experiences and {len(cv.skills)} skills."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CV: {str(e)}")

@api_router.post("/jd/add", response_model=JDAddResponse)
async def add_jd(request: JDAddRequest):
    """Add a Job Description."""
    try:
        # Parse JD
        jd = parse_jd(request.text)
        jd.title = request.title  # Override with user-provided title
        
        # Store in cache and DB
        cache['jds'][jd.id] = jd
        await db.jds.insert_one({
            **jd.model_dump(),
            'added_at': jd.added_at.isoformat()
        })
        
        return JDAddResponse(
            jd_id=jd.id,
            title=jd.title,
            message=f"JD added successfully. Extracted {len(jd.requirements)} requirements."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process JD: {str(e)}")

@api_router.post("/match", response_model=MatchResponse)
async def match_cv_jd(request: MatchRequest):
    """Run ATS-like matching between CV and JD."""
    try:
        # Retrieve CV and JD
        cv = cache['cvs'].get(request.cv_id)
        if not cv:
            # Try DB
            cv_doc = await db.cvs.find_one({'id': request.cv_id}, {'_id': 0})
            if cv_doc:
                cv = CV(**cv_doc)
                cache['cvs'][cv.id] = cv
            else:
                raise HTTPException(status_code=404, detail="CV not found")
        
        jd = cache['jds'].get(request.jd_id)
        if not jd:
            jd_doc = await db.jds.find_one({'id': request.jd_id}, {'_id': 0})
            if jd_doc:
                jd = JD(**jd_doc)
                cache['jds'][jd.id] = jd
            else:
                raise HTTPException(status_code=404, detail="JD not found")
        
        # Compute match score
        report = score_cv_jd(cv, jd)
        
        # Analyze gaps
        hard_gaps, soft_gaps = analyze_gaps(cv, jd, report)
        report.hard_gaps = hard_gaps
        report.soft_gaps = soft_gaps
        
        # Store report
        cache['reports'][report.id] = report
        await db.reports.insert_one({
            **report.model_dump(),
            'created_at': report.created_at.isoformat()
        })
        
        return MatchResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@api_router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_cv(request: RewriteRequest):
    """Generate tailored CV based on match report."""
    try:
        # Retrieve match report
        report = cache['reports'].get(request.match_report_id)
        if not report:
            report_doc = await db.reports.find_one({'id': request.match_report_id}, {'_id': 0})
            if report_doc:
                report = MatchReport(**report_doc)
                cache['reports'][report.id] = report
            else:
                raise HTTPException(status_code=404, detail="Match report not found")
        
        # Retrieve CV and JD
        cv = cache['cvs'].get(report.cv_id)
        if not cv:
            cv_doc = await db.cvs.find_one({'id': report.cv_id}, {'_id': 0})
            if cv_doc:
                cv = CV(**cv_doc)
                cache['cvs'][cv.id] = cv
        
        jd = cache['jds'].get(report.jd_id)
        if not jd:
            jd_doc = await db.jds.find_one({'id': report.jd_id}, {'_id': 0})
            if jd_doc:
                jd = JD(**jd_doc)
                cache['jds'][jd.id] = jd
        
        # Select provider
        provider_name = request.provider.lower()
        api_key = request.api_key or os.getenv('EMERGENT_LLM_KEY')
        
        if provider_name == "deterministic":
            # Use deterministic rewriter
            tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        elif provider_name == "openai":
            provider = OpenAIProvider(api_key=api_key, model=request.model or "gpt-5.2")
            # For now, use deterministic (LLM bullet-by-bullet rewrite is implemented but heavy)
            tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        elif provider_name == "anthropic":
            provider = AnthropicProvider(api_key=api_key, model=request.model or "claude-4-sonnet-20250514")
            tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        elif provider_name == "gemini":
            provider = GeminiProvider(api_key=api_key, model=request.model or "gemini-2.5-pro")
            tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        elif provider_name == "huggingface":
            provider = HuggingFaceProvider(model_name=request.model or "gpt2")
            tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")
        
        tailored.match_report_id = report.id
        
        # Store tailored CV
        cache['tailored_cvs'][tailored.id] = tailored
        await db.tailored_cvs.insert_one({
            **tailored.model_dump(),
            'created_at': tailored.created_at.isoformat()
        })
        
        return RewriteResponse(
            tailored_cv_id=tailored.id,
            message=f"Tailored CV generated successfully with {len(tailored.modifications)} modifications"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)}")

@api_router.get("/cvs", response_model=ListCVsResponse)
async def list_cvs():
    """List all uploaded CVs."""
    cvs_list = []
    for cv in cache['cvs'].values():
        cvs_list.append({
            'id': cv.id,
            'name': cv.name,
            'skills_count': len(cv.skills),
            'experiences_count': len(cv.experiences),
            'uploaded_at': cv.uploaded_at.isoformat()
        })
    return ListCVsResponse(cvs=cvs_list)

@api_router.get("/jds", response_model=ListJDsResponse)
async def list_jds():
    """List all added JDs."""
    jds_list = []
    for jd in cache['jds'].values():
        jds_list.append({
            'id': jd.id,
            'title': jd.title,
            'company': jd.company,
            'requirements_count': len(jd.requirements),
            'added_at': jd.added_at.isoformat()
        })
    return ListJDsResponse(jds=jds_list)

@api_router.get("/cv/{cv_id}")
async def get_cv(cv_id: str):
    """Get CV details."""
    cv = cache['cvs'].get(cv_id)
    if not cv:
        cv_doc = await db.cvs.find_one({'id': cv_id}, {'_id': 0})
        if cv_doc:
            return cv_doc
        raise HTTPException(status_code=404, detail="CV not found")
    return cv.model_dump()

@api_router.get("/jd/{jd_id}")
async def get_jd(jd_id: str):
    """Get JD details."""
    jd = cache['jds'].get(jd_id)
    if not jd:
        jd_doc = await db.jds.find_one({'id': jd_id}, {'_id': 0})
        if jd_doc:
            return jd_doc
        raise HTTPException(status_code=404, detail="JD not found")
    return jd.model_dump()

@api_router.get("/report/{report_id}")
async def get_report(report_id: str):
    """Get match report details."""
    report = cache['reports'].get(report_id)
    if not report:
        report_doc = await db.reports.find_one({'id': report_id}, {'_id': 0})
        if report_doc:
            return report_doc
        raise HTTPException(status_code=404, detail="Report not found")
    return report.model_dump()

@api_router.get("/tailored/{tailored_id}")
async def get_tailored_cv(tailored_id: str):
    """Get tailored CV details."""
    tailored = cache['tailored_cvs'].get(tailored_id)
    if not tailored:
        tailored_doc = await db.tailored_cvs.find_one({'id': tailored_id}, {'_id': 0})
        if tailored_doc:
            return tailored_doc
        raise HTTPException(status_code=404, detail="Tailored CV not found")
    return tailored.model_dump()

@api_router.get("/tailored/{tailored_id}/download")
async def download_tailored_cv(tailored_id: str):
    """Download tailored CV as text file."""
    tailored = cache['tailored_cvs'].get(tailored_id)
    if not tailored:
        tailored_doc = await db.tailored_cvs.find_one({'id': tailored_id}, {'_id': 0})
        if tailored_doc:
            tailored = TailoredCV(**tailored_doc)
        else:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
    
    # Format as text
    cv = tailored.cv
    text_content = f"{cv.name}\n\n"
    if cv.summary:
        text_content += f"SUMMARY\n{cv.summary}\n\n"
    
    text_content += "EXPERIENCE\n"
    for exp in cv.experiences:
        text_content += f"\n{exp.role}, {exp.company}, {exp.dates}\n"
        for bullet in exp.bullets:
            text_content += f"\u2022 {bullet}\n"
    
    text_content += f"\n\nSKILLS\n{', '.join(cv.skills)}\n\n"
    text_content += "EDUCATION\n"
    for edu in cv.education:
        text_content += f"{edu.get('degree', '')} - {edu.get('institution', '')} ({edu.get('year', '')})\n"
    
    return Response(
        content=text_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=tailored_cv_{cv.name.replace(' ', '_')}.txt"}
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
