from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from typing import Dict, Optional
import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

class GeminiProvider(LLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-pro"):
        self.api_key = api_key or os.getenv('EMERGENT_LLM_KEY') or os.getenv('GEMINI_API_KEY')
        self.model = model
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
    
    def extract_cv(self, text: str) -> CV:
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        prompt = f"""Rewrite CV bullet for job description. Use ONLY original facts.

Original: {evidence.original_text}
Job context: {jd_context[:200]}

Rewrite with strong action verb:"""
        
        try:
            response = asyncio.run(self._call_llm(prompt))
            return response.strip()
        except Exception as e:
            print(f"Gemini rewrite failed: {e}")
            from src.rewriter import _rewrite_bullet
            return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        from src.rewriter import check_factuality
        is_valid = check_factuality(rewritten_bullet, evidence)
        return {"valid": is_valid, "violations": []}
    
    async def _call_llm(self, prompt: str) -> str:
        chat = LlmChat(
            api_key=self.api_key,
            session_id="cv_rewrite_gemini",
            system_message="You are a CV writing assistant."
        ).with_model("gemini", self.model)
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        return response
