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
    modifications: List[str] = Field(default_factory=list, description="List of modifications made")
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal["deterministic", "openai", "anthropic", "gemini", "huggingface"]
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000

# User Authentication
class User(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))
    total_applications: int = 0

class UserCreate(BaseModel):
    email: EmailStr
    name: str

# Application Tracker
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
    updated_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))

class ApplicationCreate(BaseModel):
    company_name: str
    position: str
    jd_id: Optional[str] = None
    cv_id: Optional[str] = None
    match_score: Optional[float] = None
    status: str = "applied"
    notes: str = ""

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None

# Analytics & Benchmarks
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

# Interview Prep
class InterviewPrepSuggestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    gap: str
    question: str
    suggested_answer_approach: str
    resources: List[str]

class InterviewPrep(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    user_email: str
    match_report_id: str
    jd_title: str
    behavioral_questions: List[str]
    technical_questions: List[str]
    gap_based_suggestions: List[InterviewPrepSuggestion]
    created_at: datetime = Field(default_factory=lambda: datetime.now(__import__('datetime').timezone.utc))
