from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from src.rewriter import _rewrite_bullet, check_factuality
from typing import Dict

class DeterministicProvider(LLMProvider):
    """Deterministic provider using regex + heuristics. No LLM needed."""
    
    def extract_cv(self, text: str) -> CV:
        """Use deterministic parser."""
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        """Use deterministic parser."""
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        """Use deterministic rewrite with verb mapping."""
        return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        """Use deterministic factuality check."""
        is_valid = check_factuality(rewritten_bullet, evidence)
        return {
            "valid": is_valid,
            "violations": [] if is_valid else ["Potential hallucination detected"]
        }
