from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone

# Import core modules
from src.schemas import (
    CV, JD, MatchReport, TailoredCV, ProviderConfig,
    User, UserCreate, Application, ApplicationCreate, ApplicationUpdate,
    CompetitiveAnalysis, IndustryBenchmark, InterviewPrep
)
from src.ingestion import load_document
from src.parser import parse_cv, parse_jd
from src.scorer import score_cv_jd
from src.gap_analyzer import analyze_gaps
from src.rewriter import rewrite_cv_deterministic
from src.analytics import (
    calculate_competitive_analysis,
    calculate_industry_benchmarks,
    calculate_success_rate_by_score_threshold
)
from src.interview_prep import generate_interview_prep
from src.formatter import format_luxury_cv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="CV-JD Matcher API - Premium", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# In-memory cache
cache = {
    'cvs': {}, 'jds': {}, 'reports': {}, 'tailored_cvs': {},
    'users': {}, 'applications': {}, 'interview_preps': {}
}

# ========== HELPER FUNCTIONS ==========

def get_user_email(authorization: Optional[str] = None) -> str:
    """Extract user email from header or return anonymous."""
    if authorization and authorization.startswith('Bearer '):
        email = authorization.replace('Bearer ', '')
        return email if '@' in email else 'anonymous'
    return 'anonymous'

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
    competitive_analysis: Optional[CompetitiveAnalysis] = None
    industry_benchmark: Optional[IndustryBenchmark] = None

class RewriteRequest(BaseModel):
    match_report_id: str
    provider: str = "deterministic"
    model: Optional[str] = None
    api_key: Optional[str] = None

class InterviewPrepRequest(BaseModel):
    match_report_id: str
    provider: str = "openai"
    api_key: Optional[str] = None

# ========== AUTH ENDPOINTS ==========

@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Check if user exists
    existing = await db.users.find_one({'email': user_data.email}, {'_id': 0})
    if existing:
        return {"message": "User already exists", "email": user_data.email}
    
    user = User(**user_data.model_dump())
    await db.users.insert_one({
        **user.model_dump(),
        'created_at': user.created_at.isoformat()
    })
    cache['users'][user.email] = user
    
    return {"message": "User registered successfully", "email": user.email}

