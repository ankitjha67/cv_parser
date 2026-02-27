import re
import spacy
from typing import List, Dict, Tuple
from src.schemas import CV, JD, Experience, JDRequirement, Evidence
import uuid

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Verb mapping for action-oriented rewriting
VERB_MAP = {
    'developed': 'built', 'created': 'designed', 'made': 'engineered',
    'worked': 'collaborated', 'helped': 'assisted', 'did': 'executed',
    'managed': 'led', 'handled': 'coordinated', 'was': 'served',
    'implemented': 'deployed', 'wrote': 'authored', 'built': 'architected',
    'designed': 'engineered', 'maintained': 'sustained', 'improved': 'optimized',
    'increased': 'accelerated', 'reduced': 'minimized', 'led': 'directed',
    'coordinated': 'orchestrated', 'assisted': 'supported', 'conducted': 'executed'
}

# Common skills taxonomy
SKILLS_TAXONOMY = [
    # Programming
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Ruby', 'PHP',
    # Frameworks
    'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring', 'Express',
    # Databases
    'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'SQL', 'NoSQL',
    # Cloud & DevOps
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git', 'Linux',
    # Data & ML
    'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy', 'NLP', 'Computer Vision',
    'Machine Learning', 'Deep Learning', 'Data Science', 'AI', 'ML', 'ETL', 'Spark',
    # API & Architecture
    'REST API', 'GraphQL', 'Microservices',
    # Methodologies
    'Agile', 'Scrum', 'DevOps', 'Testing', 'Lean Six Sigma',
    # Finance & Banking
    'OFSAA', 'BASEL', 'Credit Risk', 'Risk Management', 'Financial Modeling',
    'Regulatory Reporting', 'IBM SPSS', 'SAS', 'Bloomberg', 'RWA',
    # Business & Product
    'Business Analysis', 'Product Management', 'JIRA', 'ARIS', 'Balsamiq',
    'Data Analytics', 'Tableau', 'Power BI', 'Excel',
]

def parse_cv(text: str) -> CV:
    """
    Parse CV text into structured CV object with evidence tracking.
    Uses deterministic methods (regex + heuristics).
    """
    # Extract sections
    sections = _extract_sections(text)
    
    # Extract name (first non-empty line usually)
    name = _extract_name(text)
    
    # Extract summary
    summary = sections.get('summary', None)
    
    # Extract experiences with evidence
    experiences = _extract_experiences(text, sections.get('experience', ''))
    
    # Extract skills
    skills = _extract_skills(text)
    
    # Extract education
    education = _extract_education(sections.get('education', ''))
    
    return CV(
        name=name,
        summary=summary,
        experiences=experiences,
        skills=skills,
        education=education,
        raw_text=text
    )

def parse_jd(text: str) -> JD:
    """
    Parse Job Description into structured JD object.
    """
    # Extract title (usually first line or contains "position", "role", "job")
    title = _extract_jd_title(text)
    
    # Extract company (optional)
    company = _extract_company(text)
    
    # Extract requirements
    requirements = _extract_requirements(text)
    
    # Extract keywords
    keywords = _extract_keywords(text)
    
    return JD(
        title=title,
        company=company,
        requirements=requirements,
        keywords=keywords,
        raw_text=text
    )

def _extract_sections(text: str) -> Dict[str, str]:
    """Extract major sections from CV using regex patterns."""
    sections = {}
    
    # Common section headers
    patterns = {
        'summary': r'(?i)(summary|profile|about|objective)[:\s]*([\s\S]*?)(?=\n\s*(?:experience|education|skills|projects|work|employment)|$)',
        'experience': r'(?i)(experience|employment|work history)[:\s]*([\s\S]*?)(?=\n\s*(?:education|skills|projects|certifications)|$)',
        'education': r'(?i)(education|academic|qualifications)[:\s]*([\s\S]*?)(?=\n\s*(?:skills|projects|certifications|experience)|$)',
        'skills': r'(?i)(skills|technical skills|technologies|expertise)[:\s]*([\s\S]*?)(?=\n\s*(?:education|projects|certifications|experience)|$)',
    }
    
    for section_name, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[section_name] = match.group(2).strip()
    
    return sections

