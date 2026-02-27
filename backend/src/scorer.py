from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple
from src.schemas import CV, JD, MatchReport, MatchEvidence
import re

def score_cv_jd(cv: CV, jd: JD) -> MatchReport:
    """
    Compute ATS-like matching score between CV and JD.
    Weighted scoring with evidence tracking.
    
    Weights:
    - Skills Match: 35%
    - Experience Relevance: 30%
    - Years/Tenure: 15%
    - Education/Certs: 10%
    - Tooling/Keywords: 10%
    """
    evidences: List[MatchEvidence] = []
    category_scores = {}
    
    # 1. Skills Match (35%)
    skills_score, skills_evidences = _score_skills(cv, jd)
    category_scores['skills'] = skills_score * 0.35
    evidences.extend(skills_evidences)
    
    # 2. Experience Relevance (30%)
    exp_score, exp_evidences = _score_experience(cv, jd)
    category_scores['experience'] = exp_score * 0.30
    evidences.extend(exp_evidences)
    
    # 3. Years/Tenure (15%)
    tenure_score = _score_tenure(cv, jd)
    category_scores['tenure'] = tenure_score * 0.15
    
    # 4. Education/Certs (10%)
    edu_score, edu_evidences = _score_education(cv, jd)
    category_scores['education'] = edu_score * 0.10
    evidences.extend(edu_evidences)
    
    # 5. Tooling/Keywords (10%)
    keyword_score, keyword_evidences = _score_keywords(cv, jd)
    category_scores['keywords'] = keyword_score * 0.10
    evidences.extend(keyword_evidences)
    
    total_score = sum(category_scores.values())
    
    return MatchReport(
        cv_id=cv.id,
        jd_id=jd.id,
        cv_name=cv.name,
        jd_title=jd.title,
        total_score=round(min(100, total_score), 2),
        category_scores={k: round(v, 2) for k, v in category_scores.items()},
        evidences=evidences,
        hard_gaps=[],  # Computed separately by gap_analyzer
        soft_gaps=[]
    )

def _score_skills(cv: CV, jd: JD) -> Tuple[float, List[MatchEvidence]]:
    """Score skills match using TF-IDF + cosine similarity."""
    evidences = []
    
    # Get skill requirements from JD
    jd_skills = [req.text for req in jd.requirements if req.category == 'skills']
    jd_skills.extend(jd.keywords)
    jd_skills_text = ' '.join(jd_skills).lower()
    
    cv_skills_text = ' '.join(cv.skills).lower()
    
    if not cv_skills_text or not jd_skills_text:
        return 0.0, evidences
    
    # TF-IDF similarity
    try:
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([cv_skills_text, jd_skills_text])
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    except:
        similarity = 0.0
    
    # Exact matches bonus
    cv_skills_set = set([s.lower() for s in cv.skills])
    jd_skills_set = set([s.lower() for s in jd_skills])
    exact_matches = cv_skills_set & jd_skills_set
    
    for match in exact_matches:
        evidences.append(MatchEvidence(
            cv_text=match,
            jd_text=match,
            similarity=1.0,
            category='skills'
        ))
    
    # Combine scores
    exact_score = len(exact_matches) / max(len(jd_skills_set), 1)
    final_score = (similarity * 0.6 + exact_score * 0.4) * 100
    
    return min(100, final_score), evidences

def _score_experience(cv: CV, jd: JD) -> Tuple[float, List[MatchEvidence]]:
    """Score experience relevance using keyword overlap."""
    evidences = []
    
    # Get all CV experience text
    cv_exp_text = ' '.join([
        f"{exp.role} {exp.company} {' '.join(exp.bullets)}"
        for exp in cv.experiences
    ]).lower()
    
    # Get JD requirements text
    jd_req_text = ' '.join([req.text for req in jd.requirements]).lower()
    jd_req_text += ' ' + jd.title.lower()
    
    if not cv_exp_text or not jd_req_text:
        return 0.0, evidences
    
    # TF-IDF similarity
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        vectors = vectorizer.fit_transform([cv_exp_text, jd_req_text])
        similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    except:
        similarity = 0.0
    
    # Check for role/title matches
    jd_title_words = set(jd.title.lower().split())
    for exp in cv.experiences:
        role_words = set(exp.role.lower().split())
        overlap = jd_title_words & role_words
        if overlap:
            evidences.append(MatchEvidence(
                cv_text=exp.role,
                jd_text=jd.title,
                similarity=len(overlap) / len(jd_title_words),
                category='experience'
            ))
    
    score = similarity * 100
    return min(100, score), evidences

