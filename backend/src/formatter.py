"""
Luxury CV Formatter - Creates beautifully formatted CV output
"""
from typing import List, Dict
from src.schemas import CV, Experience
import re
import textwrap

# Valid skills (clean list - no junk)
VALID_SKILLS = {
    # Programming Languages
    'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Ruby', 'PHP', 'R', 'Scala', 'Kotlin', 'Swift',
    # Frameworks & Libraries
    'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring', 'Express', '.NET', 'Rails',
    # Data & ML
    'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy', 'Spark', 'Hadoop', 'Kafka', 'Airflow',
    'Machine Learning', 'Deep Learning', 'Data Science', 'AI', 'NLP', 'Computer Vision', 'Data Analytics',
    # Databases
    'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'SQL', 'NoSQL', 'Oracle', 'SQL Server', 'DynamoDB',
    # Cloud & DevOps
    'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git', 'Linux', 'Terraform', 'Ansible',
    # Business Tools
    'Tableau', 'Power BI', 'Excel', 'JIRA', 'Confluence', 'Salesforce', 'SAP',
    # Finance & Risk
    'OFSAA', 'BASEL', 'Credit Risk', 'Risk Management', 'Financial Modeling', 'Regulatory Reporting',
    'IBM SPSS', 'SAS', 'Bloomberg', 'Reuters',
    # Methodologies
    'Agile', 'Scrum', 'DevOps', 'REST API', 'GraphQL', 'Microservices', 'ETL',
    # Certifications keywords
    'Lean Six Sigma', 'PMP', 'CFA', 'FRM', 'AWS Certified', 'Azure Certified', 'Scrum Master',
    # Design & Product
    'Figma', 'Sketch', 'Adobe XD', 'Balsamiq', 'ARIS', 'CATIA', 'Business Analysis', 'Product Management'
}


def format_luxury_cv(cv: CV, jd_title: str = None) -> str:
    """
    Format CV in a luxury, professional style.
    Clean, elegant, well-structured output.
    """
    lines = []
    width = 72  # Character width for formatting
    
    # Header with name
    lines.append("=" * width)
    lines.append("")
    lines.append(f"    {cv.name.upper()}")
    lines.append("")
    lines.append("=" * width)
    
    # Tailored for notice (if JD provided)
    if jd_title:
        lines.append("")
        lines.append(f"    Tailored for: {jd_title}")
        lines.append("-" * width)
    
    # Professional Summary
    if cv.summary:
        lines.append("")
        lines.append("PROFESSIONAL SUMMARY")
        lines.append("-" * 20)
        lines.append("")
        wrapped = textwrap.fill(cv.summary, width=width-4)
        for line in wrapped.split('\n'):
            lines.append(f"    {line}")
    
    # Experience Section
    lines.append("")
    lines.append("")
    lines.append("PROFESSIONAL EXPERIENCE")
    lines.append("-" * 24)
    
    for exp in cv.experiences:
        lines.append("")
        # Clean up role and company
        role = _clean_text(exp.role)
        company = _clean_text(exp.company)
        dates = _clean_dates(exp.dates)
        
        lines.append(f"    {role.upper()}")
        lines.append(f"    {company}")
        lines.append(f"    {dates}")
        lines.append("")
        
        # Format bullets nicely
        for bullet in exp.bullets:
            clean_bullet = _clean_bullet(bullet)
            if clean_bullet and len(clean_bullet) > 15:
                # Wrap long bullets
                wrapped = textwrap.fill(clean_bullet, width=width-8, subsequent_indent="      ")
                lines.append(f"    * {wrapped}")
        lines.append("")
    
    # Skills Section - Only valid skills
    clean_skills = _clean_skills(cv.skills)
    if clean_skills:
        lines.append("")
        lines.append("TECHNICAL SKILLS")
        lines.append("-" * 16)
        lines.append("")
        
        # Group skills by category for luxury presentation
        skill_groups = _categorize_skills(clean_skills)
        for category, skills in skill_groups.items():
            if skills:
                skill_line = f"    {category}: {', '.join(sorted(skills))}"
                if len(skill_line) > width:
                    # Wrap if too long
                    wrapped = textwrap.fill(', '.join(sorted(skills)), width=width-len(category)-8)
                    lines.append(f"    {category}:")
                    for wline in wrapped.split('\n'):
                        lines.append(f"        {wline}")
                else:
                    lines.append(skill_line)
    
    # Education Section
    clean_education = _clean_education(cv.education, cv.raw_text)
    if clean_education:
        lines.append("")
        lines.append("")
        lines.append("EDUCATION")
        lines.append("-" * 9)
        lines.append("")

        for edu in clean_education:
            degree = edu.get('degree', '').strip()
            institution = edu.get('institution', '').strip()
            year = edu.get('year', '').strip()

            if degree:
                lines.append(f"    {degree}")
                if institution:
                    lines.append(f"    {institution}")
                if year:
                    lines.append(f"    {year}")
                lines.append("")
    
    # Footer
    lines.append("")
    lines.append("=" * width)
    
    return '\n'.join(lines)


def _clean_text(text: str) -> str:
    """Clean up messy text."""
    if not text:
        return ""
    # Remove extra spaces
    text = ' '.join(text.split())
    # Fix common OCR issues
    text = text.replace('  ', ' ')
    return text.strip()


def _clean_dates(dates: str) -> str:
    """Clean and format dates properly."""
    if not dates:
        return ""
    # Standardize date format
    dates = dates.replace('–', '-').replace('—', '-')
    dates = ' '.join(dates.split())
    return dates


