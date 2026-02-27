from typing import List, Tuple
from src.schemas import CV, JD, MatchReport

def analyze_gaps(cv: CV, jd: JD, match_report: MatchReport) -> Tuple[List[str], List[str]]:
    """
    Identify hard gaps (completely missing) and soft gaps (unclear/not evidenced).
    Returns: (hard_gaps, soft_gaps)
    """
    hard_gaps = []
    soft_gaps = []
    
    cv_text_lower = cv.raw_text.lower()
    cv_skills_lower = set([s.lower() for s in cv.skills])
    
    # Analyze each JD requirement
    for req in jd.requirements:
        if not req.required:
            continue  # Only analyze required items
        
        req_text_lower = req.text.lower()
        
        if req.category == 'skills':
            # Check if any keywords from requirement appear in CV
            req_words = set(req_text_lower.split())
            # Filter out common words
            req_words = {w for w in req_words if len(w) > 3 and w.isalnum()}
            
            found_in_cv = any(word in cv_text_lower for word in req_words)
            found_in_skills = any(word in ' '.join(cv_skills_lower) for word in req_words)
            
            if not found_in_cv and not found_in_skills:
                hard_gaps.append(f"Missing skill: {req.text}")
            elif found_in_cv and not found_in_skills:
                soft_gaps.append(f"Skill mentioned but not highlighted: {req.text}")
        
        elif req.category == 'experience':
            # Check years requirement
            if req.min_years:
                cv_years = sum([_extract_years(exp.dates) for exp in cv.experiences])
                if cv_years < req.min_years:
                    hard_gaps.append(f"Experience gap: {req.min_years}+ years required, CV shows ~{cv_years} years")
            
            # Check for relevant experience
            req_keywords = _extract_keywords(req_text_lower)
            found = any(
                any(kw in exp.role.lower() or any(kw in bullet.lower() for bullet in exp.bullets) for kw in req_keywords)
                for exp in cv.experiences
            )
            if not found:
                soft_gaps.append(f"Experience not clearly demonstrated: {req.text[:80]}...")
        
        elif req.category == 'education':
            # Check education requirements
            req_degrees = ['bachelor', 'master', 'phd', 'doctorate']
            req_degree_found = any(deg in req_text_lower for deg in req_degrees)
            
            if req_degree_found:
                cv_has_degree = any(
                    any(deg in edu.get('degree', '').lower() for deg in req_degrees)
                    for edu in cv.education
                )
                if not cv_has_degree:
                    hard_gaps.append(f"Education requirement not met: {req.text}")
        
        elif req.category == 'certs':
            # Certifications
            cert_keywords = _extract_keywords(req_text_lower)
            found = any(kw in cv_text_lower for kw in cert_keywords)
            if not found:
                hard_gaps.append(f"Missing certification: {req.text}")
        
        elif req.category == 'tools':
            # Tools/technologies
            tool_keywords = _extract_keywords(req_text_lower)
            found = any(kw in cv_text_lower for kw in tool_keywords)
            if not found:
                soft_gaps.append(f"Tool/technology not mentioned: {req.text}")
    
    # Check JD keywords
    for keyword in jd.keywords[:20]:  # Top 20 keywords
        if keyword.lower() not in cv_text_lower:
            soft_gaps.append(f"Keyword not present: {keyword}")
    
    return hard_gaps, soft_gaps

def _extract_years(dates_str: str) -> int:
    """Extract years from date string."""
    import re
    years = re.findall(r'\b(\d{4})\b', dates_str)
    if len(years) >= 2:
        return int(years[-1]) - int(years[0])
    elif 'present' in dates_str.lower():
        if years:
            from datetime import datetime
            return datetime.now().year - int(years[0])
    return 1

def _extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    import re
    # Remove common stop words
    stop_words = {'the', 'and', 'or', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 'for', 'with', 'on', 'at', 'be', 'have', 'has', 'that', 'this', 'it', 'from', 'by', 'will', 'can', 'should'}
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]
    return list(set(keywords))[:10]  # Top 10 unique
