# CV-JD Matcher - Product Requirements Document

## Overview
A production-grade CV-to-Job-Description matching system with ATS-like scoring, gap analysis, and CV tailoring capabilities.

## Core Features
- **CV Ingestion**: Upload PDF/DOCX/TXT files with automatic parsing
- **JD Management**: Add job descriptions via text input with requirement extraction
- **ATS Scoring**: Score CVs against JDs with category breakdown (Skills, Experience, Tenure, Education, Keywords)
- **Gap Analysis**: Identify missing skills, keywords, and experience gaps
- **CV Tailoring**: Rewrite CVs for specific JDs without hallucinating facts (deterministic baseline)
- **Multi-JD Matching**: Match one CV against multiple JDs simultaneously

## Premium Features
- **User Authentication**: Email-based registration for data privacy
- **Application Tracker**: Track job applications with status, company, recruiter details
- **Competitive Analysis**: Compare scores against aggregate data
- **Industry Benchmarks**: Percentile rankings and industry averages
- **CSV Export**: Export application data

## Technical Architecture
- **Backend**: FastAPI + MongoDB + Python (spaCy, scikit-learn)
- **Frontend**: React + Tailwind CSS + shadcn/ui
- **LLM Strategy**: Deterministic baseline with pluggable LLM adapters (OpenAI, Anthropic, Gemini, etc.)

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cv/upload` | POST | Upload CV file |
| `/api/jd/add` | POST | Add JD text |
| `/api/match` | POST | Run CV-JD matching |
| `/api/rewrite` | POST | Generate tailored CV |
| `/api/tailored/{id}` | GET | Get tailored CV data |
| `/api/tailored/{id}/download` | GET | Download tailored CV |
| `/api/auth/register` | POST | User registration |
| `/api/applications` | GET/POST | Application tracker |

## Completed (Feb 27, 2026)
- [x] Full CV/JD upload and parsing pipeline
- [x] ATS scoring with 5 categories
- [x] Gap analysis (hard/soft gaps)
- [x] Deterministic CV rewriting
- [x] Multi-JD batch matching
- [x] User authentication
- [x] Application tracker with CRUD
- [x] CSV export
- [x] Frontend dashboard with Match All / Generate All
- [x] Competitive analysis & industry benchmarks
- [x] Fixed P0 bug: Missing `/api/tailored/{id}` endpoint
- [x] Fixed P1 bug: PDF name extraction (now extracts "Ankit Kumar" correctly)
- [x] 25/25 backend tests passing

## Backlog
- [ ] Email notification system (SendGrid/Resend integration)
- [ ] Interview prep AI suggestions
- [ ] Recruiter dashboard features
- [ ] Vector DB for skill taxonomy (Chroma)
- [ ] Tiny GPT model for ultra-light local rewrite

## Test Credentials
- Test URL: https://gpt-pure-python.preview.emergentagent.com
- Test files: `/app/backend/data/Ankit_Kumar.pdf`, `/app/backend/data/Financial_JD.pdf`
