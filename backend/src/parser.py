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
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Ruby', 'PHP',
    'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring', 'Express',
    'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'SQL', 'NoSQL',
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git', 'Linux',
    'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy', 'NLP', 'Computer Vision',
    'Machine Learning', 'Deep Learning', 'Data Science', 'AI', 'ML', 'ETL', 'Spark',
    'REST API', 'GraphQL', 'Microservices', 'Agile', 'Scrum', 'DevOps', 'Testing'
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
    """Extract name (usually first line)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        # First line that's not an email or phone
        for line in lines[:3]:
            if not re.search(r'@|\d{3}[-.]?\d{3}[-.]?\d{4}', line) and len(line.split()) <= 5:
                return line
    return "Unknown"

def _extract_experiences(full_text: str, exp_text: str) -> List[Experience]:
    """Extract work experiences with bullet points and evidence."""
    experiences = []
    
    # Split by job entries (usually separated by company/role lines)
    # Look for patterns like: "Title, Company, Date" or "Title at Company"
    job_pattern = r'([A-Z][\w\s]+(?:Engineer|Developer|Manager|Analyst|Scientist|Designer|Consultant|Lead|Director|Specialist))[,\s]+([A-Z][\w\s&.]+)[,\s]+(\w+\s+\d{4}\s*[-–]\s*(?:\w+\s+\d{4}|Present|Current))'
    
    matches = list(re.finditer(job_pattern, exp_text, re.MULTILINE))
    
    if not matches:
        # Fallback: try to extract at least one generic experience
        bullets = _extract_bullets(exp_text, full_text)
        if bullets:
            experiences.append(Experience(
                role="Professional",
                company="Previous Employer",
                dates="2020 - Present",
                bullets=[b['text'] for b in bullets],
                evidence_map={b['text']: b['evidence'] for b in bullets}
            ))
    else:
        for i, match in enumerate(matches):
            role = match.group(1).strip()
            company = match.group(2).strip()
            dates = match.group(3).strip()
            
            # Extract bullets for this experience
            start_pos = match.end()
            end_pos = matches[i+1].start() if i+1 < len(matches) else len(exp_text)
            job_text = exp_text[start_pos:end_pos]
            
            bullets = _extract_bullets(job_text, full_text)
            
            if bullets or True:  # Include even if no bullets
                experiences.append(Experience(
                    role=role,
                    company=company,
                    dates=dates,
                    bullets=[b['text'] for b in bullets] if bullets else ["Contributed to team projects"],
                    evidence_map={b['text']: b['evidence'] for b in bullets} if bullets else {}
                ))
    
    return experiences

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

def _extract_education(edu_text: str) -> List[Dict[str, str]]:
    """Extract education entries."""
    education = []
    
    # Pattern: Degree, Institution, Year
    pattern = r'(B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|Bachelor|Master|Doctorate)[\s\w]*,?\s+([A-Z][\w\s&]+),?\s+(\d{4})'
    matches = re.finditer(pattern, edu_text, re.IGNORECASE)
    
    for match in matches:
        education.append({
            'degree': match.group(1),
            'institution': match.group(2).strip(),
            'year': match.group(3)
        })
    
    if not education and edu_text.strip():
        # Fallback
        education.append({
            'degree': 'Degree',
            'institution': 'University',
            'year': '2020'
        })
    
    return education

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