def _score_tenure(cv: CV, jd: JD) -> float:
    """Score years of experience."""
    # Extract years from CV
    total_years = 0
    for exp in cv.experiences:
        years = _extract_years_from_dates(exp.dates)
        total_years += years
    
    # Extract required years from JD
    required_years = 0
    for req in jd.requirements:
        if req.min_years:
            required_years = max(required_years, req.min_years)
    
    if required_years == 0:
        return 100.0  # No specific requirement
    
    # Score based on ratio
    ratio = min(total_years / required_years, 1.5)  # Cap at 1.5x
    score = (ratio / 1.5) * 100
    
    return min(100, score)

def _extract_years_from_dates(dates_str: str) -> float:
    """Extract years of experience from date string."""
    # Look for year patterns
    years = re.findall(r'\b(\d{4})\b', dates_str)
    if len(years) >= 2:
        start_year = int(years[0])
        end_year = int(years[-1])
        return max(0, end_year - start_year)
    elif 'present' in dates_str.lower() or 'current' in dates_str.lower():
        if years:
            from datetime import datetime
            current_year = datetime.now().year
            return current_year - int(years[0])
    return 1.0  # Default to 1 year if unclear

def _score_education(cv: CV, jd: JD) -> Tuple[float, List[MatchEvidence]]:
    """Score education match."""
    evidences = []
    
    edu_requirements = [req for req in jd.requirements if req.category == 'education']
    
    if not edu_requirements:
        return 100.0, evidences  # No specific requirement
    
    if not cv.education:
        return 0.0, evidences
    
    # Check for degree level matches
    degree_levels = {'bachelor': 1, 'master': 2, 'phd': 3, 'doctorate': 3}
    
    cv_max_level = 0
    for edu in cv.education:
        degree = edu.get('degree', '').lower()
        for level_name, level_val in degree_levels.items():
            if level_name in degree:
                cv_max_level = max(cv_max_level, level_val)
    
    req_max_level = 0
    for req in edu_requirements:
        text = req.text.lower()
        for level_name, level_val in degree_levels.items():
            if level_name in text:
                req_max_level = max(req_max_level, level_val)
    
    if cv_max_level >= req_max_level:
        score = 100.0
        evidences.append(MatchEvidence(
            cv_text=str(cv.education[0]),
            jd_text=edu_requirements[0].text,
            similarity=1.0,
            category='education'
        ))
    else:
        score = (cv_max_level / req_max_level) * 100 if req_max_level > 0 else 50.0
    
    return score, evidences

def _score_keywords(cv: CV, jd: JD) -> Tuple[float, List[MatchEvidence]]:
    """Score keyword match with evidence."""
    evidences = []
    
    cv_text = cv.raw_text.lower()
    jd_keywords_set = set([kw.lower() for kw in jd.keywords])
    
    if not jd_keywords_set:
        return 100.0, evidences
    
    matched_keywords = set()
    for keyword in jd_keywords_set:
        if keyword in cv_text:
            matched_keywords.add(keyword)
            # Find context
            idx = cv_text.find(keyword)
            context = cv.raw_text[max(0, idx-50):idx+50]
            evidences.append(MatchEvidence(
                cv_text=context.strip(),
                jd_text=keyword,
                similarity=1.0,
                category='keywords'
            ))
    
    # Jaccard similarity
    if len(jd_keywords_set) > 0:
        jaccard = len(matched_keywords) / len(jd_keywords_set)
    else:
        jaccard = 1.0
    
    score = jaccard * 100
    return min(100, score), evidences
