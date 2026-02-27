from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from src.rewriter import _rewrite_bullet, check_factuality
from typing import Dict, Optional
import requests

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, model_name: str = "llama2", api_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.api_url = api_url
        print(f"[Ollama] Using model: {model_name} at {api_url}")
    
    def extract_cv(self, text: str) -> CV:
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        """Use Ollama for bullet rewriting."""
        try:
            prompt = f"""Rewrite this CV bullet to align with the job context. Use ONLY facts from the original.

Original: {evidence.original_text}
Job context: {jd_context[:200]}

Rules:
- Start with strong past-tense action verb
- Keep all original facts
- No new metrics or achievements

Rewrite:"""
            
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                rewritten = result.get('response', '').strip()
                
                # Verify factuality
                if check_factuality(rewritten, evidence):
                    return rewritten
        except Exception as e:
            print(f"Ollama rewrite failed: {e}")
        
        # Fallback
        return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        is_valid = check_factuality(rewritten_bullet, evidence)
        return {"valid": is_valid, "violations": []}
