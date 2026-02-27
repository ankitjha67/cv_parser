from src.llm.base import LLMProvider
from src.schemas import CV, JD, Evidence
from src.parser import parse_cv, parse_jd
from typing import Dict, Optional
import os
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-4-sonnet-20250514"):
        self.api_key = api_key or os.getenv('EMERGENT_LLM_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.model = model
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")
    
    def extract_cv(self, text: str) -> CV:
        return parse_cv(text)
    
    def extract_jd(self, text: str) -> JD:
        return parse_jd(text)
    
    def rewrite_bullet(self, bullet: str, jd_context: str, evidence: Evidence) -> str:
        prompt = f"""Rewrite this CV bullet to align with the job description.

CRITICAL RULES:
- Use ONLY facts from original bullet
- Start with strong action verb (past tense)
- NO new metrics, tools, or achievements

Original: {evidence.original_text}
Job context: {jd_context[:200]}

Rewrite:"""
        
        try:
            response = asyncio.run(self._call_llm(prompt))
            return response.strip()
        except Exception as e:
            print(f"Claude rewrite failed: {e}")
            from src.rewriter import _rewrite_bullet
            return _rewrite_bullet(bullet)
    
    def fact_check(self, rewritten_bullet: str, evidence: Evidence) -> Dict:
        from src.rewriter import check_factuality
        is_valid = check_factuality(rewritten_bullet, evidence)
        return {"valid": is_valid, "violations": []}
    
    async def _call_llm(self, prompt: str) -> str:
        chat = LlmChat(
            api_key=self.api_key,
            session_id="cv_rewrite_claude",
            system_message="You are a professional CV writer."
        ).with_model("anthropic", self.model)
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        return response