def _extract_name(text: str) -> str:
    """Extract candidate name — typically one of the first few lines before section headers."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    section_re = re.compile(
        r'^(EXPERIENCE|EDUCATION|SKILLS|SUMMARY|PROFILE|WORK|EMPLOYMENT|'
        r'CERTIFICATIONS|PROJECTS|CONTACT|REFERENCES|OBJECTIVE|PROFESSIONAL|'
        r'ACHIEVEMENTS|AWARDS|LANGUAGES|INTERESTS)',
        re.IGNORECASE
    )
    contact_re = re.compile(r'[@|\d\|•]')

    for line in lines[:10]:
        if section_re.match(line):
            continue
        if contact_re.search(line):
            continue
        if len(line) > 60:
            continue
        words = line.split()
        # Name: 2-5 words, each starting with a capital letter
        if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w and w[0].isalpha()):
            return line.title() if line.isupper() else line

    # Regex fallback: look for a clean "Firstname Lastname" pattern
    for line in lines[:6]:
        if section_re.match(line) or contact_re.search(line):
            continue
        m = re.match(r'^([A-Z][A-Za-z-]+(?:\s+[A-Z][A-Za-z-]+){1,3})\s*$', line)
        if m:
            return m.group(1)

    return "Unknown"

def _extract_experiences(full_text: str, exp_text: str) -> List[Experience]:
    """Extract work experiences using date ranges as anchors, with a pattern fallback."""
    experiences = []

    # --- Strategy 1: date-range anchoring (most reliable) ---
    month_re = (r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?'
                r'|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
                r'\s+\d{4}')
    date_range_re = re.compile(
        fr'({month_re})\s*[-–\s]+\s*({month_re}|Present|Current|Till\s*Date)',
        re.IGNORECASE
    )
    date_matches = list(date_range_re.finditer(exp_text))

    if date_matches:
        for i, dm in enumerate(date_matches):
            date_str = _clean_dates(dm.group(0))

            # Header: text before date (up to 300 chars, but not past previous date end)
            look_back = max(0, dm.start() - 300)
            if i > 0:
                look_back = max(look_back, date_matches[i - 1].end())
            header_text = exp_text[look_back:dm.start()].strip()

            # Body: text after date up to next date match
            next_anchor = date_matches[i + 1].start() if i + 1 < len(date_matches) else len(exp_text)
            body_text = exp_text[dm.end():next_anchor]

            role, company = _parse_role_company(header_text)
            bullets = _extract_bullets(body_text, full_text)

            experiences.append(Experience(
                role=role or "Professional",
                company=company or "Organisation",
                dates=date_str,
                bullets=[b['text'] for b in bullets],
                evidence_map={b['text']: b['evidence'] for b in bullets}
            ))
        return experiences

    # --- Strategy 2: strict keyword pattern fallback ---
    job_pattern = (r'([A-Z][\w\s]+(?:Engineer|Developer|Manager|Analyst|Scientist|Designer'
                   r'|Consultant|Lead|Director|Specialist))[,\s]+'
                   r'([A-Z][\w\s&.]+)[,\s]+'
                   r'(\w+\s+\d{4}\s*[-–]\s*(?:\w+\s+\d{4}|Present|Current))')
    matches = list(re.finditer(job_pattern, exp_text, re.MULTILINE))

    if not matches:
        bullets = _extract_bullets(exp_text, full_text)
        if bullets:
            experiences.append(Experience(
                role="Professional",
                company="Previous Employer",
                dates="",
                bullets=[b['text'] for b in bullets],
                evidence_map={b['text']: b['evidence'] for b in bullets}
            ))
    else:
        for i, match in enumerate(matches):
            role = match.group(1).strip()
            company = match.group(2).strip()
            dates = match.group(3).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(exp_text)
            bullets = _extract_bullets(exp_text[start_pos:end_pos], full_text)
            experiences.append(Experience(
                role=role,
                company=company,
                dates=dates,
                bullets=[b['text'] for b in bullets] if bullets else [],
                evidence_map={b['text']: b['evidence'] for b in bullets} if bullets else {}
            ))

    return experiences


def _parse_role_company(text: str) -> Tuple[str, str]:
    """Extract role title and company name from the header segment before a date range."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return '', ''

    role_re = re.compile(
        r'(?:Engineer|Developer|Manager|Analyst|Scientist|Designer|Consultant|'
        r'Lead|Director|Specialist|Officer|Head|VP|President|Executive|Associate|'
        r'Intern|Trainee|Banker|Advisor|Administrator|Coordinator)',
        re.IGNORECASE
    )
    company_re = re.compile(
        r'(?:LLP|Ltd|LLC|Inc|Pvt|Bank|Corp|Group|Solutions|Services|Finance|'
        r'Institute|Technologies|Systems|Consulting|Partners)',
        re.IGNORECASE
    )
    city_re = re.compile(
        r'\s+(?:Mumbai|Delhi|Chennai|Bangalore|Hyderabad|Pune|Kolkata|Noida|Gurugram|Gurgaon)\s*$',
        re.IGNORECASE
    )

    role = ''
    company = ''
    for line in reversed(lines):
        if role_re.search(line) and not role:
            role = line.strip()
        if company_re.search(line) and not company:
            company = city_re.sub('', line).strip()

    if not company and lines:
        company = city_re.sub('', lines[0]).strip()
    if not role and len(lines) > 1:
        role = lines[-1]
    elif not role and lines:
        role = lines[0]

    return role, company

