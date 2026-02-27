from abc import ABC, abstractmethod
from typing import Dict, Optional
from src.schemas import CV, JD, Evidence

class LLMProvider(ABC):
    """Base class for all LLM providers."""
    
    @abstractmethod
    def extract_cv(self, text: str) -> CV:
        """Extract structured CV from text."""
        pass
    
    @abstractmethod
    def extract_jd(self, text: str) -> JD:
        """Extract structured JD from text."""
        pass
    
    @abstractmethod
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        """Rewrite a single bullet with JD context, grounded in evidence."""
        pass
    
    @abstractmethod
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        """Check if rewritten bullet is factual.
        Returns: {"valid": bool, "violations": List[str]}
        """
        pass