def _clean_bullet(bullet: str) -> str:
    """Clean up bullet point text."""
    if not bullet:
        return ""
    
    # Remove leading bullets/markers
    bullet = re.sub(r'^[•●○◦▪▫⁃‣⦿⦾\-\*]+\s*', '', bullet)
    
    # Fix common OCR/parsing issues
    bullet = bullet.replace('  ', ' ')
    bullet = re.sub(r'\s+', ' ', bullet)
    
    # Fix broken words (e.g., "Design ed" -> "Designed")
    bullet = re.sub(r'(\w+)\s+ed\b', r'\1ed', bullet)
    bullet = re.sub(r'(\w+)\s+ing\b', r'\1ing', bullet)
    bullet = re.sub(r'(\w+)\s+ion\b', r'\1ion', bullet)
    
    # Capitalize first letter
    if bullet:
        bullet = bullet[0].upper() + bullet[1:] if len(bullet) > 1 else bullet.upper()
    
    return bullet.strip()


def _clean_skills(skills: List[str]) -> List[str]:
    """Filter to only valid, clean skills."""
    clean = set()
    
    for skill in skills:
        # Check against valid skills (case-insensitive)
        skill_clean = skill.strip()
        
        # Direct match
        if skill_clean in VALID_SKILLS:
            clean.add(skill_clean)
            continue
        
        # Case-insensitive match
        for valid in VALID_SKILLS:
            if skill_clean.lower() == valid.lower():
                clean.add(valid)  # Use the properly cased version
                break
    
    return sorted(list(clean))


def _categorize_skills(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize skills for luxury presentation."""
    categories = {
        'Programming': [],
        'Data & Analytics': [],
        'Finance & Risk': [],
        'Cloud & DevOps': [],
        'Tools & Platforms': [],
        'Methodologies': []
    }

    programming = {'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
                   'Ruby', 'PHP', 'R', 'Scala', 'Kotlin', 'Swift', 'SQL'}
    data = {'TensorFlow', 'PyTorch', 'scikit-learn', 'Pandas', 'NumPy', 'Spark', 'Hadoop',
            'Kafka', 'Machine Learning', 'Deep Learning', 'Data Science', 'AI', 'NLP',
            'Data Analytics', 'IBM SPSS', 'Tableau', 'Power BI', 'Excel'}
    finance = {'OFSAA', 'BASEL', 'Credit Risk', 'Risk Management', 'Financial Modeling',
               'Regulatory Reporting', 'SAS', 'Bloomberg', 'Reuters', 'RWA'}
    cloud = {'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git',
             'Linux', 'Terraform', 'Ansible'}
    methods = {'Agile', 'Scrum', 'DevOps', 'REST API', 'GraphQL', 'Microservices', 'ETL',
               'Lean Six Sigma', 'PMP'}

    for skill in skills:
        if skill in programming:
            categories['Programming'].append(skill)
        elif skill in data:
            categories['Data & Analytics'].append(skill)
        elif skill in finance:
            categories['Finance & Risk'].append(skill)
        elif skill in cloud:
            categories['Cloud & DevOps'].append(skill)
        elif skill in methods:
            categories['Methodologies'].append(skill)
        else:
            categories['Tools & Platforms'].append(skill)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def _clean_education(education: List[Dict], raw_text: str) -> List[Dict]:
    """Extract and clean education entries, falling back to pre-parsed data when needed."""
    clean_edu = []

    # Strategy 1: parse from raw text looking for institution keywords
    edu_patterns = [
        r'(Post\s*Graduate\s*Diploma[^,\n]*|PGDM[^,\n]*|MBA[^,\n]*)\s*[-–]?\s*'
        r'([A-Z][A-Za-z\s&]+(?:University|Institute|School|College|Business)[^,\n]*)\s*[-–]?\s*(?:.*?(\d{4}))?',
        r'(Bachelor[^,\n]*|Master[^,\n]*|B\.?Tech[^,\n]*|M\.?Tech[^,\n]*'
        r'|B\.?S\.?[^,\n]*|M\.?S\.?[^,\n]*)\s*[-–]?\s*'
        r'([A-Z][A-Za-z\s&]+(?:University|Institute|College)[^,\n]*)\s*[-–]?\s*(?:.*?(\d{4}))?',
    ]
    for pattern in edu_patterns:
        for match in re.finditer(pattern, raw_text, re.IGNORECASE):
            degree = (match.group(1) or '').strip()
            institution = (match.group(2) or '').strip()
            year = match.group(3) if match.lastindex >= 3 else ''
            if degree and institution and len(institution) > 5:
                clean_edu.append({
                    'degree': re.sub(r'\s+', ' ', degree),
                    'institution': re.sub(r'\s+', ' ', institution),
                    'year': year or ''
                })

    # Strategy 2: fall back to the pre-parsed education list (handles abbreviated degrees
    # like "Master of Arts" extracted by parser._extract_education / _expand_degree)
    if not clean_edu and education:
        for edu in education:
            degree = (edu.get('degree') or '').strip()
            institution = (edu.get('institution') or '').strip()
            year = (edu.get('year') or '').strip()
            # Skip placeholder entries
            if degree and degree not in ('Degree',):
                clean_edu.append({
                    'degree': degree,
                    'institution': institution,
                    'year': year
                })

    # Deduplicate
    seen: set = set()
    unique_edu = []
    for edu in clean_edu:
        key = (edu['degree'].lower()[:25], edu['year'])
        if key not in seen:
            seen.add(key)
            unique_edu.append(edu)

    return unique_edu[:4]