def _extract_bullets(text: str, full_text: str) -> List[Dict]:
    """Extract bullet points with evidence tracking."""
    bullets = []
    
    # Match bullet points (•, -, *, etc.)
    bullet_pattern = r'[•●○◦▪▫⁃‣⦿⦾\-\*]\s*(.+?)(?=\n[•●○◦▪▫⁃‣⦿⦾\-\*]|\n\n|$)'
    matches = re.finditer(bullet_pattern, text, re.DOTALL)
    
    for i, match in enumerate(matches):
        bullet_text = match.group(1).strip()
        if len(bullet_text) > 10:  # Filter out too short bullets
            # Find position in full text
            start = full_text.find(bullet_text)
            if start == -1:
                start = 0  # Fallback
            end = start + len(bullet_text)
            
            evidence = Evidence(
                original_text=bullet_text,
                start=start,
                end=end,
                bullet_id=f"b{i}_{uuid.uuid4().hex[:8]}"
            )
            bullets.append({
                'text': bullet_text,
                'evidence': evidence
            })
    
    return bullets

def _extract_skills(text: str) -> List[str]:
    """Extract skills using taxonomy matching and NER."""
    skills = set()
    
    # Match against taxonomy
    text_lower = text.lower()
    for skill in SKILLS_TAXONOMY:
        if skill.lower() in text_lower:
            skills.add(skill)
    
    # Extract from skills section specifically
    skills_match = re.search(r'(?i)skills[:\s]*([\s\S]*?)(?=\n\s*(?:education|experience|projects)|$)', text)
    if skills_match:
        skills_text = skills_match.group(1)
        # Split by common delimiters
        tokens = re.split(r'[,;\n|•●]', skills_text)
        for token in tokens:
            token = token.strip()
            if token and 2 < len(token) < 30:
                skills.add(token)
    
    return sorted(list(skills))

def _expand_degree(abbrev: str) -> str:
    """Expand degree abbreviations to full names."""
    mapping = {
        'MA': 'Master of Arts',
        'MS': 'Master of Science',
        'MSC': 'Master of Science',
        'MBA': 'Master of Business Administration',
        'BA': 'Bachelor of Arts',
        'BS': 'Bachelor of Science',
        'BSC': 'Bachelor of Science',
        'BTECH': 'Bachelor of Technology',
        'MTECH': 'Master of Technology',
        'PHD': 'Doctor of Philosophy',
        'MCA': 'Master of Computer Applications',
        'BCA': 'Bachelor of Computer Applications',
        'PGDM': 'Post Graduate Diploma in Management',
        'MCOM': 'Master of Commerce',
        'BCOM': 'Bachelor of Commerce',
        'BE': 'Bachelor of Engineering',
        'ME': 'Master of Engineering',
    }
    normalised = re.sub(r'[\s.]', '', abbrev).upper()
    for key, val in mapping.items():
        if re.sub(r'[\s.]', '', key).upper() == normalised:
            return val
    return abbrev  # Return as-is if no match found


