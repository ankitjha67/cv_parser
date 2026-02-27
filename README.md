# CV-JD Matcher: Production-Grade Resume Matching System

## 🎯 Overview

A **luxury, zero-hallucination** CV ↔ JD matching, gap analysis, and resume rewrite system. Every rewritten bullet is traceable to original CV evidence. Works 100% offline (deterministic baseline) with optional LLM enhancement (OpenAI/Claude/Gemini/HuggingFace).

### Key Features

✅ **Zero Hallucinations** - Every claim traced to source spans  
✅ **ATS-Grade Scoring** - Explainable weighted scores (Skills 35%, Experience 30%, etc.)  
✅ **Multi-JD Support** - Process N job descriptions in batch  
✅ **LLM Optional** - Deterministic baseline works fully offline  
✅ **Evidence Mapping** - Track modifications back to original CV  
✅ **Web UI + CLI** - Luxury React frontend + Python CLI  
✅ **All LLM Providers** - OpenAI, Anthropic, Gemini, HuggingFace adapters  

---

## 🚀 Quick Start

### 1. Web Application (Recommended)

The app is already deployed and running:

**URL:** https://gpt-pure-python.preview.emergentagent.com/

1. **Upload CV** - Drop your resume (PDF/DOCX/TXT)
2. **Add JDs** - Paste one or more job descriptions
3. **Run Match** - Get ATS score + gap analysis
4. **Generate Tailored CV** - Choose provider (deterministic or LLM)
5. **Download** - Get your truthful, JD-aligned resume

### 2. CLI Usage (Local)

```bash
# Navigate to backend
cd /app/backend

# Match single CV against JD
python cli.py match data/sample_cv.txt data/jd_backend.txt

# Batch mode: match CV against multiple JDs
python cli.py batch data/sample_cv.txt data/ -o ./results

# With LLM provider (requires API key)
python cli.py match cv.pdf jd.txt --provider openai --api-key sk-...
```

---

## 📚 API Documentation

### Base URL

```
https://gpt-pure-python.preview.emergentagent.com/api
```

### Endpoints

#### 1. Upload CV

```bash
POST /api/cv/upload
Content-Type: multipart/form-data

# Response
{
  "cv_id": "uuid",
  "name": "John Doe",
  "message": "CV uploaded successfully. Found 3 experiences and 25 skills."
}
```

#### 2. Add Job Description

```bash
POST /api/jd/add
Content-Type: application/json

{
  "title": "Senior Backend Engineer",
  "text": "<full JD text>"
}

# Response
{
  "jd_id": "uuid",
  "title": "Senior Backend Engineer",
  "message": "JD added successfully. Extracted 15 requirements."
}
```

#### 3. Run Match

```bash
POST /api/match
Content-Type: application/json

{
  "cv_id": "uuid",
  "jd_id": "uuid"
}

# Response
{
  "report": {
    "total_score": 82.4,
    "category_scores": {
      "skills": 28.5,
      "experience": 25.0,
      "tenure": 12.0,
      "education": 9.0,
      "keywords": 7.9
    },
    "hard_gaps": ["Missing: Kubernetes"],
    "soft_gaps": ["Skill mentioned but not highlighted: Docker"],
    "evidences": [...]
  }
}
```

#### 4. Generate Tailored CV

```bash
POST /api/rewrite
Content-Type: application/json

{
  "match_report_id": "uuid",
  "provider": "deterministic",  # or openai, anthropic, gemini, huggingface
  "model": "gpt-5.2",  # optional
  "api_key": "sk-..."  # optional (uses EMERGENT_LLM_KEY by default)
}

# Response
{
  "tailored_cv_id": "uuid",
  "message": "Tailored CV generated successfully with 12 modifications"
}
```

#### 5. Download Tailored CV

```bash
GET /api/tailored/{tailored_cv_id}/download

# Returns: text/plain file
```

---

## 🎨 Luxury Design System

Our frontend follows **The Editor's Desk** aesthetic:

