from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Dict, Optional, Literal
from datetime import datetime

class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    original_text: str
    start: int
    end: int
    bullet_id: str = Field(..., description="traceable ID")

class Experience(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: str
    company: str
    dates: str
    bullets: List[str]
    evidence_map: Dict[str, Evidence] = Field(default_factory=dict)

class CV(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str = "anonymous"
    name: str
    summary: Optional[str] = None
    experiences: List[Experience]
    skills: List[str]
    education: List[Dict[str, str]]
    raw_text: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class JDRequirement(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str
    category: Literal["skills", "experience", "education", "certs", "tools", "responsibilities"]
    required: bool = True
    min_years: Optional[int] = None

class JD(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str = "anonymous"
    title: str
    company: Optional[str] = None
    requirements: List[JDRequirement]
    keywords: List[str]
    raw_text: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class MatchEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cv_text: str
    jd_text: str
    similarity: float
    category: str

class MatchReport(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str = "anonymous"
    cv_id: str
    jd_id: str
    cv_name: str
    jd_title: str
    total_score: float = Field(..., ge=0, le=100)
    category_scores: Dict[str, float]
    evidences: List[MatchEvidence]
    hard_gaps: List[str]
    soft_gaps: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class TailoredCV(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str = "anonymous"
    match_report_id: str
    cv: CV
    modifications: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal["deterministic", "openai", "anthropic", "gemini", "huggingface", "ollama", "local"]
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000

class User(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    name: str
    role: Literal["candidate", "recruiter", "admin"] = "candidate"
    company: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))
    total_applications: int = 0

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    role: str = "candidate"
    company: Optional[str] = None
    phone: Optional[str] = None

class RecruiterDetails(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: str

class Application(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str
    company_name: str
    position: str
    jd_id: Optional[str] = None
    cv_id: Optional[str] = None
    match_score: Optional[float] = None
    status: Literal["applied", "screening", "interview", "offer", "rejected", "accepted", "withdrawn"] = "applied"
    application_date: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))
    notes: str = ""
    interview_date: Optional[datetime] = None
    recruiter: Optional[RecruiterDetails] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class ApplicationCreate(BaseModel):
    company_name: str
    position: str
    jd_id: Optional[str] = None
    cv_id: Optional[str] = None
    match_score: Optional[float] = None
    status: str = "applied"
    notes: str = ""
    recruiter: Optional[RecruiterDetails] = None

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    recruiter: Optional[RecruiterDetails] = None

class IndustryBenchmark(BaseModel):
    model_config = ConfigDict(extra='forbid')
    industry: str
    avg_score: float
    top_10_percentile: float
    top_25_percentile: float
    median_score: float
    sample_size: int

class CompetitiveAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_score: float
    percentile_rank: float
    better_than_percent: float
    industry_avg: float
    gap_to_top_10: float
    strengths: List[str]
    improvement_areas: List[str]

class InterviewQuestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str
    sample_answer: str
    difficulty: Literal["easy", "medium", "hard"]
    category: Literal["behavioral", "technical", "situational"]
    tips: List[str] = Field(default_factory=list)

class InterviewPrepSuggestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    gap: str
    question: str
    suggested_answer_approach: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    resources: List[str]

class InterviewPrep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str
    match_report_id: str
    jd_title: str
    questions: List[InterviewQuestion]
    gap_based_suggestions: List[InterviewPrepSuggestion]
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class EmailNotification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str
    subject: str
    body: str
    notification_type: Literal["status_change", "interview_reminder", "new_match", "system"]
    sent_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))
    read: bool = False

class RecruiterDashboard(BaseModel):
    model_config = ConfigDict(extra='forbid')
    total_candidates: int
    active_positions: int
    interviews_scheduled: int
    avg_match_score: float
    top_candidates: List[Dict]


class Comment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    application_id: str
    user_email: str
    user_name: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))


class CommentCreate(BaseModel):
    text: str
    user_name: str = "Recruiter"


class InterviewSlot(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    application_id: str
    recruiter_email: str
    candidate_email: str
    candidate_name: str
    position: str
    company: str
    scheduled_at: datetime
    duration_minutes: int = 60
    location: str = ""
    meeting_link: str = ""
    notes: str = ""
    status: Literal["scheduled", "completed", "cancelled"] = "scheduled"
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))


class InterviewSlotCreate(BaseModel):
    application_id: str
    candidate_email: str
    candidate_name: str
    position: str
    company: str
    scheduled_at: datetime
    duration_minutes: int = 60
    location: str = ""
    meeting_link: str = ""
    notes: str = ""


class AnalyticsDashboard(BaseModel):
    model_config = ConfigDict(extra='forbid')
    total_applications: int
    total_interviews: int
    total_offers: int
    avg_match_score: float
    score_distribution: List[Dict]       # [{range, count}]
    success_by_score: List[Dict]         # [{range, rate}]
    status_breakdown: Dict[str, int]     # {status: count}
    applications_over_time: List[Dict]   # [{date, count}]
    top_companies: List[Dict]            # [{company, count, avg_score}]