@api_router.get("/auth/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info."""
    email = get_user_email(authorization)
    if email == 'anonymous':
        return {"email": "anonymous", "name": "Guest User", "total_applications": 0}
    
    user = cache['users'].get(email)
    if not user:
        user_doc = await db.users.find_one({'email': email}, {'_id': 0})
        if user_doc:
            user = User(**user_doc)
            cache['users'][email] = user
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user.model_dump()

# ========== CV & JD ENDPOINTS (existing, enhanced with user_email) ==========

@api_router.post("/cv/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """Upload and parse CV."""
    user_email = get_user_email(authorization)
    try:
        content = await file.read()
        filename = file.filename
        text = load_document(filename, content)
        cv = parse_cv(text)
        cv.user_email = user_email
        
        cache['cvs'][cv.id] = cv
        await db.cvs.insert_one({
            **cv.model_dump(),
            'uploaded_at': cv.uploaded_at.isoformat()
        })
        
        return CVUploadResponse(
            cv_id=cv.id,
            name=cv.name,
            message=f"CV uploaded successfully. Found {len(cv.experiences)} experiences and {len(cv.skills)} skills."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CV: {str(e)}")

@api_router.post("/jd/add", response_model=JDAddResponse)
async def add_jd(request: JDAddRequest, authorization: Optional[str] = Header(None)):
    """Add a Job Description."""
    user_email = get_user_email(authorization)
    try:
        jd = parse_jd(request.text)
        jd.title = request.title
        jd.user_email = user_email
        
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
async def match_cv_jd(request: MatchRequest, authorization: Optional[str] = Header(None)):
    """Run ATS matching with competitive analysis."""
    user_email = get_user_email(authorization)
    try:
        # Retrieve CV and JD
        cv = cache['cvs'].get(request.cv_id)
        if not cv:
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
        report.user_email = user_email
        hard_gaps, soft_gaps = analyze_gaps(cv, jd, report)
        report.hard_gaps = hard_gaps
        report.soft_gaps = soft_gaps
        
        # Store report
        cache['reports'][report.id] = report
        await db.reports.insert_one({
            **report.model_dump(),
            'created_at': report.created_at.isoformat()
        })
        
        # Calculate competitive analysis (if enough data)
        all_reports_cursor = db.reports.find({}, {'_id': 0}).limit(1000)
        all_reports_docs = await all_reports_cursor.to_list(1000)
        all_reports = [MatchReport(**doc) for doc in all_reports_docs if 'total_score' in doc]
        
        competitive_analysis = None
        industry_benchmark = None
        
        if len(all_reports) >= 5:  # Need minimum data
            competitive_analysis = calculate_competitive_analysis(report, all_reports)
            industry_benchmark = calculate_industry_benchmarks(all_reports)
        
        return MatchResponse(
            report=report,
            competitive_analysis=competitive_analysis,
            industry_benchmark=industry_benchmark
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@api_router.post("/rewrite")
async def rewrite_cv(request: RewriteRequest, authorization: Optional[str] = Header(None)):
    """Generate tailored CV."""
    user_email = get_user_email(authorization)
    try:
        report = cache['reports'].get(request.match_report_id)
        if not report:
            report_doc = await db.reports.find_one({'id': request.match_report_id}, {'_id': 0})
            if report_doc:
                report = MatchReport(**report_doc)
                cache['reports'][report.id] = report
            else:
                raise HTTPException(status_code=404, detail="Match report not found")
        
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
        
        # Use deterministic rewriter (LLM path is complex and async)
        tailored = rewrite_cv_deterministic(cv, jd, report.hard_gaps)
        tailored.match_report_id = report.id
        tailored.user_email = user_email
        
        cache['tailored_cvs'][tailored.id] = tailored
        await db.tailored_cvs.insert_one({
            **tailored.model_dump(),
            'created_at': tailored.created_at.isoformat()
        })
        
        return {
            "tailored_cv_id": tailored.id,
            "message": f"Tailored CV generated with {len(tailored.modifications)} modifications"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)}")

# ========== INTERVIEW PREP ENDPOINTS ==========

@api_router.post("/interview-prep", response_model=InterviewPrep)
async def create_interview_prep(
    request: InterviewPrepRequest,
    authorization: Optional[str] = Header(None)
):
    """Generate AI-powered interview prep."""
    user_email = get_user_email(authorization)
    try:
        report = cache['reports'].get(request.match_report_id)
        if not report:
            report_doc = await db.reports.find_one({'id': request.match_report_id}, {'_id': 0})
            if report_doc:
                report = MatchReport(**report_doc)
        
        if not report:
            raise HTTPException(status_code=404, detail="Match report not found")
        
        # Generate prep
        prep = await generate_interview_prep(
            report,
            report.jd_title,
            user_email,
            provider=request.provider,
            api_key=request.api_key
        )
        
        cache['interview_preps'][prep.id] = prep
        await db.interview_preps.insert_one({
            **prep.model_dump(),
            'created_at': prep.created_at.isoformat()
        })
        
        return prep
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview prep failed: {str(e)}")

# ========== APPLICATION TRACKER ENDPOINTS ==========

@api_router.post("/applications", response_model=Application)
async def create_application(
    app_data: ApplicationCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new job application entry."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        application = Application(
            user_email=user_email,
            **app_data.model_dump()
        )
        
        await db.applications.insert_one({
            **application.model_dump(),
            'application_date': application.application_date.isoformat(),
            'updated_at': application.updated_at.isoformat()
        })
        
        # Update user's total applications
        await db.users.update_one(
            {'email': user_email},
            {'$inc': {'total_applications': 1}}
        )
        
        return application
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")

@api_router.get("/applications", response_model=List[Application])
async def get_applications(authorization: Optional[str] = Header(None)):
    """Get all applications for current user."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        return []
    
    try:
        apps_cursor = db.applications.find({'user_email': user_email}, {'_id': 0}).sort('application_date', -1)
        apps_docs = await apps_cursor.to_list(1000)
        return [Application(**doc) for doc in apps_docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")

@api_router.put("/applications/{app_id}", response_model=Application)
async def update_application(
    app_id: str,
    update_data: ApplicationUpdate,
    authorization: Optional[str] = Header(None)
):
    """Update an application."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Check ownership
        existing = await db.applications.find_one({'id': app_id, 'user_email': user_email}, {'_id': 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Application not found")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        if 'interview_date' in update_dict and update_dict['interview_date']:
            update_dict['interview_date'] = update_dict['interview_date'].isoformat()
        
        await db.applications.update_one(
            {'id': app_id, 'user_email': user_email},
            {'$set': update_dict}
        )
        
        updated_doc = await db.applications.find_one({'id': app_id}, {'_id': 0})
        return Application(**updated_doc)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update application: {str(e)}")

@api_router.delete("/applications/{app_id}")
async def delete_application(app_id: str, authorization: Optional[str] = Header(None)):
    """Delete an application."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    result = await db.applications.delete_one({'id': app_id, 'user_email': user_email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application deleted successfully"}

# ========== ANALYTICS ENDPOINTS ==========

@api_router.get("/analytics/success-rates")
async def get_success_rates(authorization: Optional[str] = Header(None)):
    """Get success rates by score threshold."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        return {"message": "Authentication required for analytics"}
    
    try:
        apps_cursor = db.applications.find({'user_email': user_email}, {'_id': 0})
        apps = await apps_cursor.to_list(1000)
        
        success_rates = calculate_success_rate_by_score_threshold(apps)
        return success_rates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

# ========== EXISTING ENDPOINTS (unchanged) ==========

@api_router.get("/")
async def root():
    return {
        "message": "CV-JD Matcher API - Premium Edition",
        "version": "2.0.0",
        "new_features": [
            "User authentication",
            "Application tracker",
            "Competitive analysis",
            "Interview prep (AI-powered)",
            "Success rate analytics"
        ]
    }

@api_router.get("/cvs")
async def list_cvs(authorization: Optional[str] = Header(None)):
    user_email = get_user_email(authorization)
    query = {} if user_email == 'anonymous' else {'user_email': user_email}
    cvs_cursor = db.cvs.find(query, {'_id': 0, 'raw_text': 0}).sort('uploaded_at', -1).limit(50)
    cvs_docs = await cvs_cursor.to_list(50)
    cvs_list = []
    for cv_doc in cvs_docs:
        cvs_list.append({
            'id': cv_doc['id'],
            'name': cv_doc['name'],
            'skills_count': len(cv_doc.get('skills', [])),
            'experiences_count': len(cv_doc.get('experiences', [])),
            'uploaded_at': cv_doc.get('uploaded_at', '')
        })
    return {"cvs": cvs_list}

@api_router.get("/jds")
async def list_jds(authorization: Optional[str] = Header(None)):
    user_email = get_user_email(authorization)
    query = {} if user_email == 'anonymous' else {'user_email': user_email}
    jds_cursor = db.jds.find(query, {'_id': 0, 'raw_text': 0}).sort('added_at', -1).limit(50)
    jds_docs = await jds_cursor.to_list(50)
    jds_list = []
    for jd_doc in jds_docs:
        jds_list.append({
            'id': jd_doc['id'],
            'title': jd_doc['title'],
            'company': jd_doc.get('company'),
            'requirements_count': len(jd_doc.get('requirements', [])),
            'added_at': jd_doc.get('added_at', '')
        })
    return {"jds": jds_list}

@api_router.get("/cv/{cv_id}")
async def get_cv(cv_id: str):
    cv = cache['cvs'].get(cv_id)
    if not cv:
        cv_doc = await db.cvs.find_one({'id': cv_id}, {'_id': 0})
        if cv_doc:
            return cv_doc
        raise HTTPException(status_code=404, detail="CV not found")
    return cv.model_dump()

@api_router.get("/jd/{jd_id}")
async def get_jd(jd_id: str):
    jd = cache['jds'].get(jd_id)
    if not jd:
        jd_doc = await db.jds.find_one({'id': jd_id}, {'_id': 0})
        if jd_doc:
            return jd_doc
        raise HTTPException(status_code=404, detail="JD not found")
    return jd.model_dump()

@api_router.get("/tailored/{tailored_id}")
async def get_tailored_cv(tailored_id: str):
    """Get tailored CV by ID."""
    tailored = cache['tailored_cvs'].get(tailored_id)
    if not tailored:
        tailored_doc = await db.tailored_cvs.find_one({'id': tailored_id}, {'_id': 0})
        if tailored_doc:
            tailored = TailoredCV(**tailored_doc)
            cache['tailored_cvs'][tailored_id] = tailored
        else:
            raise HTTPException(status_code=404, detail="Tailored CV not found")
    return tailored.model_dump()

@api_router.get("/tailored/{tailored_id}/download")
async def download_tailored_cv(tailored_id: str):
    tailored = cache['tailored_cvs'].get(tailored_id)
    if not tailored:
        tailored_doc = await db.tailored_cvs.find_one({'id': tailored_id}, {'_id': 0})
        if tailored_doc:
            tailored = TailoredCV(**tailored_doc)
        else:
            raise HTTPException(status_code=404, detail="Tailored CV not found")

    # Resolve JD title for the luxury formatter (best-effort)
    jd_title = None
    report = cache['reports'].get(tailored.match_report_id)
    if report:
        jd_title = getattr(report, 'jd_title', None)
        if not jd_title:
            jd = cache['jds'].get(report.jd_id)
            if jd:
                jd_title = jd.title

    text_content = format_luxury_cv(tailored.cv, jd_title=jd_title)
    safe_name = tailored.cv.name.replace(' ', '_').replace('/', '_')

    return Response(
        content=text_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=tailored_cv_{safe_name}.txt"}
    )

# ========== CSV EXPORT ENDPOINT ==========

@api_router.get("/applications/export/csv")
async def export_applications_csv(authorization: Optional[str] = Header(None)):
    """Export all applications to CSV."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        apps_cursor = db.applications.find({'user_email': user_email}, {'_id': 0}).sort('application_date', -1)
        apps = await apps_cursor.to_list(1000)
        
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Company', 'Position', 'Status', 'Match Score', 'Application Date',
            'Interview Date', 'Notes', 'Recruiter Name', 'Recruiter Email', 'Recruiter Phone'
        ])
        
        # Rows
        for app in apps:
            recruiter = app.get('recruiter', {})
            writer.writerow([
                app.get('company_name', ''),
                app.get('position', ''),
                app.get('status', ''),
                app.get('match_score', ''),
                app.get('application_date', '')[:10] if app.get('application_date') else '',
                app.get('interview_date', '')[:10] if app.get('interview_date') else '',
                app.get('notes', ''),
                recruiter.get('name', '') if recruiter else '',
                recruiter.get('email', '') if recruiter else '',
                recruiter.get('phone', '') if recruiter else ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications_export.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# ========== EMAIL NOTIFICATIONS ENDPOINTS ==========

@api_router.get("/notifications")
async def get_notifications(authorization: Optional[str] = Header(None)):
    """Get all notifications for user."""
    from src.schemas import EmailNotification
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        return []
    
    try:
        notifs_cursor = db.notifications.find({'user_email': user_email}, {'_id': 0}).sort('sent_at', -1).limit(50)
        notifs_docs = await notifs_cursor.to_list(50)
        return [EmailNotification(**doc) for doc in notifs_docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notifications: {str(e)}")

@api_router.post("/notifications/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str, authorization: Optional[str] = Header(None)):
    """Mark notification as read."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    await db.notifications.update_one(
        {'id': notification_id, 'user_email': user_email},
        {'$set': {'read': True}}
    )
    return {"message": "Notification marked as read"}

async def send_notification(user_email: str, subject: str, body: str, notification_type: str):
    """Helper to send notification."""
    from src.schemas import EmailNotification
    notification = EmailNotification(
        user_email=user_email,
        subject=subject,
        body=body,
        notification_type=notification_type
    )
    await db.notifications.insert_one({
        **notification.model_dump(),
        'sent_at': notification.sent_at.isoformat()
    })

# ========== RECRUITER/TEAM DASHBOARD ENDPOINTS ==========

@api_router.get("/recruiter/dashboard")
async def get_recruiter_dashboard(authorization: Optional[str] = Header(None)):
    """Get recruiter dashboard with KPIs."""
    from src.schemas import RecruiterDashboard
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if user is recruiter
    user = await db.users.find_one({'email': user_email}, {'_id': 0})
    if not user or user.get('role') != 'recruiter':
        raise HTTPException(status_code=403, detail="Recruiter access only")
    
    try:
        # Get all CVs from candidates
        total_candidates = await db.cvs.count_documents({})
        
        # Get all JDs from this recruiter
        active_positions = await db.jds.count_documents({'user_email': user_email})
        
        # Get applications with interview status
        interviews_scheduled = await db.applications.count_documents({'status': 'interview'})
        
        # Calculate average match score across all reports
        reports_cursor = db.reports.find({}, {'_id': 0, 'total_score': 1}).limit(1000)
        reports = await reports_cursor.to_list(1000)
        avg_score = sum(r.get('total_score', 0) for r in reports) / len(reports) if reports else 0
        
        # Get top candidates (high match scores)
        top_reports_cursor = db.reports.find({}, {'_id': 0}).sort('total_score', -1).limit(10)
        top_reports = await top_reports_cursor.to_list(10)
        
        top_candidates = []
        for report in top_reports:
            cv_doc = await db.cvs.find_one({'id': report.get('cv_id')}, {'_id': 0})
            if cv_doc:
                top_candidates.append({
                    'name': cv_doc.get('name'),
                    'score': report.get('total_score'),
                    'jd_title': report.get('jd_title'),
                    'cv_id': cv_doc.get('id')
                })
        
        dashboard = RecruiterDashboard(
            total_candidates=total_candidates,
            active_positions=active_positions,
            interviews_scheduled=interviews_scheduled,
            avg_match_score=round(avg_score, 1),
            top_candidates=top_candidates
        )
        
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")

@api_router.get("/recruiter/candidates")
async def get_all_candidates(
    min_score: Optional[float] = 0,
    authorization: Optional[str] = Header(None)
):
    """Get all candidates with filtering."""
    user_email = get_user_email(authorization)
    if user_email == 'anonymous':
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = await db.users.find_one({'email': user_email}, {'_id': 0})
    if not user or user.get('role') != 'recruiter':
        raise HTTPException(status_code=403, detail="Recruiter access only")
    
    try:
        # Get all match reports with scores above threshold
        reports_cursor = db.reports.find(
            {'total_score': {'$gte': min_score}},
            {'_id': 0}
        ).sort('total_score', -1).limit(100)
        reports = await reports_cursor.to_list(100)
        
        candidates = []
        for report in reports:
            cv_doc = await db.cvs.find_one({'id': report.get('cv_id')}, {'_id': 0})
            if cv_doc:
                candidates.append({
                    'cv_id': cv_doc.get('id'),
                    'name': cv_doc.get('name'),
                    'skills': cv_doc.get('skills', [])[:10],
                    'match_score': report.get('total_score'),
                    'jd_title': report.get('jd_title'),
                    'report_id': report.get('id')
                })
        
        return {"candidates": candidates, "count": len(candidates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidates: {str(e)}")

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

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