- **Typography:** Playfair Display (headings), Manrope (body), JetBrains Mono (data)
- **Colors:** Deep Emerald (#1A4D3D) + Burnt Sienna (#E85D30) accents
- **Layout:** Swiss editorial with sharp edges (0px border-radius)
- **Grid:** Tetris grid (landing), Bento grid (dashboard)
- **Feel:** Magazine-quality precision with automotive luxury

---

## 🧠 How It Works

### 1. Ingestion

Supports PDF, DOCX, TXT via `pypdf2` and `python-docx`. Clean text normalization.

### 2. Parsing (Deterministic)

- **CV:** Regex + heuristics to extract sections (Summary, Experience, Skills, Education)
- **JD:** Extract requirements, keywords, categorize (skills/experience/education/certs/tools)
- **Evidence tracking:** Every bullet gets a unique ID + character span

### 3. ATS Scoring

Weighted categories:

| Category | Weight | Method |
|----------|--------|--------|
| Skills | 35% | TF-IDF cosine + exact matches |
| Experience | 30% | Keyword overlap + role/title match |
| Tenure | 15% | Years extraction + ratio scoring |
| Education | 10% | Degree level matching |
| Keywords | 10% | Jaccard similarity with evidence |

### 4. Gap Analysis

- **Hard Gaps:** Completely missing required items
- **Soft Gaps:** Mentioned but not evidenced clearly

### 5. Truthful Rewrite

**Deterministic Mode:**
- Reorder bullets by JD relevance
- Apply action verb mapping (20+ verbs)
- Preserve all evidence
- NO new facts

**LLM Mode (Optional):**
- Use OpenAI/Claude/Gemini for bullet rephrasing
- Post-factuality gate: reject any hallucinations
- Fallback to deterministic if LLM fails

---

## 🔑 LLM Provider Configuration

### Emergent LLM Key (Universal Key)

A **universal key** is pre-configured in the backend:

```
EMERGENT_LLM_KEY=<set-in-environment>
```

This single key works for:
- OpenAI (gpt-5.2, gpt-4o, etc.)
- Anthropic (claude-4-sonnet-20250514, etc.)
- Google Gemini (gemini-2.5-pro, gemini-3-flash-preview)

You can override it in **Settings** with your own keys.

### Provider Details

| Provider | Models | Key Source |
|----------|--------|------------|
| Deterministic | N/A | None (offline) |
| OpenAI | gpt-5.2, gpt-5.1, gpt-4o | EMERGENT_LLM_KEY or OPENAI_API_KEY |
| Anthropic | claude-4-sonnet, claude-opus-4-5 | EMERGENT_LLM_KEY or ANTHROPIC_API_KEY |
| Gemini | gemini-2.5-pro, gemini-3-flash | EMERGENT_LLM_KEY or GEMINI_API_KEY |
| HuggingFace | gpt2, etc. | None (local) |

---

## 📊 Architecture

```
/app/
├── backend/
│   ├── server.py           # FastAPI server
│   ├── cli.py              # CLI tool
│   ├── src/
│   │   ├── schemas.py       # Pydantic models
│   │   ├── ingestion.py     # PDF/DOCX parser
│   │   ├── parser.py        # CV + JD extraction
│   │   ├── scorer.py        # ATS scoring
│   │   ├── gap_analyzer.py  # Gap detection
│   │   ├── rewriter.py      # Deterministic + LLM rewrite
│   │   └── llm/             # Provider adapters
│   │       ├── base.py
│   │       ├── deterministic.py
│   │       ├── openai_adapter.py
│   │       ├── anthropic_adapter.py
│   │       ├── gemini_adapter.py
│   │       └── hf_adapter.py
│   └── data/
│       ├── sample_cv.txt
│       ├── jd_backend.txt
│       └── jd_ml.txt
│
└── frontend/
    ├── src/
    │   ├── App.js           # Main app
    │   ├── pages/
    │   │   ├── Landing.js    # Hero + features
    │   │   ├── Upload.js     # CV + JD input
    │   │   ├── Dashboard.js  # Match results
    │   │   └── Settings.js   # API keys
    │   └── index.css        # Luxury design system
    └── package.json
```

---

## ⚙️ Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **MongoDB** - Document storage (CVs, JDs, reports)
- **spaCy** - NLP (NER, phrase matching)
- **scikit-learn** - TF-IDF vectorization, cosine similarity
- **PyPDF2, python-docx** - Document parsing
- **emergentintegrations** - Unified LLM client (OpenAI/Claude/Gemini)

### Frontend
- **React** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icons
- **Tailwind CSS** - Utility-first styling
- **Custom Design System** - Luxury editorial theme

---

## 🧪 Testing

### Test with Sample Data

```bash
# Backend API test
API_URL=https://gpt-pure-python.preview.emergentagent.com/api

# 1. Upload sample CV
curl -X POST "$API_URL/cv/upload" \
  -F "file=@/app/backend/data/sample_cv.txt"

# 2. Add sample JD
curl -X POST "$API_URL/jd/add" \
  -H "Content-Type: application/json" \
  -d '{"title": "Backend Engineer", "text": "..."}'

# 3. Run match
curl -X POST "$API_URL/match" \
  -H "Content-Type: application/json" \
  -d '{"cv_id": "<cv_id>", "jd_id": "<jd_id>"}'
```

### CLI Test

```bash
cd /app/backend
python cli.py match data/sample_cv.txt data/jd_backend.txt -o ./test_output
```

---

## 📌 Environment Variables

### Backend (.env)

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=<set-in-environment>

# Optional: Override with your own keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=https://gpt-pure-python.preview.emergentagent.com
```

---

## 🛡️ Zero-Hallucination Guarantee

Our system enforces factuality through:

1. **Evidence Tracking:** Every bullet has a unique ID + character span in original CV
2. **Deterministic Baseline:** Regex + templates can't invent facts
3. **LLM Factuality Gate:** Post-processing checks that rewritten bullets contain only original entities/metrics
4. **Fallback:** If LLM hallucinates, we automatically downgrade to deterministic
5. **Metric Lockdown:** Numbers extracted from original, never generated

**Example:**

```
Original: "Improved API response time by optimizing database queries"
✓ Valid rewrite: "Optimized database queries to improve API response time"
✗ Hallucination: "Improved API response time by 40% through query optimization"
                  ^ invented metric
```

---

## 🚀 Production Deployment

The system is designed for both:

1. **Emergent Platform** (current) - React + FastAPI + MongoDB stack
2. **Standalone Local** - CLI tool with optional Streamlit UI

For production:

- Add rate limiting on API endpoints
- Implement user authentication (JWT)
- Use Redis for caching instead of in-memory dict
- Add vector DB (Chroma/Pinecone) for semantic search
- Deploy LLM calls as background tasks (Celery)

---

## 📝 Sample Output

### Match Report (CLI)

```
ATS Score: 82.4/100

Category Breakdown:
┏━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Category  ┃ Score  ┃ Weight ┃
┡━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ Skills    │ 28.5   │ 35%    │
│ Experience│ 25.0   │ 30%    │
│ Tenure    │ 12.0   │ 15%    │
│ Education │ 9.0    │ 10%    │
│ Keywords  │ 7.9    │ 10%    │
└━━━━━━━━━━━┴━━━━━━━━┴━━━━━━━━┘

Hard Gaps (1):
  • Missing: Kubernetes

Soft Gaps (3):
  • Skill mentioned but not highlighted: Redis
  • Tool/technology not mentioned: Terraform
  • Keyword not present: GitOps
```

---

## 🌟 Next Enhancements

- [ ] LiteLLM integration for unified provider interface
- [ ] Vector DB (Chroma) for semantic skill matching
- [ ] Train tiny karpathy-style GPT on resume corpus
- [ ] Web scraping for JDs from job boards (LinkedIn, Indeed)
- [ ] Batch comparison dashboard (compare CV vs 10 JDs)
- [ ] Email integration (send tailored CVs directly)
- [ ] PDF generation for tailored CVs with luxury styling

---

## 👥 Credits

Inspired by:
- **@karpathy's minGPT** - Pure Python transformer reference
- **Emergent LLM integrations** - Universal key for seamless LLM access
- **Swiss editorial design** - For the luxury UI aesthetic

---

## 📜 License

MIT License - Built for Emergent platform

---

**Built with precision. Zero hallucinations. Luxury execution.**

💎 cv-jd-matcher v1.0.0