def _extract_education(edu_text: str) -> List[Dict[str, str]]:
    """Extract education entries — handles full names and common abbreviations."""
    education = []
    if not edu_text.strip():
        return education

    seen_entries: set = set()  # (normalised_degree, year)

    # Strategy 1: full degree name + optional institution + optional year
    full_pattern = re.compile(
        r'(Post\s*Graduate[^,\n]*|PGDM[^,\n]*|MBA[^,\n]*|MCA[^,\n]*|BCA[^,\n]*|'
        r'B\.?\s*Tech[^,\n]*|M\.?\s*Tech[^,\n]*|Bachelor[^,\n]*|Master[^,\n]*|'
        r'Doctorate[^,\n]*|Ph\.?\s*D\.?[^,\n]*|B\.?E\.?[^,\n]*|M\.?E\.?[^,\n]*|'
        r'B\.?S\.?[^,\n]{0,30}|M\.?S\.?[^,\n]{0,30}|B\.?A\.?[^,\n]{0,30}|M\.?A\.?[^,\n]{0,30})'
        r'(?:[,\s]+([A-Z][A-Za-z\s&]+(?:University|Institute|College|School|IIT|IIM)[A-Za-z\s]*))?'
        r'[,\s]*(?:.*?(\d{4}))?',
        re.IGNORECASE
    )
    for m in full_pattern.finditer(edu_text):
        degree_raw = (m.group(1) or '').strip()
        institution = (m.group(2) or '').strip()
        year = m.group(3) or ''
        if not degree_raw:
            continue
        degree = _expand_degree(degree_raw)
        key = (degree.lower()[:20], year)
        if key not in seen_entries:
            seen_entries.add(key)
            education.append({'degree': degree, 'institution': institution, 'year': year})

    # Strategy 2: abbreviated degree + optional month + year  e.g. "Ma - August (2021)"
    if not education:
        abbrev_re = re.compile(
            r'\b(ma|ms|mba|bsc|ba|bs|msc|btech|mtech|phd|mca|bca|pgdm|mcom|bcom|be|me)\b'
            r'[\s\-–]*(?:\w+\s+)?\(?(\d{4})\)?',
            re.IGNORECASE
        )
        for m in abbrev_re.finditer(edu_text):
            year = m.group(2)
            degree = _expand_degree(m.group(1))
            key = (degree.lower()[:20], year)
            if key not in seen_entries:
                seen_entries.add(key)
                education.append({'degree': degree, 'institution': '', 'year': year})

    if not education and edu_text.strip():
        education.append({'degree': 'Degree', 'institution': '', 'year': ''})

    return education[:4]

def _extract_jd_title(text: str) -> str:
    """Extract job title from JD."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        # Look for lines with job-related keywords
        for line in lines[:5]:
            if any(kw in line.lower() for kw in ['engineer', 'developer', 'manager', 'analyst', 'scientist', 'designer', 'position', 'role']):
                return line
        return lines[0]  # Fallback to first line
    return "Job Position"

def _extract_company(text: str) -> str:
    """Extract company name from JD."""
    # Look for common patterns
    match = re.search(r'(?i)company[:\s]+(\w[\w\s&.]+)', text)
    if match:
        return match.group(1).strip()
    return None

def _extract_requirements(text: str) -> List[JDRequirement]:
    """Extract requirements from JD."""
    requirements = []
    
    # Look for requirements/qualifications section
    req_pattern = r'(?i)(requirements?|qualifications?|responsibilities)[:\s]*([\s\S]*?)(?=\n\s*(?:benefits|about|company|we offer)|$)'
    match = re.search(req_pattern, text)
    
    if match:
        req_text = match.group(2)
        
        # Extract bullet points
        bullets = re.findall(r'[•●○◦▪▫⁃‣⦿⦾\-\*]\s*(.+?)(?=\n[•●○◦▪▫⁃‣⦿⦾\-\*]|\n\n|$)', req_text, re.DOTALL)
        
        for bullet in bullets:
            bullet = bullet.strip()
            if len(bullet) < 10:
                continue
            
            # Categorize requirement
            category = 'experience'
            if any(skill.lower() in bullet.lower() for skill in SKILLS_TAXONOMY[:20]):
                category = 'skills'
            elif any(kw in bullet.lower() for kw in ['degree', 'education', 'bachelor', 'master', 'phd']):
                category = 'education'
            elif any(kw in bullet.lower() for kw in ['certification', 'certified', 'cert']):
                category = 'certs'
            elif any(kw in bullet.lower() for kw in ['tool', 'software', 'platform']):
                category = 'tools'
            elif any(kw in bullet.lower() for kw in ['responsible', 'will', 'collaborate', 'work with']):
                category = 'responsibilities'
            
            # Detect if required or preferred
            required = 'preferred' not in bullet.lower() and 'nice to have' not in bullet.lower()
            
            # Extract years if mentioned
            years_match = re.search(r'(\d+)\+?\s*years?', bullet, re.IGNORECASE)
            min_years = int(years_match.group(1)) if years_match else None
            
            requirements.append(JDRequirement(
                text=bullet,
                category=category,
                required=required,
                min_years=min_years
            ))
    
    return requirements

def _extract_keywords(text: str) -> List[str]:
    """Extract important keywords from JD."""
    keywords = set()
    
    # Extract skills from taxonomy
    text_lower = text.lower()
    for skill in SKILLS_TAXONOMY:
        if skill.lower() in text_lower:
            keywords.add(skill)
    
    # Extract using spaCy NER for PRODUCT, ORG, TECH
    doc = nlp(text[:2000])  # Limit to avoid slowdown
    for ent in doc.ents:
        if ent.label_ in ['PRODUCT', 'ORG'] and len(ent.text) > 2:
            keywords.add(ent.text)
    
    return sorted(list(keywords))[:50]  # Limit to top 50
