from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from src.rewriter import _rewrite_bullet, check_factuality
from typing import Dict, Optional

class HuggingFaceProvider(LLMProvider):
    """HuggingFace local transformers provider (placeholder - requires model loading)."""
    
    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        # In production, load model here:
        # from transformers import pipeline
        # self.generator = pipeline('text-generation', model=model_name)
        print(f"[HF] Using model: {model_name} (deterministic fallback for now)")
    
    def extract_cv(self, text: str) -> CV:
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        # For now, use deterministic (loading full HF models is heavy)
        # In production, use self.generator with proper prompts
        return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        is_valid = check_factuality(rewritten_bullet, evidence)
        return {"valid": is_valid, "violations": []}
