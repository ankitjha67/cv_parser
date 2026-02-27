from typing import Dict, List, Optional
from src.schemas import CV, JD, Experience, Evidence, TailoredCV
from src.parser import VERB_MAP
import re
import uuid

def rewrite_cv_deterministic(cv: CV, jd: JD, gaps: List[str]) -> TailoredCV:
    """
    Rewrite CV deterministically without LLM.
    - Reorder bullets by relevance to JD
    - Apply action verb mapping
    - Preserve all evidence
    - NEVER add new facts
    """
    modifications = []
    
    # Create new CV object
    tailored_cv = CV(**cv.model_dump())
    tailored_cv.id = str(uuid.uuid4())
    
    # Extract JD keywords for relevance scoring
    jd_keywords = set([kw.lower() for kw in jd.keywords])
    jd_keywords.update([req.text.lower() for req in jd.requirements])
    jd_keywords.update(jd.title.lower().split())
    
    # Rewrite experiences
    for i, exp in enumerate(tailored_cv.experiences):
        # Score each bullet by relevance
        bullet_scores = []
        for bullet in exp.bullets:
            score = _score_bullet_relevance(bullet, jd_keywords)
            bullet_scores.append((bullet, score))
        
        # Sort bullets by relevance (highest first)
        bullet_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Rewrite bullets with action verbs
        new_bullets = []
        new_evidence_map = {}
        
        for bullet, score in bullet_scores:
            rewritten = _rewrite_bullet(bullet)
            new_bullets.append(rewritten)
            
            # Preserve evidence mapping
            if bullet in exp.evidence_map:
                new_evidence_map[rewritten] = exp.evidence_map[bullet]
                modifications.append(f"Rewrote bullet: '{bullet[:50]}...' -> '{rewritten[:50]}...'")
        
        exp.bullets = new_bullets
        exp.evidence_map = new_evidence_map
    
    # Reorder experiences (most relevant first)
    exp_relevance = []
    for exp in tailored_cv.experiences:
        score = _score_experience_relevance(exp, jd_keywords)
        exp_relevance.append((exp, score))
    exp_relevance.sort(key=lambda x: x[1], reverse=True)
    tailored_cv.experiences = [exp for exp, score in exp_relevance]
    modifications.append(f"Reordered {len(tailored_cv.experiences)} experiences by relevance")
    
    # Enhance summary (if exists) with JD-aligned keywords
    if tailored_cv.summary:
        enhanced_summary = _enhance_summary(tailored_cv.summary, jd, cv.raw_text)
        if enhanced_summary != tailored_cv.summary:
            tailored_cv.summary = enhanced_summary
            modifications.append("Enhanced summary with JD-relevant keywords")
    
    return TailoredCV(
        match_report_id="",  # Set by caller
        cv=tailored_cv,
        modifications=modifications
    )

def _score_bullet_relevance(bullet: str, jd_keywords: set) -> float:
    """Score bullet relevance to JD."""
    bullet_lower = bullet.lower()
    matches = sum(1 for kw in jd_keywords if kw in bullet_lower)
    return matches

def _score_experience_relevance(exp: Experience, jd_keywords: set) -> float:
    """Score entire experience relevance."""
    text = f"{exp.role} {exp.company} {' '.join(exp.bullets)}".lower()
    matches = sum(1 for kw in jd_keywords if kw in text)
    return matches

def _rewrite_bullet(bullet: str) -> str:
    """
    Rewrite bullet with strong action verbs.
    ONLY rephrase, NEVER add new information.
    """
    words = bullet.split()
    if not words:
        return bullet
    
    first_word = words[0].lower()
    
    # Apply verb mapping
    if first_word in VERB_MAP:
        new_verb = VERB_MAP[first_word]
        # Capitalize first letter
        words[0] = new_verb.capitalize()
        return ' '.join(words)
    
    # If starts with weak phrase, strengthen
    weak_starts = {
        'responsible for': 'Led',
        'worked on': 'Executed',
        'helped with': 'Supported',
        'assisted in': 'Contributed to',
        'participated in': 'Collaborated on'
    }
    
    for weak, strong in weak_starts.items():
        if bullet.lower().startswith(weak):
            return bullet.replace(weak, strong, 1).replace(weak.capitalize(), strong, 1)
    
    return bullet

def _enhance_summary(summary: str, jd: JD, cv_raw_text: str) -> str:
    """
    Enhance summary by aligning language with JD.
    ONLY use keywords that are already evidenced in CV.
    """
    # Extract skills/keywords from JD that are also in CV
    cv_lower = cv_raw_text.lower()
    relevant_keywords = []
    
    for keyword in jd.keywords[:10]:  # Top 10
        if keyword.lower() in cv_lower and keyword.lower() not in summary.lower():
            relevant_keywords.append(keyword)
    
    # Add to summary if space allows
    if relevant_keywords and len(summary) < 300:
        keywords_text = ', '.join(relevant_keywords[:3])
        summary = summary.rstrip('.') + f". Proficient in {keywords_text}."
    
    return summary

def check_factuality(rewritten_bullet: str, evidence: Evidence) -> bool:
    """
    Verify that rewritten bullet contains only information from evidence.
    Returns True if factual, False if hallucination detected.
    """
    # Extract key entities and metrics from both
    original_tokens = set(evidence.original_text.lower().split())
    rewritten_tokens = set(rewritten_bullet.lower().split())
    
    # Check for new numbers (potential metric hallucination)
    original_numbers = set(re.findall(r'\d+', evidence.original_text))
    rewritten_numbers = set(re.findall(r'\d+', rewritten_bullet))
    
    if rewritten_numbers - original_numbers:
        return False  # New numbers added
    
    # Check for new specific tools/technologies
    # (Allow verb changes and minor rephrasing)
    core_words = rewritten_tokens - set(VERB_MAP.values())
    core_words = {w for w in core_words if len(w) > 4}  # Focus on meaningful words
    
    # Allow some new words (articles, connectors) but not too many
    new_words = core_words - original_tokens
    if len(new_words) > len(core_words) * 0.3:  # More than 30% new content
        return False
    
    return True
